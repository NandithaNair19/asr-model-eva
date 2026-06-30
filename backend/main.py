from fastapi import FastAPI, UploadFile, File, Form
import shutil
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from googletrans import Translator
from gtts import gTTS
from jiwer import wer, cer
import pandas as pd
import seaborn as sns
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import tempfile
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from asr_eval import LANGUAGES, USE_MOCK, mock_asr, real_asr

app = FastAPI()
translator = Translator()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("results", exist_ok=True)
app.mount("/results", StaticFiles(directory="results"), name="results")


class EvalRequest(BaseModel):
    sentence: str


@app.get("/health")
def health():
    return {"status": "ok"}


def translate_sentence(sentence, target_lang):
    return translator.translate(sentence, dest=target_lang).text


def generate_audio(text, lang_code):
    temp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    temp.close()
    gTTS(text=text, lang=lang_code).save(temp.name)
    return temp.name


def save_single_sentence_heatmaps(results):
    os.makedirs("results", exist_ok=True)

    wer_data = pd.DataFrame([
        {lang: v["WER (%)"] for lang, v in results.items() if "WER (%)" in v}
    ])

    cer_data = pd.DataFrame([
        {lang: v["CER (%)"] for lang, v in results.items() if "CER (%)" in v}
    ])

    plt.figure(figsize=(12, 3))
    sns.heatmap(wer_data, annot=True, fmt=".1f", cmap="RdYlGn_r")
    plt.title("Single Sentence ASR Evaluation — WER")
    plt.tight_layout()
    plt.savefig("results/single_wer_heatmap.png", dpi=150)
    plt.close()

    plt.figure(figsize=(12, 3))
    sns.heatmap(cer_data, annot=True, fmt=".1f", cmap="RdYlGn_r")
    plt.title("Single Sentence ASR Evaluation — CER")
    plt.tight_layout()
    plt.savefig("results/single_cer_heatmap.png", dpi=150)
    plt.close()

@app.post("/live-voice-test")
async def live_voice_test(
    file: UploadFile = File(...),
    language: str = Form(...),
    reference: str = Form(...)
):
    os.makedirs("recordings", exist_ok=True)
    # Save the latest recording for debugging/demo purposes.
# This can be switched back to a temporary file after review.
    audio_path = "recordings/latest_recording.webm"

    try:
        with open(audio_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        print("Saved to:", audio_path)
        print("Saved file size:", os.path.getsize(audio_path))
            

        if USE_MOCK:
            hypothesis = mock_asr(audio_path, reference)
        else:
            hypothesis = real_asr(audio_path, LANGUAGES[language]["code"])

        return {
            "language": language,
            "reference": reference,
            "hypothesis": hypothesis,
            "WER (%)": round(wer(reference, hypothesis) * 100, 2),
            "CER (%)": round(cer(reference, hypothesis) * 100, 2),
            "mode": "MOCK" if USE_MOCK else "REAL ASR"
        }

    except Exception as e:
        return {"error": str(e)}

    #finally:
        #if os.path.exists(audio_path):
            #os.unlink(audio_path)

@app.post("/evaluate")
def evaluate(request: EvalRequest):
    sentence = request.sentence.strip()

    if not sentence:
        return {"error": "Sentence cannot be empty"}

    detected = translator.detect(sentence)
    results = {}

    for lang_name, lang_info in LANGUAGES.items():
        lang_code = lang_info["code"]
        audio_path = None

        try:
            translated = translate_sentence(sentence, lang_code)
            audio_path = generate_audio(translated, lang_code)

            if USE_MOCK:
                hypothesis = mock_asr(audio_path, translated)
            else:
                hypothesis = real_asr(audio_path, lang_code)

            results[lang_name] = {
                "translation": translated,
                "hypothesis": hypothesis,
                "WER (%)": round(wer(translated, hypothesis) * 100, 2),
                "CER (%)": round(cer(translated, hypothesis) * 100, 2),
            }

        except Exception as e:
            results[lang_name] = {"error": str(e)}

        finally:
            if audio_path and os.path.exists(audio_path):
                os.unlink(audio_path)

    save_single_sentence_heatmaps(results)

    return {
        "input_sentence": sentence,
        "detected_language": detected.lang,
        "mode": "MOCK" if USE_MOCK else "REAL ASR",
        "results": results,
        "wer_heatmap": "/results/single_wer_heatmap.png",
        "cer_heatmap": "/results/single_cer_heatmap.png",
    }