import numpy as np
from pydub import AudioSegment
import json
import unicodedata
import re
import os
import random
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from jiwer import wer, cer
from dotenv import load_dotenv

load_dotenv()

# Config
USE_MOCK = os.getenv("USE_MOCK", "true").lower() == "true"
ASR_ENDPOINT = os.getenv("ASR_ENDPOINT")
REFERENCE_FILE = os.getenv("REFERENCE_FILE", "references/references.json")


def normalize_text(text):
    # Unicode normalization
    text = unicodedata.normalize("NFC", text)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    # Remove all Unicode punctuation
    text = "".join(
        ch for ch in text
        if not unicodedata.category(ch).startswith("P")
    )

    return text.strip()



if not USE_MOCK and not ASR_ENDPOINT:
    raise ValueError("ASR_ENDPOINT is not set. Please add it to your .env file.")


LANGUAGES = {
    "hindi": {"code": "hi"},
    "tamil": {"code": "ta"},
    "telugu": {"code": "te"},
    "marathi": {"code": "mr"},
    "malayalam": {"code": "ml"},
    "gujarati": {"code": "gu"},
    "kannada": {"code": "kn"},
    "bengali": {"code": "bn"},
    "punjabi": {"code": "pa"},
}

UNSUPPORTED = ["assamese", "garo", "khasi"]


# Mock ASR
def mock_asr(audio_path, reference_text):
    """Reads audio file to confirm it exists, then simulates ASR response."""
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()

    file_size = len(audio_bytes)
    print(f"     Audio file read: {audio_path} ({file_size} bytes)")

    words = reference_text.split()
    error_rate = random.uniform(0.05, 0.45)
    num_errors = int(len(words) * error_rate)

    for _ in range(num_errors):
        idx = random.randint(0, len(words) - 1)
        words[idx] = "????"

    return " ".join(words)


# Real ASR
# NOTE: real_asr() is not tested in CI as it requires access to a private inference server.
# Test manually by setting USE_MOCK=false in .env and running: python3 asr_eval.py
def real_asr(audio_path, language_code):
    import requests

    print(f"     Calling real ASR endpoint for {audio_path}...")

    audio = AudioSegment.from_file(audio_path)
    audio = audio.set_frame_rate(16000).set_channels(1)

    samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
    samples = samples / 32768.0
    num_samples = len(samples)

    payload = {
        "inputs": [
            {
                "name": "AUDIO_SIGNAL",
                "shape": [1, num_samples],
                "datatype": "FP32",
                "data": samples.tolist(),
            },
            {
                "name": "NUM_SAMPLES",
                "shape": [1, 1],
                "datatype": "INT32",
                "data": [num_samples],
            },
            {
                "name": "LANG_ID",
                "shape": [1, 1],
                "datatype": "BYTES",
                "data": [language_code],
            },
        ]
    }

    response = requests.post(
        ASR_ENDPOINT,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=60,
    )

    response.raise_for_status()

    result = response.json()
    print(f"    Server response status: {response.status_code}")
    return result["outputs"][0]["data"][0]


# Main Evaluation
def run_evaluation():
    with open(REFERENCE_FILE) as f:
        data = json.load(f)

    results = {}

    for lang in LANGUAGES:
        print(f"\n Evaluating {lang}...")
        references = []
        hypotheses = []

        for sentence in data["sentences"]:
            ref_text = sentence[lang]
            audio_path = f"audio/{lang}_{sentence['id']}.mp3"

            if not os.path.exists(audio_path):
                print(f"      Audio file not found: {audio_path}, skipping...")
                continue

            if USE_MOCK:
                hyp_text = mock_asr(audio_path, ref_text)
            else:
                hyp_text = real_asr(audio_path, LANGUAGES[lang]["code"])

            references.append(ref_text)
            hypotheses.append(hyp_text)

            print(f"      Sentence {sentence['id']}")
            print(f"      REF: {ref_text}")
            print(f"      HYP: {hyp_text}")

        if references:
            references_norm = [normalize_text(t) for t in references]
            hypotheses_norm = [normalize_text(t) for t in hypotheses]

            word_error_rate = wer(references_norm, hypotheses_norm)
            char_error_rate = cer(references_norm, hypotheses_norm)

            results[lang] = {
                "WER (%)": round(word_error_rate * 100, 2),
                "CER (%)": round(char_error_rate * 100, 2),
            }

            print(
                f" WER: {results[lang]['WER (%)']}% | CER: {results[lang]['CER (%)']}%"
            )
        else:
            print(f"   No audio files found for {lang}")

    return results


# Save Results
def save_results(results):
    os.makedirs("results", exist_ok=True)

    df = pd.DataFrame(
        [
            {"Language": lang, "WER (%)": v["WER (%)"], "CER (%)": v["CER (%)"]}
            for lang, v in results.items()
        ]
    )

    df = df.sort_values("WER (%)")
    df.to_csv("results/report.csv", index=False)

    print("\n Report saved to results/report.csv")
    print(df.to_string(index=False))

    wer_data = pd.DataFrame([{lang: v["WER (%)"] for lang, v in results.items()}])
    plt.figure(figsize=(12, 3))
    sns.heatmap(
        wer_data,
        annot=True,
        fmt=".1f",
        cmap="RdYlGn_r",
        linewidths=0.5,
        cbar_kws={"label": "WER (%) — lower is better"},
    )
    plt.title(
        "Cross-Language ASR Consistency — WER\n(Word Error Rate % — lower is better)",
        fontsize=13,
    )
    plt.tight_layout()
    plt.savefig("results/wer_heatmap.png", dpi=150)
    print(" WER Heatmap saved to results/wer_heatmap.png")

    cer_data = pd.DataFrame([{lang: v["CER (%)"] for lang, v in results.items()}])
    plt.figure(figsize=(12, 3))
    sns.heatmap(
        cer_data,
        annot=True,
        fmt=".1f",
        cmap="RdYlGn_r",
        linewidths=0.5,
        cbar_kws={"label": "CER (%) — lower is better"},
    )
    plt.title(
        "Cross-Language ASR Consistency — CER\n(Character Error Rate % — lower is better)",
        fontsize=13,
    )
    plt.tight_layout()
    plt.savefig("results/cer_heatmap.png", dpi=150)
    print(" CER Heatmap saved to results/cer_heatmap.png")

    best = min(results, key=lambda x: results[x]["WER (%)"])
    worst = max(results, key=lambda x: results[x]["WER (%)"])
    avg_wer = round(sum(v["WER (%)"] for v in results.values()) / len(results), 2)
    avg_cer = round(sum(v["CER (%)"] for v in results.values()) / len(results), 2)

    print("\n Summary:")
    print(f"   Best language:  {best} (WER: {results[best]['WER (%)']}%)")
    print(f"   Worst language: {worst} (WER: {results[worst]['WER (%)']}%)")
    print(f"   Average WER: {avg_wer}%")
    print(f"   Average CER: {avg_cer}%")

    print("\n  Unsupported languages (no TTS/dataset available):")
    for lang in UNSUPPORTED:
        print(f"   - {lang.capitalize()}: real audio recordings needed")


# Run
if __name__ == "__main__":
    print(" Starting Cross-Language ASR Consistency Evaluation")
    print(f"   Mode: {'MOCK' if USE_MOCK else 'REAL ASR'}")
    print(f"   Languages: {', '.join(LANGUAGES.keys())}")
    print("   Sentences: configurable via REFERENCE_FILE\n")

    results = run_evaluation()
    save_results(results)

    print("\n Evaluation complete!")