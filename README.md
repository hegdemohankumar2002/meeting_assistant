
# AI Meeting Assistant (MVP)

This project is a local **AI meeting assistant** that turns spoken discussions into structured notes. It transcribes audio using Whisper and summarizes the content into a concise overview, key points, and action items.

Current MVP supports two flows:

- **Upload recording**: upload an existing audio file and get transcript + summary.
- **Record meeting (then transcribe)**: record from your microphone in the browser, then send the full recording once for transcription and summarization.

---

## Features

- Local transcription with Whisper (GPU used when available).
- Summarization using a HuggingFace model (BART).
- Structured output:
  - Full transcript
  - Summary
  - Key points
  - Action items (heuristically detected tasks / follow‑ups)

---

## Running the project

From the project root:

### 1. Backend (FastAPI)

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # PowerShell
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt
python backend\run.py
```

Backend runs on `http://127.0.0.1:8000` with docs at `http://127.0.0.1:8000/docs`.

### 2. Frontend (React)

```bash
cd frontend
npm install
npm start
```

Frontend runs on `http://localhost:3000`.

---

## Usage

1. Start backend and frontend.
2. Open `http://localhost:3000`.
3. Choose either:
   - **Upload recording**: pick an audio file, set language/model, and click **Transcribe & Summarize**.
   - **Record meeting (then transcribe)**: click **Start recording**, speak, then click **Stop & transcribe** to send the meeting recording for processing.
4. Review:
   - Transcript
   - Summary
   - Key points
   - Action items

This repository represents the working MVP checkpoint and can be extended later with diarization, emotion/decision detection, knowledge graph, and integrations.

