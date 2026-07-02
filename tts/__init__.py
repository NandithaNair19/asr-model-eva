import importlib
import os
from dotenv import load_dotenv

load_dotenv()

TTS_PROVIDER = os.getenv("TTS_PROVIDER", "gtts").lower()

def generate_audio(text, lang_code):
    try:
        provider_module = importlib.import_module(
            f"tts.{TTS_PROVIDER}_provider"
        )
    except ModuleNotFoundError:
        raise ValueError(
            f"Unsupported TTS provider: {TTS_PROVIDER}. "
            f"Create tts/{TTS_PROVIDER}_provider.py with a generate_audio(text, lang_code) function."
        )

    if not hasattr(provider_module, "generate_audio"):
        raise ValueError(
            f"Provider tts/{TTS_PROVIDER}_provider.py must define generate_audio(text, lang_code)."
        )

    return provider_module.generate_audio(text, lang_code)