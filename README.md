# Next-Gen Cognitive AI Meeting Assistant

A privacy-first, local intelligence platform that records, transcribes, and analyzes meetings in real-time. Unlike cloud-based tools, this assistant runs entirely on your device (Edge AI), ensuring 100% data privacy while delivering deep cognitive insights.

---

## 🚀 Key Features (Updated)

### 1. **Real-Time Streaming & Transcription**
*   **Live Feedback**: Uses WebSockets to stream transcription character-by-character as you speak.
*   **Faster-Whisper**: Integrated `faster-whisper` (int8 quantization) for 4x faster performance than standard Whisper.
*   **Large File Support**: Intelligent chunking allows processing of long meetings (1 hour+) without memory crashes.

### 2. **Cognitive Intelligence**
*   **Emotion Recognition**: Analyzes the sentiment of each segment (Positive/Negative/Neutral) to capture the *tone* of the meeting.
*   **Smart Insights**: Uses Zero-Shot NLP (`bart-large-mnli`) to automatically extract:
    *   ✅ **Decisions**: e.g., "We chose to launch on Friday."
    *   🤝 **Agreements**: e.g., "I agree with that approach."
    *   ⚠️ **Conflicts**: e.g., "I don't think that will work."

### 3. **Advanced Summarization**
*   **Role-Based Summaries**: Generates distinct reports for different stakeholders.
*   **Structured Output**: Auto-generates Key Points and Action Items.
*   **🧠 Hybrid Cloud Mode**: Automatically switches to **GPT-3.5/4** if an OpenAI key is detected, delivering human-level reasoning and perfect summarization quality.

### 4. **Speaker Diarization**
*   **Who Said What**: Integrates `pyannote.audio` to distinguish between multiple speakers (Speaker 0, Speaker 1, etc.).

### 5. **Privacy-First Architecture**
*   **Local Execution**: All ML models run locally. No audio data is sent to the cloud.
*   **Structured Database**: Stores all meetings and insights in a local SQL database for easy retrieval.

---

## 🛠️ Project Architecture

*   **Frontend**: React.js 18 (Real-time Dashboard)
*   **Backend**: FastAPI (Asynchronous Python Server)
*   **Database**: SQLite (SQLAlchemy ORM)
*   **AI Models**:
    *   **ASR**: `faster-whisper-small`
    *   **Diarization**: `pyannote/speaker-diarization-3.1`
    *   **NLP**: `facebook/bart-large-mnli` & `facebook/bart-large-cnn`
    *   **Emotion**: `j-hartmann/emotion-english-distilroberta-base`

---

## 🏃‍♂️ How to Run

### Prerequisite
Ensure you have Python 3.10+ and Node.js installed.

### 1. Backend Setup
```bash
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

### 1.1. Configure Environment (Optional but Recommended)
Create a `.env` file in the `backend` folder to enable advanced features:
```env
# Required for optimal Speaker Diarization
HF_TOKEN=your_huggingface_token

# Required for Smart Hybrid Summarization (ChatGPT/Gemini quality)
OPENAI_API_KEY=sk-...
```

*Backend runs at `http://127.0.0.1:8000`*

### 2. Frontend Setup
```bash
cd frontend
npm install
npm start
```
*Frontend runs at `http://localhost:3000`*

---

## 🐳 Running with Docker (Recommended)

The easiest way to run the project with all dependencies (including `ffmpeg`) is using Docker.

### 1. Build and Start
```bash
docker-compose up --build
```

### 2. Access the Application
- **Frontend**: `http://localhost:3000`
- **Backend API Docs**: `http://localhost:8000/docs`

> [!TIP]
> This command will automatically set up both the backend and frontend, link them together, and manage the `ffmpeg` installation for you.

---

---

## 📝 Usage Guide
1.  **Open Dashboard**: Go to localhost:3000.
2.  **Select Mode**:
    *   **Live Stream**: Speak into the microphone and see text appear instantly.
    *   **Upload**: Upload an existing .wav/.mp3 file.
3.  **View Analysis**:
    *   Watch the **Live Transcript** update.
    *   Check the **Smart Insights** tab for extracted decisions.
    *   Review **Role-Specific Summaries** at the end.

---

## ⚠️ Notes
*   **First Run**: The first time you run the app, it will download necessary ML models (~2GB). This may take a few minutes.
*   **GPU Support**: If you have an NVIDIA GPU, install CUDA toolkit for 10x faster performance.
