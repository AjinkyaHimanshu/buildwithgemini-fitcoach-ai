"""Script to set up a serverless Vertex AI RAG Engine corpus and import Culpeper's Complete Herbal text file.
"""

import vertexai
from vertexai.preview import rag
from vertexai.preview.rag.utils import resources as rr

PROJECT_ID = "qwiklabs-gcp-03-3812c3284864"
LOCATION = "us-central1"
GCS_PATH = "gs://fitcoach-ai-media-3812/rag/pg49513.txt"

PARSING_PROMPT = (
    "Extract the individual useful facts, medicinal herbs, recipes, and health remedies described in this text. "
    "Ignore and omit all metadata, Gutenberg license text, boilerplate, and page headers. "
    "Output clean, self-contained prose."
)


def create_and_index_rag_corpus():
    print(f"Initializing Vertex AI SDK with project '{PROJECT_ID}' in '{LOCATION}'...")
    vertexai.init(project=PROJECT_ID, location=LOCATION)

    # 1. Switch region's RAG managed DB to serverless mode
    cfg = f"projects/{PROJECT_ID}/locations/{LOCATION}/ragEngineConfig"
    print(f"⚙️ Configuring RAG engine to serverless mode ({cfg})...")
    rag.update_rag_engine_config(
        rag_engine_config=rag.RagEngineConfig(
            name=cfg,
            rag_managed_db_config=rag.RagManagedDbConfig(mode=rr.Serverless()),
        )
    )

    # 2. Create the RAG corpus
    print("🌱 Creating serverless Vertex AI RAG corpus 'culpeper-complete-herbal-corpus'...")
    corpus = rag.create_corpus(
        display_name="culpeper-complete-herbal-corpus",
        embedding_model_config=rag.EmbeddingModelConfig(
            publisher_model="publishers/google/models/text-embedding-005"
        ),
    )
    print("==================================================")
    print("✅ RAG Corpus Resource Name:")
    print(corpus.name)
    print("==================================================")

    # Save corpus name to a local file for seamless integration
    with open("data/rag_corpus_name.txt", "w") as f:
        f.write(corpus.name.strip())

    # 3. Import + parse + chunk + embed
    print(f"📥 Importing and indexing '{GCS_PATH}' into RAG corpus...")
    resp = rag.import_files(
        corpus_name=corpus.name,
        paths=[GCS_PATH],
        transformation_config=rag.TransformationConfig(
            chunking_config=rag.ChunkingConfig(chunk_size=512, chunk_overlap=100)
        ),
        llm_parser=rag.LlmParserConfig(
            model_name="gemini-3.6-flash",
            custom_parsing_prompt=PARSING_PROMPT,
        ),
    )
    print(f"✅ Successfully imported {resp.imported_rag_files_count} file(s) into RAG corpus!")
    return corpus.name


if __name__ == "__main__":
    create_and_index_rag_corpus()
