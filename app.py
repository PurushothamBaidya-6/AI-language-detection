"""AI Language Detection: detect the language of text, speech or an image and translate it to English."""
import os, tempfile
from flask import Flask, jsonify, render_template, request
from langdetect import DetectorFactory, detect
from deep_translator import GoogleTranslator

DetectorFactory.seed = 0  # make langdetect deterministic
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 25 MB uploads

NAMES = {"en": "English", "fr": "French", "es": "Spanish", "de": "German", "it": "Italian",
         "pt": "Portuguese", "hi": "Hindi", "kn": "Kannada", "ta": "Tamil", "te": "Telugu",
         "ml": "Malayalam", "mr": "Marathi", "bn": "Bengali", "gu": "Gujarati", "pa": "Punjabi",
         "ur": "Urdu", "ar": "Arabic", "ru": "Russian", "ja": "Japanese", "ko": "Korean",
         "zh": "Chinese", "zh-cn": "Chinese (Simplified)", "zh-tw": "Chinese (Traditional)",
         "nl": "Dutch", "tr": "Turkish", "pl": "Polish", "id": "Indonesian", "vi": "Vietnamese",
         "th": "Thai", "sv": "Swedish", "el": "Greek", "ne": "Nepali"}

# EasyOCR needs a language list up front, so the user picks a script group.
OCR_GROUPS = {
    "latin": ["en", "fr", "es", "de", "it", "pt"],
    "hindi": ["hi", "mr", "ne", "en"],
    "kannada": ["kn", "en"], "tamil": ["ta", "en"], "telugu": ["te", "en"],
    "bengali": ["bn", "as", "en"], "arabic": ["ar", "fa", "ur", "en"],
    "russian": ["ru", "en"], "japanese": ["ja", "en"], "korean": ["ko", "en"],
    "chinese": ["ch_sim", "en"],
}

_whisper = None
_ocr = {}


def whisper_model():
    global _whisper
    if _whisper is None:
        import whisper
        _whisper = whisper.load_model(os.environ.get("WHISPER_MODEL", "base"))
    return _whisper


def ocr_reader(group):
    if group not in _ocr:
        import easyocr
        _ocr[group] = easyocr.Reader(OCR_GROUPS[group], gpu=False)
    return _ocr[group]


def to_english(text, code):
    if code.split("-")[0] == "en":
        return text
    return GoogleTranslator(source="auto", target="en").translate(text[:4500])


def analyse(text):
    text = (text or "").strip()
    if not text:
        return {"error": "No text found."}, 400
    code = detect(text)
    return {"original": text, "code": code, "language": NAMES.get(code, code),
            "english": to_english(text, code)}, 200


@app.get("/")
def index():
    return render_template("index.html", groups=list(OCR_GROUPS))


@app.post("/api/text")
def api_text():
    body, status = analyse((request.get_json(silent=True) or {}).get("text"))
    return jsonify(body), status


@app.post("/api/speech")
def api_speech():
    f = request.files.get("audio")
    if not f:
        return jsonify(error="No audio received."), 400
    with tempfile.NamedTemporaryFile(suffix=os.path.splitext(f.filename or "a.webm")[1] or ".webm",
                                     delete=False) as tmp:
        f.save(tmp.name)
    try:
        model = whisper_model()
        spoken = model.transcribe(tmp.name)  # detects language and transcribes
        code = spoken["language"]
        english = model.transcribe(tmp.name, task="translate")["text"].strip()
        return jsonify(original=spoken["text"].strip(), code=code,
                       language=NAMES.get(code, code), english=english)
    finally:
        os.unlink(tmp.name)


@app.post("/api/image")
def api_image():
    f = request.files.get("image")
    group = request.form.get("group", "latin")
    if not f or group not in OCR_GROUPS:
        return jsonify(error="Send an image and a valid script group."), 400
    with tempfile.NamedTemporaryFile(suffix=".img", delete=False) as tmp:
        f.save(tmp.name)
    try:
        text = " ".join(ocr_reader(group).readtext(tmp.name, detail=0))
    finally:
        os.unlink(tmp.name)
    body, status = analyse(text)
    if status == 400:
        body["error"] = "No readable text found in the image."
    return jsonify(body), status


@app.errorhandler(Exception)
def fail(e):
    code = getattr(e, "code", 500)
    return jsonify(error=str(e)), code if isinstance(code, int) else 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
