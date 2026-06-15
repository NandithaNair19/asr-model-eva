import numpy as np
import soundfile as sf
from pydub import AudioSegment
import io
import json
import os
import base64
import random
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from jiwer import wer, cer

# Config
ASR_ENDPOINT = "http://<your server>/v2/models/asr_am_ensemble/infer"
USE_MOCK = False  

LANGUAGES = {
    "hindi":     {"code": "hi", "service_id": "ai4bharat/asr-wav2vec2-hindi"},
    "tamil":     {"code": "ta", "service_id": "ai4bharat/asr-wav2vec2-tamil"},
    "telugu":    {"code": "te", "service_id": "ai4bharat/asr-wav2vec2-telugu"},
    "marathi":   {"code": "mr", "service_id": "ai4bharat/asr-wav2vec2-marathi"},
    "malayalam": {"code": "ml", "service_id": "ai4bharat/asr-wav2vec2-malayalam"},
    "gujarati":  {"code": "gu", "service_id": "ai4bharat/asr-wav2vec2-gujarati"},
    "kannada":   {"code": "kn", "service_id": "ai4bharat/asr-wav2vec2-kannada"},
}

UNSUPPORTED = ["assamese", "garo", "khasi"]

#  Mock ASR 
def mock_asr(audio_path, reference_text):
    """Reads audio file to confirm it exists, then simulates ASR response."""
    # Actually read the audio file
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()
    file_size = len(audio_bytes)
    print(f"     Audio file read: {audio_path} ({file_size} bytes)")

    # Simulate ASR errors randomly
    words = reference_text.split()
    error_rate = random.uniform(0.05, 0.45)
    num_errors = int(len(words) * error_rate)
    for _ in range(num_errors):
        idx = random.randint(0, len(words) - 1)
        words[idx] = "????"
    return " ".join(words)

#  Real ASR 
def real_asr(audio_path, language_code, service_id):
    import requests
    print(f"     Calling real ASR endpoint for {audio_path}...")
    
    # rest of the function...
    
    # Convert mp3 to wav and load as float array
    audio = AudioSegment.from_mp3(audio_path)
    audio = audio.set_frame_rate(16000).set_channels(1)
    
    # Convert to numpy float32 array
    samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
    samples = samples / 32768.0  # normalize to -1 to 1
    num_samples = len(samples)
    
    payload = {
        "inputs": [
            {
                "name": "AUDIO_SIGNAL",
                "shape": [1, num_samples],
                "datatype": "FP32",
                "data": samples.tolist()
            },
            {
                "name": "NUM_SAMPLES",
                "shape": [1, 1],
                "datatype": "INT32",
                "data": [num_samples]
            },
            {
                "name": "LANG_ID",
                "shape": [1, 1],
                "datatype": "BYTES",
                "data": [language_code]
            }
        ]
    }
    
    response = requests.post(
        "http://13.200.133.97:5000/v2/models/asr_am_ensemble/infer",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    result = response.json()
    print(f"    📡 Server response status: {response.status_code}")
    return result["outputs"][0]["data"][0]

# Main Evaluation
def run_evaluation():
    with open("references/references.json") as f:
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
                hyp_text = real_asr(
                    audio_path,
                    LANGUAGES[lang]["code"],
                    LANGUAGES[lang]["service_id"]
                )

            references.append(ref_text)
            hypotheses.append(hyp_text)
            print(f"    ✓ Sentence {sentence['id']}")
            print(f"      REF: {ref_text}")
            print(f"      HYP: {hyp_text}")

        if references:
            word_error_rate = wer(references, hypotheses)
            char_error_rate = cer(references, hypotheses)
            results[lang] = {
                "WER (%)": round(word_error_rate * 100, 2),
                "CER (%)": round(char_error_rate * 100, 2)
            }
            print(f" WER: {results[lang]['WER (%)']}% | CER: {results[lang]['CER (%)']}%")
        else:
            print(f"   No audio files found for {lang}")

    return results

#  Save Results 
def save_results(results):
    os.makedirs("results", exist_ok=True)

    # CSV report
    df = pd.DataFrame([
        {"Language": lang, "WER (%)": v["WER (%)"], "CER (%)": v["CER (%)"]}
        for lang, v in results.items()
    ])
    df = df.sort_values("WER (%)")
    df.to_csv("results/report.csv", index=False)
    print("\n Report saved to results/report.csv")
    print(df.to_string(index=False))

    # Heatmap for WER
    wer_data = pd.DataFrame([{lang: v["WER (%)"] for lang, v in results.items()}])
    plt.figure(figsize=(12, 3))
    sns.heatmap(
        wer_data,
        annot=True,
        fmt=".1f",
        cmap="RdYlGn_r",
        linewidths=0.5,
        cbar_kws={"label": "WER (%) — lower is better"}
    )
    plt.title(
        "Cross-Language ASR Consistency — WER\n(Word Error Rate % — lower is better)",
        fontsize=13
    )
    plt.tight_layout()
    plt.savefig("results/wer_heatmap.png", dpi=150)
    print(" WER Heatmap saved to results/wer_heatmap.png")

    # Heatmap for CER
    cer_data = pd.DataFrame([{lang: v["CER (%)"] for lang, v in results.items()}])
    plt.figure(figsize=(12, 3))
    sns.heatmap(
        cer_data,
        annot=True,
        fmt=".1f",
        cmap="RdYlGn_r",
        linewidths=0.5,
        cbar_kws={"label": "CER (%) — lower is better"}
    )
    plt.title(
        "Cross-Language ASR Consistency — CER\n(Character Error Rate % — lower is better)",
        fontsize=13
    )
    plt.tight_layout()
    plt.savefig("results/cer_heatmap.png", dpi=150)
    print(" CER Heatmap saved to results/cer_heatmap.png")

    # Summary
    best = min(results, key=lambda x: results[x]["WER (%)"])
    worst = max(results, key=lambda x: results[x]["WER (%)"])
    avg_wer = round(sum(v["WER (%)"] for v in results.values()) / len(results), 2)
    avg_cer = round(sum(v["CER (%)"] for v in results.values()) / len(results), 2)
    print(f"\n Summary:")
    print(f"   Best language:  {best} (WER: {results[best]['WER (%)']}%)")
    print(f"   Worst language: {worst} (WER: {results[worst]['WER (%)']}%)")
    print(f"   Average WER: {avg_wer}%")
    print(f"   Average CER: {avg_cer}%")

    # Unsupported languages
    print("\n  Unsupported languages (no TTS/dataset available):")
    for lang in UNSUPPORTED:
        print(f"   - {lang.capitalize()}: real audio recordings needed")
#  Run 
if __name__ == "__main__":
    print(" Starting Cross-Language ASR Consistency Evaluation")
    print(f"   Mode: {'MOCK' if USE_MOCK else 'REAL ASR'}")
    print(f"   Languages: {', '.join(LANGUAGES.keys())}")
    print(f"   Sentences: 10 per language\n")
    results = run_evaluation()
    save_results(results)
    print("\n Evaluation complete!")