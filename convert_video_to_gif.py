import os
import subprocess
import imageio_ffmpeg

INPUT_WEBM = "/config/.gemini/antigravity/brain/7b1bf65a-f8fc-462b-ae0d-68a304a83d09/fitcoach_ai_agent_demo.webm"
ASSETS_DIR = "/config/Desktop/session4/buildwithgemini-fitcoach-ai/assets"
OUTPUT_GIF = os.path.join(ASSETS_DIR, "fitcoach_ai_agent_demo.gif")

os.makedirs(ASSETS_DIR, exist_ok=True)

def convert():
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    print(f"Using ffmpeg binary at: {ffmpeg_exe}")
    print(f"Converting {INPUT_WEBM} -> {OUTPUT_GIF}...")

    # High quality palette-based GIF compression
    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", INPUT_WEBM,
        "-vf", "fps=10,scale=800:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=bayer",
        OUTPUT_GIF
    ]

    subprocess.run(cmd, check=True)
    print("Conversion completed successfully!")
    print("Output GIF size:", os.path.getsize(OUTPUT_GIF) / (1024 * 1024), "MB")

if __name__ == "__main__":
    convert()
