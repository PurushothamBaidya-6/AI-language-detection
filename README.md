# AI Language Detection

Open-source web app that detects the language of **text**, **speech** and **text inside images**, then translates it to English.

| Input  | Library |
|--------|---------|
| Text   | `langdetect` (language) + `deep-translator` (English) |
| Speech | OpenAI `whisper` (detects and translates) |
| Image  | `easyocr` (reads text) then `langdetect` |

Built with Python and Flask. Licensed under MIT.

## Run locally

Requirements: Python 3.10 to 3.12 and [ffmpeg](https://ffmpeg.org/download.html) on your PATH.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open http://localhost:5000. The first speech and image requests download the models, so they are slow once.

Use a smaller speech model on weak machines: `WHISPER_MODEL=tiny python app.py`.

## Publish it on GitHub

```bash
git init
git add .
git commit -m "AI language detection"
git branch -M main
git remote add origin https://github.com/<your-username>/ai-language-detection.git
git push -u origin main
```

## Get a public link (free): Hugging Face Spaces

1. Create an account at huggingface.co, then **New Space**.
2. Choose **Docker** as the SDK and the free CPU hardware.
3. Upload every file in this folder (or push the repo to the Space).
4. Wait for the build. Your link will look like `https://<user>-<space>.hf.space`.

Other hosts that run the included `Dockerfile` also work (Render, Railway, Fly.io). Set `WHISPER_MODEL=tiny` if memory is tight.

## Notes and limits

- Translation uses Google Translate through `deep-translator`, so the server needs internet access.
- EasyOCR needs a script group chosen up front (Latin, Hindi, Kannada and so on); it cannot guess the script.
- The image feature reads text in the image. It does not describe pictures that contain no text.
- Very short text (one or two words) is hard to detect reliably.
- Browser recording needs https or localhost.
