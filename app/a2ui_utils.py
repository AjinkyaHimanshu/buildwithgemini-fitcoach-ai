"""Make an ADK agent's A2UI output render in the ADK dev UI (`adk web`).

`adk web` has a built-in A2UI renderer, but it only fires when a response part is
a text/plain Blob wrapped in <a2a_datapart_json>...</a2a_datapart_json> with
custom_metadata {"a2a:response": "true"}. This callback takes the A2UI JSON the
model emits as text and rewraps it into exactly that format.

Wire it up with `after_model_callback=a2ui_callback` on your Agent. Pin the A2UI
schema to **version 0.8** (this callback keys off v0.8 messages: beginRendering,
surfaceUpdate, dataModelUpdate). Copy this file next to your agent.py.

Robustness notes (why this file is more than a one-liner):
  * The model often *self-wraps* — it imitates the wrapped format it sees in its
    own history and emits `<a2a_datapart_json>{"kind":"data","data":{...}}</...>`
    or concatenated JSON objects. This callback strips those tags, splits
    concatenated objects, and unwraps `{"kind":"data","data":{...}}` envelopes.
  * On large / deeply-nested surfaces the model sometimes emits *invalid* JSON
    (e.g. a `]` where `}}` belonged). When that happens we can only partially
    parse the payload and would be left with a lone `beginRendering` and no body,
    which renders as a BLANK surface. To avoid that bad UX we require a surface to
    actually have renderable content; if it doesn't, we return a short plain-text
    fallback instead of a blank card.
"""

import json
import re

from google.genai import types
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_response import LlmResponse

# A2UI message kinds this renderer understands (v0.8).
_A2UI_KEYS = ("beginRendering", "surfaceUpdate", "dataModelUpdate", "deleteSurface")

# Tags the model may wrap around its output (its own render wrapper, or the SDK's).
_TAG_RE = re.compile(r"</?(?:a2a_datapart_json|a2ui-json)>")

# Shown when the model emitted A2UI we could not fully parse (usually malformed
# JSON on a large surface). Better than a blank card or a wall of raw JSON.
_FALLBACK_TEXT = (
    "I couldn't render that view. Could you ask again, maybe for a simpler summary?"
)

# adk web can only render an <Image> whose url is a real, fetchable http(s) link.
# Models frequently emit an Image pointing at a bare artifact filename or a
# relative path (e.g. "recipe_image_123.png"), which renders as a broken-image
# icon. We swap those for this short note; the generated media still shows up in
# the adk web Artifacts panel.
_HTTP_URL_RE = re.compile(r"^https?://", re.I)
_IMAGE_NOTE = "Image generated — open the Artifacts panel to view it."


def _wrap_a2ui_part(a2ui_message: dict) -> types.Part:
    """Wrap a single A2UI message for rendering in adk web."""
    datapart_json = json.dumps(
        {
            "kind": "data",
            "metadata": {"mimeType": "application/json+a2ui"},
            "data": a2ui_message,
        }
    )
    blob_data = (
        b"<a2a_datapart_json>" + datapart_json.encode("utf-8") + b"</a2a_datapart_json>"
    )
    return types.Part(
        inline_data=types.Blob(
            data=blob_data,
            mime_type="text/plain",
        )
    )


def _iter_json_values(text: str):
    """Yield top-level JSON values from a string of concatenated objects/arrays.

    Tolerates junk between values (tags, whitespace, commas). Stops at the first
    unparseable value, so a valid prefix is still returned (partial recovery).
    """
    decoder = json.JSONDecoder()
    idx = 0
    n = len(text)
    while idx < n:
        while idx < n and text[idx] not in "{[":
            idx += 1
        if idx >= n:
            break
        try:
            value, end = decoder.raw_decode(text, idx)
        except json.JSONDecodeError:
            break  # malformed from here on; keep whatever we already parsed
        yield value
        idx = end


def _parse_pseudo_xml_a2ui(text: str) -> list[dict]:
    """Parse pseudo-XML <a2ui-json> / <surfaceUpdate> tags into valid A2UI message dicts."""
    if "<surfaceUpdate" not in text and "<component" not in text:
        return []

    su_match = re.search(r'<surfaceUpdate\s+surfaceId=["\'](.*?)["\']>', text)
    surface_id = su_match.group(1) if su_match else "main_surface"

    components = []
    comp_matches = re.finditer(r'<component\s+id=["\'](.*?)["\']\s+component=["\'](.*?)["\']>(.*?)</component>', text, re.DOTALL)

    for cm in comp_matches:
        cid = cm.group(1)
        ctype = cm.group(2)
        body = cm.group(3)

        comp_obj = {}
        if ctype == "Card":
            child_m = re.search(r'<child>(.*?)</child>', body)
            child_id = child_m.group(1).strip() if child_m else ""
            comp_obj = {"Card": {"child": child_id}}
        elif ctype in ("Column", "Row"):
            expl_m = re.search(r'explicitList=["\']\[?(.*?)\]?["\']', body)
            child_list = []
            if expl_m:
                raw_items = expl_m.group(1).split(",")
                child_list = [item.strip().strip("'\"") for item in raw_items if item.strip()]
            dist_m = re.search(r'<distribution>(.*?)</distribution>', body)
            align_m = re.search(r'<alignment>(.*?)</alignment>', body)
            comp_obj = {
                ctype: {
                    "children": {"explicitList": child_list},
                    "distribution": dist_m.group(1).strip() if dist_m else "start",
                    "alignment": align_m.group(1).strip() if align_m else "stretch",
                }
            }
        elif ctype == "Text":
            lit_m = re.search(r'literalString=["\'](.*?)["\']', body)
            usage_m = re.search(r'<usageHint>(.*?)</usageHint>', body)
            comp_obj = {
                "Text": {
                    "text": {"literalString": lit_m.group(1) if lit_m else ""},
                    "usageHint": usage_m.group(1).strip() if usage_m else "body",
                }
            }
        elif ctype == "Image":
            url_m = re.search(r'literalString=["\'](.*?)["\']', body)
            comp_obj = {
                "Image": {
                    "url": {"literalString": url_m.group(1) if url_m else ""}
                }
            }

        if comp_obj:
            components.append({"id": cid, "component": comp_obj})

    if components:
        return [{"surfaceUpdate": {"surfaceId": surface_id, "components": components}}]
    return []


def _extract_a2ui_messages(text: str) -> list[dict]:
    """Pull A2UI messages out of the model's raw text output.

    Handles: markdown fences, self-wrap tags, plain arrays, concatenated objects,
    pseudo-XML <a2ui-json> tags, and `{"kind":"data","data":{...}}` envelopes.
    """
    raw_original = text
    # Strip markdown fences.
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        if text.endswith("```"):
            text = text[:-3]
    # Strip any wrapper tags so the JSON scanner sees clean payload.
    clean_text = _TAG_RE.sub("", text).strip()

    values: list = []
    for value in _iter_json_values(clean_text):
        if isinstance(value, list):
            values.extend(value)
        else:
            values.append(value)

    messages: list[dict] = []
    for value in values:
        if not isinstance(value, dict):
            continue
        # Unwrap {"kind":"data","data":{...}} envelopes the model may imitate.
        inner = value.get("data")
        if isinstance(inner, dict) and any(k in inner for k in _A2UI_KEYS):
            messages.append(inner)
        elif any(k in value for k in _A2UI_KEYS):
            messages.append(value)

    if not messages:
        # Fallback: model emitted pseudo-XML <a2ui-json> tags
        messages = _parse_pseudo_xml_a2ui(raw_original)

    return messages



def _sanitize_image_components(messages: list[dict]) -> None:
    """Replace un-fetchable <Image> components with a short <Text> note, in place.

    Keeps the component's `id` so any parent child-reference still resolves; only
    the component body changes from Image to Text. An Image is kept only if its
    url is a literal http(s) link (a path-bound or relative/filename url can't be
    fetched by adk web and would render as a broken-image icon).
    """
    for m in messages:
        surface = m.get("surfaceUpdate")
        if not isinstance(surface, dict):
            continue
        for c in surface.get("components") or []:
            if not isinstance(c, dict):
                continue
            comp = c.get("component")
            if not isinstance(comp, dict) or "Image" not in comp:
                continue
            img = comp.get("Image")
            url = img.get("url") if isinstance(img, dict) else None
            literal = url.get("literalString") if isinstance(url, dict) else None
            if isinstance(literal, str) and _HTTP_URL_RE.match(literal):
                continue  # real link -> leave the Image alone
            c["component"] = {
                "Text": {
                    "text": {"literalString": _IMAGE_NOTE},
                    "usageHint": "body",
                }
            }


def _component_ids_and_refs(components: list) -> tuple[set, set]:
    """Return (defined ids, referenced child ids) for a component list."""
    ids: set = set()
    refs: set = set()
    for c in components:
        if not isinstance(c, dict):
            continue
        if "id" in c:
            ids.add(c["id"])
        comp = c.get("component")
        if not isinstance(comp, dict):
            continue
        for spec in comp.values():  # e.g. {"Card": {...}} / {"Column": {...}}
            if not isinstance(spec, dict):
                continue
            if isinstance(spec.get("child"), str):
                refs.add(spec["child"])
            children = spec.get("children")
            if isinstance(children, dict):
                for cid in children.get("explicitList") or []:
                    if isinstance(cid, str):
                        refs.add(cid)
    return ids, refs


def _surface_is_renderable(messages: list[dict]) -> bool:
    """True only if the messages form a surface adk web can actually draw.

    Guards against the two blank-card failure modes flash models produce:
      * a lone `beginRendering` with no `surfaceUpdate` body (malformed JSON), and
      * a surface whose `root` (or a child ref) points at an id that was never
        defined — the whole tree then renders as nothing.
    dataModelUpdate / deleteSurface messages are always considered renderable.
    """
    all_ids: set = set()
    all_refs: set = set()
    roots: list = []
    has_body = False
    for m in messages:
        if "dataModelUpdate" in m or "deleteSurface" in m:
            return True
        br = m.get("beginRendering")
        if isinstance(br, dict) and isinstance(br.get("root"), str):
            roots.append(br["root"])
        su = m.get("surfaceUpdate")
        if isinstance(su, dict) and su.get("components"):
            has_body = True
            ids, refs = _component_ids_and_refs(su["components"])
            all_ids |= ids
            all_refs |= refs
    if not has_body:
        return False
    if any(root not in all_ids for root in roots):
        return False  # root points at an undefined component -> blank
    if all_refs - all_ids:
        return False  # dangling child references -> blank
    return True


def _repair_surface_tree(messages: list[dict]) -> None:
    """Automatically repairs common LLM component tree discrepancies:
    1. Removes dangling child IDs from explicitList and child properties.
    2. Re-points beginRendering.root to a valid defined component ID.
    """
    all_defined = set()
    for m in messages:
        su = m.get("surfaceUpdate")
        if isinstance(su, dict) and isinstance(su.get("components"), list):
            for c in su["components"]:
                if isinstance(c, dict) and "id" in c:
                    all_defined.add(c["id"])

    if not all_defined:
        return

    for m in messages:
        su = m.get("surfaceUpdate")
        if isinstance(su, dict) and isinstance(su.get("components"), list):
            for c in su["components"]:
                if not isinstance(c, dict):
                    continue
                comp = c.get("component")
                if not isinstance(comp, dict):
                    continue
                for spec in comp.values():
                    if not isinstance(spec, dict):
                        continue
                    if isinstance(spec.get("child"), str) and spec["child"] not in all_defined:
                        spec.pop("child", None)
                    children = spec.get("children")
                    if isinstance(children, dict) and isinstance(children.get("explicitList"), list):
                        children["explicitList"] = [cid for cid in children["explicitList"] if cid in all_defined]

        br = m.get("beginRendering")
        if isinstance(br, dict) and isinstance(br.get("root"), str):
            if br["root"] not in all_defined:
                # Find component with "Card" or pick first defined ID
                card_id = None
                if isinstance(su, dict) and isinstance(su.get("components"), list):
                    for c in su["components"]:
                        if isinstance(c, dict) and isinstance(c.get("component"), dict) and "Card" in c["component"]:
                            card_id = c.get("id")
                            break
                br["root"] = card_id if card_id else next(iter(all_defined))


def a2ui_callback(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
) -> LlmResponse | None:
    """Convert A2UI JSON in text output to rendered components (or a clean fallback)."""
    if not llm_response.content or not llm_response.content.parts:
        return None

    for part in llm_response.content.parts:
        text = (part.text or "").strip()
        if not text:
            continue
        # Cheap gate: only touch parts that look like A2UI, leave prose alone.
        if not any(k in text for k in _A2UI_KEYS):
            continue

        messages = _extract_a2ui_messages(text)
        if not messages:
            continue

        # Turn un-fetchable <Image> URLs into a text note (no broken-image icons).
        _sanitize_image_components(messages)

        # Repair common component tree discrepancies (dangling IDs, root mismatch)
        _repair_surface_tree(messages)

        if not _surface_is_renderable(messages):
            # We recognized A2UI but couldn't recover a renderable surface — the
            # model emitted invalid JSON or empty body. Return clean text instead of a blank card.
            return LlmResponse(
                content=types.Content(
                    role="model", parts=[types.Part(text=_FALLBACK_TEXT)]
                )
            )

        new_parts = [_wrap_a2ui_part(m) for m in messages]
        return LlmResponse(
            content=types.Content(role="model", parts=new_parts),
            custom_metadata={"a2a:response": "true"},
        )

    return None
