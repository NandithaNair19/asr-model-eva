from gtts import gTTS
import json
import os

with open("references/references.json", "r", encoding="utf-8") as f:
    data = json.load(f)

languages = {
    "hindi": "hi",
    "tamil": "ta",
    "telugu": "te",
    "marathi": "mr",
    "malayalam": "ml",
    "gujarati": "gu",
    "kannada": "kn"
}

os.makedirs("audio", exist_ok=True)

for sentence in data["sentences"]:
    for lang, code in languages.items():
        text = sentence[lang]
        filename = f"audio/{lang}_{sentence['id']}.mp3"

        tts = gTTS(text=text, lang=code)
        tts.save(filename)

        print(f"Generated {filename}")

print("Audio generation completed.")