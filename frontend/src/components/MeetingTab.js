import React, { useState, useRef, useEffect } from "react";

const API_BASE = "http://127.0.0.1:8000";
const WS_BASE = "ws://127.0.0.1:8000";

const MeetingTab = ({ mode }) => { // mode: 'mic' | 'file'
    const [file, setFile] = useState(null);
    const [language, setLanguage] = useState("en");
    const [modelSize, setModelSize] = useState("small");

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [result, setResult] = useState(null);

    // Live State
    const [partialTranscript, setPartialTranscript] = useState("");
    const [fullTranscript, setFullTranscript] = useState("");
    const [isRecording, setIsRecording] = useState(false);
    const [processingStage, setProcessingStage] = useState("");

    const wsRef = useRef(null);
    const mediaRecorderRef = useRef(null);
    const recordedChunksRef = useRef([]);
    const speechRecognitionRef = useRef(null);
    const captionsEndRef = useRef(null);
    const isRecordingRef = useRef(false);

    useEffect(() => {
        isRecordingRef.current = isRecording;
    }, [isRecording]);

    useEffect(() => {
        captionsEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [partialTranscript, fullTranscript]);

    const startMicrophone = async () => {
        setError("");
        setResult(null);
        setPartialTranscript("");
        setFullTranscript("");
        setIsRecording(true);
        isRecordingRef.current = true;
        setLoading(false);

        try {
            // 1. Browser Speech Recognition (Visuals)
            if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                const recognition = new SpeechRecognition();
                recognition.continuous = true;
                recognition.interimResults = true;
                recognition.lang = "en-US";

                recognition.onresult = (event) => {
                    let interim = "";
                    let finalChunk = "";
                    for (let i = event.resultIndex; i < event.results.length; ++i) {
                        if (event.results[i].isFinal) {
                            finalChunk += event.results[i][0].transcript;
                        } else {
                            interim += event.results[i][0].transcript;
                        }
                    }
                    if (finalChunk) setFullTranscript(prev => prev + finalChunk + " ");
                    setPartialTranscript(interim);
                };

                recognition.onend = () => {
                    if (isRecordingRef.current) {
                        try { recognition.start(); } catch (e) { }
                    }
                };

                recognition.start();
                speechRecognitionRef.current = recognition;
            }

            // 2. MediaRecorder (Audio Capture)
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
            mediaRecorderRef.current = recorder;
            recordedChunksRef.current = [];

            recorder.ondataavailable = (e) => {
                if (e.data.size > 0) recordedChunksRef.current.push(e.data);
            };

            recorder.start(1000);

        } catch (err) {
            setError("Microphone failed: " + err.message);
            setIsRecording(false);
        }
    };

    const stopMicrophone = async () => {
        if (!mediaRecorderRef.current) return;
        setIsRecording(false);
        isRecordingRef.current = false;

        if (speechRecognitionRef.current) {
            speechRecognitionRef.current.onend = null;
            speechRecognitionRef.current.stop();
            speechRecognitionRef.current = null;
        }

        setProcessingStage("Finalizing recording...");
        setLoading(true);

        const recorder = mediaRecorderRef.current;
        const recordingPromise = new Promise((resolve) => { recorder.onstop = () => resolve(); });
        recorder.stop();
        await recordingPromise;

        const blob = new Blob(recordedChunksRef.current, { type: "audio/webm" });
        const recordedFile = new File([blob], "mic_recording.webm", { type: "audio/webm" });

        await handleFileUploadStream(recordedFile);

        recorder.stream.getTracks().forEach(track => track.stop());
        mediaRecorderRef.current = null;
    };

    const handleFileUploadStream = async (selectedFile) => {
        if (!selectedFile) return;

        setLoading(true);
        setProcessingStage("Initializing AI...");

        try {
            const formData = new FormData();
            formData.append("file", selectedFile);

            setProcessingStage("Uploading audio...");
            const res = await fetch(`${API_BASE}/upload`, { method: "POST", body: formData });
            if (!res.ok) throw new Error("Upload failed");
            const { file_path } = await res.json();

            const ws = new WebSocket(`${WS_BASE}/ws/transcribe`);
            wsRef.current = ws;

            ws.onopen = () => {
                setProcessingStage("Connected. Transcribing...");
                ws.send(JSON.stringify({ file_path, language, model_size: modelSize }));
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.error) { setError(data.error); ws.close(); }

                if (data.stage === "transcription" && data.status === "progress") {
                    setProcessingStage("Transcribing...");
                    setPartialTranscript(data.partial_text);
                }
                if (data.stage === "diarization") { setProcessingStage("Identifying speakers..."); }
                if (data.stage === "analysis") { setProcessingStage("Generating insights..."); }
                if (data.type === "summary") { setResult(prev => ({ ...prev, ...data.data })); }
                if (data.type === "role_summaries") {
                    setResult(prev => ({ ...prev, role_summaries: data.data }));
                    setLoading(false);
                    setProcessingStage("");
                    ws.close();
                }
                if (data.type === "insights") { setResult(prev => ({ ...prev, insights: data.data })); }
            };

            ws.onerror = () => { setError("WebSocket Connection Error"); setLoading(false); };

        } catch (err) {
            setError(err.message);
            setLoading(false);
        }
    };

    // Helper to render markdown
    const renderMarkdown = (text) => {
        if (!text) return null;
        return text.split('\n').map((line, i) => {
            // Basic markdown parsing
            if (line.startsWith('# ')) return <h1 key={i}>{line.substring(2)}</h1>;
            if (line.startsWith('## ')) return <h2 key={i}>{line.substring(3)}</h2>;
            if (line.startsWith('### ')) return <h3 key={i}>{line.substring(4)}</h3>;
            if (line.startsWith('- ')) return <li key={i}>{line.substring(2)}</li>;
            return <p key={i}>{line}</p>;
        });
    };

    return (
        <div className="meeting-tab">
            {/* --- Action Area --- */}
            <div className="card" style={{ marginBottom: '2rem' }}>
                {mode === 'mic' ? (
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
                            <h3 style={{ marginBottom: '0.2rem' }}>Live Session</h3>
                            <p style={{ color: 'var(--text-secondary)', margin: 0 }}>Capture audio directly from your microphone.</p>
                        </div>
                        {isRecording ? (
                            <button className="primary-btn" style={{ background: 'var(--danger)' }} onClick={stopMicrophone}>
                                ⏹ Stop & Process
                            </button>
                        ) : (
                            <button className="primary-btn" onClick={startMicrophone} disabled={loading}>
                                🎙 Start Microphone
                            </button>
                        )}
                    </div>
                ) : (
                    <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end' }}>
                        <div style={{ flex: 1 }}>
                            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>Upload Recording</label>
                            <input
                                type="file"
                                onChange={(e) => setFile(e.target.files[0])}
                                style={{ width: '100%', padding: '0.5rem', background: 'var(--bg-primary)', border: '1px solid var(--border-color)', borderRadius: '8px', color: 'white' }}
                            />
                        </div>
                        <button className="primary-btn" disabled={loading || !file} onClick={() => handleFileUploadStream(file)}>
                            {loading ? "Processing..." : "Start Processing"}
                        </button>
                    </div>
                )}
                {error && <div style={{ color: 'var(--danger)', marginTop: '1rem', background: 'rgba(239, 68, 68, 0.1)', padding: '0.5rem', borderRadius: '8px' }}>{error}</div>}
            </div>

            {/* --- Live Monitor --- */}
            {(isRecording || loading || fullTranscript || partialTranscript) && (
                <div className="live-monitor">
                    <div className="monitor-bg"></div>
                    {isRecording && (
                        <div className="live-status-badge">
                            <div className="dot-pulse"></div> LIVE
                        </div>
                    )}

                    <div className="active-viz">
                        {[...Array(5)].map((_, i) => <div key={i} className="viz-bar"></div>)}
                    </div>

                    <div className="live-text" style={{ maxHeight: '200px', overflowY: 'auto', width: '100%' }}>
                        {fullTranscript} <span style={{ color: 'var(--accent-secondary)' }}>{partialTranscript}</span>
                        {loading && !isRecording && (
                            <div style={{ marginTop: '1rem', color: 'var(--accent-primary)' }}>⏳ {processingStage}</div>
                        )}
                        <div ref={captionsEndRef} />
                    </div>
                </div>
            )}

            {/* --- Results --- */}
            {result && (
                <div className="results-grid">
                    {/* Executive Summary */}
                    <div className="card" style={{ gridColumn: '1 / -1' }}>
                        <div className="result-card-header">
                            <div className="result-title">📝 Executive Brief</div>
                        </div>
                        <h3 style={{ color: 'var(--accent-primary)', marginBottom: '1rem' }}>{result.inferred_agenda || "Meeting Agenda"}</h3>
                        <p style={{ color: 'var(--text-secondary)' }}>{result.summary}</p>
                    </div>

                    {/* Decisions */}
                    <div className="card">
                        <div className="result-card-header">
                            <div className="result-title" style={{ color: 'var(--success)' }}>✅ Key Decisions</div>
                        </div>
                        <ul className="result-list">
                            {result.decisions?.map((d, i) => <li key={i}>{d}</li>)}
                        </ul>
                    </div>

                    {/* Action Items */}
                    <div className="card">
                        <div className="result-card-header">
                            <div className="result-title" style={{ color: 'var(--warning)' }}>⚡ Action Items</div>
                        </div>
                        <ul className="result-list">
                            {result.action_items?.map((item, i) => <li key={i}>{item}</li>)}
                        </ul>
                    </div>

                    {/* Roadmap */}
                    {result.roadmap && (
                        <div className="card" style={{ gridColumn: '1 / -1' }}>
                            <div className="result-card-header">
                                <div className="result-title" style={{ color: 'var(--danger)' }}>🚀 Strategic Roadmap</div>
                            </div>
                            <div className="markdown-body">
                                {renderMarkdown(result.roadmap)}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default MeetingTab;
