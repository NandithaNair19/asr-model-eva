import tempfile
from gtts import gTTS


def generate_audio(text, lang_code):
    temp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    temp.close()

    gTTS(text=text, lang=lang_code).save(temp.name)

    return temp.name