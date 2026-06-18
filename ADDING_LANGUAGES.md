# Adding New Languages to asr-model-eva

This guide explains how to add a new language to the evaluation tool — from creating the dataset to generating audio and running the evaluation.

---

## Step 1 — Check if gTTS supports your language

gTTS uses Google Translate's TTS engine. Check if your language is supported:

```python
from gtts.lang import tts_langs
print(tts_langs())
```

Common Indic language codes:
| Language | gTTS Code |
|---|---|
| Hindi | hi |
| Tamil | ta |
| Telugu | te |
| Marathi | mr |
| Malayalam | ml |
| Gujarati | gu |
| Kannada | kn |
| Bengali | bn |
| Punjabi | pa |
| Assamese | as |
| Urdu | ur |

If your language is not in the list, see the **Unsupported Languages** section at the bottom.

---

## Step 2 — Add translations to references.json

Open `references/references.json` and add your language to each sentence. For example, to add Bengali:

```json
{
  "id": 1,
  "english": "The child is going to school",
  "hindi": "बच्चा स्कूल जा रहा है",
  "tamil": "குழந்தை பள்ளிக்கு செல்கிறது",
  ...
  "bengali": "শিশু স্কুলে যাচ্ছে"
}
```

Do this for all 10 sentences.

---

## Step 3 — Add language to generate_audio.py

Open `generate_audio.py` and add your language to the `languages` dictionary:

```python
languages = {
    'hindi': 'hi',
    'tamil': 'ta',
    ...
    'bengali': 'bn',  # add this
}
```

---

## Step 4 — Add language to asr_eval.py

Open `asr_eval.py` and add your language to the `LANGUAGES` dictionary:

```python
LANGUAGES = {
    "hindi": {"code": "hi", "service_id": "ai4bharat/asr-wav2vec2-hindi"},
    ...
    "bengali": {"code": "bn", "service_id": "ai4bharat/asr-wav2vec2-bengali"},
}
```

> Note: The `service_id` should match the model name on your Triton inference server. 

---

## Step 5 — Generate audio files

```bash
python3 generate_audio.py
```

This will generate 10 new MP3 files in the `audio/` folder for your language.

---

## Step 6 — Run the evaluation

```bash
python3 asr_eval.py
```

Your new language will now appear in the results!

---

## Adding Your Own Custom Sentences

You don't have to use the default 10 sentences. You can create your own dataset:

**1. Create your references.json:**
```json
{
  "sentences": [
    {
      "id": 1,
      "english": "Your sentence in English",
      "hindi": "Your sentence in Hindi",
      "tamil": "Your sentence in Tamil"
    },
    {
      "id": 2,
      ...
    }
  ]
}
```

**Tips for choosing good test sentences:**
- Use everyday practical sentences
- Mix short (3-5 words) and long (8-12 words) sentences
- Include sentences with numbers, questions, and statements
- Avoid rare or technical words
- Use sentences relevant to your use case (medical, legal, casual etc.)

---

## Unsupported Languages (no gTTS support)

For languages not supported by gTTS (Garo, Khasi, Bodo etc.), you have these options:

**Option 1 — IndicVoices-R Dataset**
AI4Bharat has real human recordings for Bodo, Santali, Manipuri and more. Request access at [ai4bharat.iitm.ac.in/datasets/IndicVoices-R](https://ai4bharat.iitm.ac.in/datasets/IndicVoices-R).

**Option 2 — Record native speakers**
Record native speakers saying your test sentences on a phone. Save as MP3 files named `<language>_<id>.mp3` (e.g. `garo_1.mp3`) in the `audio/` folder and add the correct transcripts to `references.json`.
