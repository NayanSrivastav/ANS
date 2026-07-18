import json
import os
import re
import requests

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------
API_KEY = os.environ.get("eleven_labs_53")
if not API_KEY:
    raise SystemExit("Error: eleven_labs environment variable is not set.")

VOICE_EN = "EXAVITQu4vr4xnSDxMaL"  # Bella
VOICE_HI = "EXAVITQu4vr4xnSDxMaL"  # Bella (Soft, Warm - Default free voice)

MODEL = "eleven_multilingual_v2"

VOICE_SETTINGS = {
    "stability": 0.75,
    "similarity_boost": 0.75,
    "style": 0.35,
    "use_speaker_boost": True,
}

# Paths are now relative to this script's directory in the web repo
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STORIES_JSON = os.path.join(SCRIPT_DIR, "stories.json")
AUDIO_DIR = os.path.join(SCRIPT_DIR, "assets", "audio")

def voice_for(lang):
    return VOICE_EN if lang == "en" else VOICE_HI

def sanitize_filename(name):
    hindi_nums = "०१२३४५६७८९"
    for i, h in enumerate(hindi_nums):
        name = name.replace(h, str(i))
    if any(ord(c) > 127 for c in name):
        return "u_" + "".join(f"{ord(c):04x}" for c in name)
    return re.sub(r"[^a-z0-9_]", "", name.lower())

def download_audio(text, filepath, voice_id):
    if os.path.exists(filepath):
        print(f"  Existing: {os.path.basename(filepath)}")
        return True

    print(f"  Generating: {os.path.basename(filepath)}  →  \"{text}\"")
    response = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        headers={
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "Xi-Api-Key": API_KEY,
        },
        json={
            "text": text,
            "model_id": MODEL,
            "voice_settings": VOICE_SETTINGS,
        },
    )
    if response.status_code == 200:
        with open(filepath, "wb") as f:
            f.write(response.content)
        print(f"  ✓ Saved to {os.path.basename(filepath)}")
        return True
    else:
        print(f"  ✗ ElevenLabs failed ({response.status_code}): {response.text[:120]}")
        return False

def main():
    os.makedirs(AUDIO_DIR, exist_ok=True)
    if not os.path.exists(STORIES_JSON):
        print(f"stories.json not found! Creating a blank structure at: {STORIES_JSON}")
        with open(STORIES_JSON, "w", encoding="utf-8") as f:
            json.dump({"stories": []}, f, indent=2)

    with open(STORIES_JSON, "r", encoding="utf-8") as f:
        content = json.load(f)

    updated = False
    for story in content.get("stories", []):
        story_id = story["id"]
        for lang in ["en", "hi"]:
            if lang not in story.get("pages", {}):
                continue
            for i, page in enumerate(story["pages"][lang]):
                filename = f"story_{story_id}_{lang}_{i}.mp3"
                filepath = os.path.join(AUDIO_DIR, filename)
                text = page["text"].replace(". ", ", ").replace("! ", "! ")
                
                success = download_audio(text, filepath, voice_for(lang))
                if success:
                    page["audio"] = f"https://nayansrivastav.github.io/ANS/assets/audio/{filename}"
                    updated = True

    if updated:
        with open(STORIES_JSON, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
        print("✓ Updated stories.json with web audio URLs")

if __name__ == "__main__":
    main()
