import React, { useState, useRef } from "react";

const API_BASE = "http://127.0.0.1:8000";

function App() {
  const [file, setFile] = useState(null);
  const [language, setLanguage] = useState("en");
  const [modelSize, setModelSize] = useState("small");
  const [enableCleaning, setEnableCleaning] = useState(true);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  // Record-then-upload state
  const [recordingStatus, setRecordingStatus] = useState("idle"); // idle | recording | processing
  const [recordError, setRecordError] = useState("");
  const [recordTranscript, setRecordTranscript] = useState("");
  const [recordSummary, setRecordSummary] = useState("");
  const [recordKeyPoints, setRecordKeyPoints] = useState([]);
  const [recordActionItems, setRecordActionItems] = useState([]);

  const mediaRecorderRef = useRef(null);
  const recordedChunksRef = useRef([]);

  const runTranscription = async (selectedFile) => {
    setError("");
    setResult(null);

    if (!selectedFile) {
      setError("Please select an audio file.");
      return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);

    const params = new URLSearchParams();
    if (language) params.append("language", language);
    if (modelSize) params.append("model_size", modelSize);
    params.append("enable_cleaning", enableCleaning ? "true" : "false");

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/transcribe/?${params.toString()}`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || `Request failed with status ${response.status}`);
      }

      const data = await response.json();
      setResult(data);
      setRecordTranscript(data.transcript || "");
      setRecordSummary(data.summary || "");
      setRecordKeyPoints(Array.isArray(data.key_points) ? data.key_points : []);
      setRecordActionItems(Array.isArray(data.action_items) ? data.action_items : []);
    } catch (err) {
      setError(err.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError("Please select an audio file.");
      return;
    }
    await runTranscription(file);
  };

  const startRecording = async () => {
    setRecordError("");
    setRecordingStatus("recording");
    setRecordTranscript("");
    setRecordSummary("");
    setRecordKeyPoints([]);
    setRecordActionItems([]);
    recordedChunksRef.current = [];

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, {
        mimeType: "audio/webm",
      });
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          recordedChunksRef.current.push(e.data);
        }
      };

      recorder.start(1000);
    } catch (err) {
      setRecordError(err.message || "Failed to access microphone.");
      setRecordingStatus("idle");
    }
  };

  const stopRecordingAndTranscribe = async () => {
    const recorder = mediaRecorderRef.current;
    if (!recorder || recorder.state === "inactive") {
      return;
    }

    setRecordingStatus("processing");
    recorder.stop();
    mediaRecorderRef.current = null;

    recorder.onstop = async () => {
      try {
        const chunks = recordedChunksRef.current;
        recordedChunksRef.current = [];
        if (!chunks.length) {
          setRecordError("No audio captured.");
          setRecordingStatus("idle");
          return;
        }

        const blob = new Blob(chunks, { type: "audio/webm" });
        const recordedFile = new File([blob], "meeting-recording.webm", {
          type: "audio/webm",
        });

        await runTranscription(recordedFile);
      } catch (err) {
        setRecordError(err.message || "Failed to process recording.");
      } finally {
        setRecordingStatus("idle");
      }
    };
  };

  return (
    <div className="app-root">
      <header className="app-header">
        <h1>Meeting Assistant</h1>
        <p>Upload a recording or record a meeting and then transcribe it into notes.</p>
      </header>

      <main className="app-main">
        <section className="card">
          <form onSubmit={handleSubmit} className="form">
            <div className="form-row">
              <label className="label">Audio file</label>
              <input
                type="file"
                accept="audio/*"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
            </div>

            <div className="form-row inline">
              <div className="field">
                <label className="label">Language</label>
                <input
                  type="text"
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  placeholder="en"
                />
              </div>

              <div className="field">
                <label className="label">Model size</label>
                <select
                  value={modelSize}
                  onChange={(e) => setModelSize(e.target.value)}
                >
                  <option value="tiny">tiny (fastest, lowest quality)</option>
                  <option value="base">base</option>
                  <option value="small">small (good dev default)</option>
                  <option value="medium">medium (better quality)</option>
                  <option value="large">large (best, slowest)</option>
                </select>
              </div>

              <div className="field toggle">
                <label className="label">Cleaning</label>
                <label className="checkbox">
                  <input
                    type="checkbox"
                    checked={enableCleaning}
                    onChange={(e) => setEnableCleaning(e.target.checked)}
                  />
                  <span>Enable</span>
                </label>
              </div>
            </div>

            <button className="primary-btn" type="submit" disabled={loading}>
              {loading ? "Processing..." : "Transcribe & Summarize"}
            </button>

            {error && <div className="error">{error}</div>}
          </form>
        </section>

        {result && (
          <section className="card results">
            <h2>Results</h2>
            <div className="result-block">
              <h3>Transcript</h3>
              <p className="mono small">{result.transcript || "(empty)"}</p>
            </div>

            <div className="result-block">
              <h3>Summary</h3>
              <p>{result.summary || "(no summary)"}</p>
            </div>

            <div className="result-block">
              <h3>Key points</h3>
              {Array.isArray(result.key_points) && result.key_points.length > 0 ? (
                <ul>
                  {result.key_points.map((point, idx) => (
                    <li key={idx}>{point}</li>
                  ))}
                </ul>
              ) : (
                <p>(no key points)</p>
              )}
            </div>

            <div className="result-block">
              <h3>Action items</h3>
              {Array.isArray(result.action_items) && result.action_items.length > 0 ? (
                <ul>
                  {result.action_items.map((item, idx) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>
              ) : (
                <p>(no action items detected)</p>
              )}
            </div>

            <div className="meta">
              <span>
                Cleaning used: {String(result.cleaning_used)}
              </span>
            </div>
          </section>
        )}

        <section className="card" style={{ marginTop: "2rem" }}>
          <h2>Record meeting (then transcribe)</h2>
          <p className="small" style={{ marginBottom: "1rem" }}>
            Records audio from your microphone locally in a compressed format. When you stop,
            the recording is sent once to the backend for full transcription and summarization.
          </p>

          <div className="form-row inline">
            <div className="field">
              <label className="label">Language</label>
              <input
                type="text"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                placeholder="en"
              />
            </div>

            <div className="field">
              <label className="label">Model size</label>
              <select
                value={modelSize}
                onChange={(e) => setModelSize(e.target.value)}
              >
                <option value="tiny">tiny (fastest, lowest quality)</option>
                <option value="base">base</option>
                <option value="small">small (good dev default)</option>
                <option value="medium">medium (better quality)</option>
                <option value="large">large (best, slowest)</option>
              </select>
            </div>
          </div>

          <div style={{ marginTop: "1rem", display: "flex", gap: "0.75rem" }}>
            <button
              type="button"
              className="primary-btn"
              disabled={recordingStatus === "recording" || recordingStatus === "processing"}
              onClick={startRecording}
            >
              {recordingStatus === "recording" ? "Recording..." : "Start recording"}
            </button>
            <button
              type="button"
              className="primary-btn"
              style={{ background: "#ef4444" }}
              disabled={recordingStatus !== "recording"}
              onClick={stopRecordingAndTranscribe}
            >
              Stop & transcribe
            </button>
          </div>
          {recordError && <div className="error" style={{ marginTop: "0.75rem" }}>{recordError}</div>}

          <div className="result-block" style={{ marginTop: "1.25rem" }}>
            <h3>Recorded transcript</h3>
            <p className="mono small" style={{ whiteSpace: "pre-wrap" }}>
              {recordTranscript || "(no recording processed yet)"}
            </p>
          </div>

          <div className="result-block">
            <h3>Recorded summary</h3>
            <p>{recordSummary || "(no summary yet)"}</p>
          </div>

          <div className="result-block">
            <h3>Recorded key points</h3>
            {recordKeyPoints.length > 0 ? (
              <ul>
                {recordKeyPoints.map((p, idx) => (
                  <li key={idx}>{p}</li>
                ))}
              </ul>
            ) : (
              <p>(no key points yet)</p>
            )}
          </div>

          <div className="result-block">
            <h3>Recorded action items</h3>
            {recordActionItems.length > 0 ? (
              <ul>
                {recordActionItems.map((p, idx) => (
                  <li key={idx}>{p}</li>
                ))}
              </ul>
            ) : (
              <p>(no action items yet)</p>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;

