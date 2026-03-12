import React, { useState, useRef, useEffect } from "react";

const API_BASE = "http://localhost:8000";
const WS_BASE  = "ws://localhost:8000";

const RESULT_TABS = ["Summary", "Transcript", "Speakers", "Roadmap", "Insights"];

const STAGES = [
    { key: "upload",       label: "Uploading audio…" },
    { key: "transcription",label: "Transcribing with Whisper…" },
    { key: "diarization",  label: "Identifying speakers…" },
    { key: "analysis",     label: "Generating AI insights…" },
    { key: "complete",     label: "Finalizing…" },
];

function renderMarkdown(text) {
    if (!text) return null;
    return text.split("\n").map((line, i) => {
        if (line.startsWith("# "))   return <h1 key={i}>{line.slice(2)}</h1>;
        if (line.startsWith("## "))  return <h2 key={i}>{line.slice(3)}</h2>;
        if (line.startsWith("### ")) return <h3 key={i}>{line.slice(4)}</h3>;
        if (line.match(/^[-*] /))    return <li key={i}>{line.slice(2)}</li>;
        if (!line.trim())             return <br key={i} />;
        return <p key={i} style={{ marginBottom: "0.4rem", lineHeight: 1.7 }}>{line}</p>;
    });
}

function renderItem(item) {
    if (typeof item === "string") return item;
    if (typeof item === "object" && item !== null) {
        if (item.Owner && item.Verb && item.Task) return `${item.Owner} to ${item.Verb} ${item.Task}`;
        return Object.values(item).filter(Boolean).join(" — ");
    }
    return String(item);
}

const MeetingTab = ({ mode }) => {
    const [file,          setFile]          = useState(null);
    const [language,      setLanguage]      = useState("en");
    const [modelSize,     setModelSize]     = useState("small");
    const [meetingTitle,  setMeetingTitle]  = useState("");
    const [loading,       setLoading]       = useState(false);
    const [error,         setError]         = useState("");
    const [result,        setResult]        = useState(null);
    const [activeResultTab, setActiveResultTab] = useState("Summary");

    // Live recording state
    const [partialTranscript, setPartialTranscript] = useState("");
    const [fullTranscript,    setFullTranscript]    = useState("");
    const [isRecording,       setIsRecording]       = useState(false);
    const [currentStage,      setCurrentStage]      = useState("");
    const [doneStages,        setDoneStages]        = useState([]);

    const wsRef               = useRef(null);
    const mediaRecorderRef    = useRef(null);
    const recordedChunksRef   = useRef([]);
    const chunkRecorderRef    = useRef(null);
    const chunkTimerRef       = useRef(null);
    const isTranscribingRef   = useRef(false);
    const speechRecognitionRef= useRef(null);
    const captionsEndRef      = useRef(null);
    const isRecordingRef      = useRef(false);

    useEffect(() => { isRecordingRef.current = isRecording; }, [isRecording]);
    useEffect(() => { captionsEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [partialTranscript, fullTranscript]);

    const advanceStage = (key) => {
        setCurrentStage(key);
        setDoneStages(prev => [...prev, key]);
    };

    /* ── Microphone recording ── */
    const startMicrophone = async () => {
        setError(""); setResult(null); setPartialTranscript(""); setFullTranscript("");
        setDoneStages([]); setCurrentStage(""); setIsRecording(true); isRecordingRef.current = true;
        try {
            const stream   = await navigator.mediaDevices.getUserMedia({ audio: true });

            // 1. Browser SpeechRecognition purely for instant visual feedback (no final results)
            if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
                const Rec = window.SpeechRecognition || window.webkitSpeechRecognition;
                const r = new Rec(); r.continuous = true; r.interimResults = true; r.lang = "en-US";
                r.onresult = (ev) => {
                    let interim = "";
                    for (let i = ev.resultIndex; i < ev.results.length; ++i) {
                        interim += ev.results[i][0].transcript;
                    }
                    setPartialTranscript(interim);
                };
                r.onerror = (ev) => { if (ev.error !== "no-speech") console.error(ev.error); };
                r.onend   = () => { if (isRecordingRef.current) { setTimeout(() => { try { r.start(); } catch {}}, 250); } };
                r.start(); 
                speechRecognitionRef.current = r;

                // Aggressive Watchdog to ensure it stays alive across long pauses
                const watchdog = setInterval(() => {
                    if (isRecordingRef.current && r) {
                        try { r.start(); } catch (e) {} // Throws harmlessly if already running
                    }
                }, 2000);
                speechRecognitionRef.current._watchdog = watchdog;
            }
            
            // 2. Main Recorder (Continuous, perfect quality for final analysis)
            const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
            mediaRecorderRef.current  = recorder; recordedChunksRef.current = [];
            recorder.ondataavailable  = (e) => { if (e.data.size > 0) recordedChunksRef.current.push(e.data); };
            recorder.start(1000);

            // 3. Chunk Recorder (4s loops) to get true Whisper punctuated live captions
            const startChunkRecorder = () => {
                if (!isRecordingRef.current) return;
                try {
                    const chunkRec = new MediaRecorder(stream, { mimeType: "audio/webm" });
                    const localChunks = [];
                    chunkRec.ondataavailable = e => { if (e.data.size > 0) localChunks.push(e.data); };
                    chunkRec.onstop = async () => {
                        if (localChunks.length === 0 || !isRecordingRef.current) return;
                        if (isTranscribingRef.current) return; // Skip to prevent backlog on slow CPUs
                        
                        isTranscribingRef.current = true;
                        const blob = new Blob(localChunks, { type: "audio/webm" });
                        const fd = new FormData();
                        fd.append("file", blob, "chunk.webm");
                        try {
                            const res = await fetch(`${API_BASE}/transcribe/chunk`, { method: "POST", body: fd });
                            if (res.ok) {
                                const data = await res.json();
                                if (data.text) {
                                    setPartialTranscript(""); // Clear interim prediction
                                    setFullTranscript(p => p + (p ? " " : "") + data.text.trim());
                                }
                            }
                        } catch (err) {}
                        finally { isTranscribingRef.current = false; }
                    };
                    chunkRec.start();
                    chunkRecorderRef.current = chunkRec;
                    
                    chunkTimerRef.current = setTimeout(() => {
                        if (chunkRec.state !== "inactive") chunkRec.stop();
                        startChunkRecorder();
                    }, 4000); // Send to whisper every 4s
                } catch (e) { console.error("Chunk setup error", e); }
            };
            startChunkRecorder();

        } catch (err) { setError("Microphone failed: " + err.message); setIsRecording(false); }
    };

    const stopMicrophone = async () => {
        if (!mediaRecorderRef.current) return;
        setIsRecording(false); isRecordingRef.current = false;
        
        // Stop browser speech recognition
        if (speechRecognitionRef.current) {
            clearInterval(speechRecognitionRef.current._watchdog);
            speechRecognitionRef.current.onend = null;
            speechRecognitionRef.current.stop();
            speechRecognitionRef.current = null;
        }

        // Stop live chunk whisper
        if (chunkTimerRef.current) clearTimeout(chunkTimerRef.current);
        if (chunkRecorderRef.current && chunkRecorderRef.current.state !== "inactive") {
            chunkRecorderRef.current.onstop = null; // Don't trigger another fetch on shutdown
            chunkRecorderRef.current.stop();
        }

        setCurrentStage("upload"); setLoading(true);
        const rec  = mediaRecorderRef.current;
        const done = new Promise(res => { rec.onstop = () => res(); });
        rec.stop(); await done;
        const blob = new Blob(recordedChunksRef.current, { type: "audio/webm" });
        await handleFileUploadStream(new File([blob], "mic_recording.webm", { type: "audio/webm" }));
        rec.stream.getTracks().forEach(t => t.stop());
        mediaRecorderRef.current = null;
        chunkRecorderRef.current = null;
    };

    /* ── File upload + WebSocket processing ── */
    const handleFileUploadStream = async (f) => {
        if (!f) return;
        setLoading(true); setResult(null); setError("");
        setDoneStages(["upload"]); setCurrentStage("transcription");
        try {
            const fd  = new FormData(); fd.append("file", f);
            const res = await fetch(`${API_BASE}/upload`, { method: "POST", body: fd });
            if (!res.ok) throw new Error("Upload failed");
            const { file_path } = await res.json();

            const ws = new WebSocket(`${WS_BASE}/ws/transcribe`);
            wsRef.current = ws;
            ws.onopen = () => ws.send(JSON.stringify({ file_path, language, model_size: modelSize, title: meetingTitle || undefined }));
            ws.onmessage = (ev) => {
                const data = JSON.parse(ev.data);
                if (data.error) { setError(data.error); ws.close(); setLoading(false); return; }
                if (data.stage === "transcription" && data.status === "progress") { setCurrentStage("transcription"); setPartialTranscript(data.partial_text); }
                if (data.stage === "transcription" && data.status === "done")    { advanceStage("transcription"); setCurrentStage("diarization"); }
                if (data.stage === "diarization") { if (data.status === "done") advanceStage("diarization"); setCurrentStage("analysis"); }
                if (data.stage === "analysis")    { setCurrentStage("analysis"); }
                if (data.type  === "summary")     { setResult(p => ({ ...p, ...data.data })); }
                if (data.type  === "insights")    { setResult(p => ({ ...p, insights: data.data })); }
                if (data.type  === "role_summaries") { setResult(p => ({ ...p, role_summaries: data.data })); advanceStage("analysis"); setCurrentStage("complete"); }
                if (data.stage === "complete") {
                    setResult(p => ({ ...p, roadmap: data.roadmap, decisions: data.decisions, title: data.title, meeting_id: data.meeting_id }));
                    advanceStage("complete"); setLoading(false); setCurrentStage("");
                }
            };
            ws.onerror = () => { setError("WebSocket Connection Error"); setLoading(false); };
        } catch (err) { setError(err.message); setLoading(false); }
    };

    const speakers = result?.speakers || [];
    const segments = result?.segments || [];
    const insights = result?.insights || {};

    return (
        <div className="section-enter">
            {/* ── Control Card ── */}
            <div className="card">
                {mode === "mic" ? (
                    <div>
                        <div className="flex-between" style={{ marginBottom: 16 }}>
                            <div>
                                <div style={{ fontWeight: 700, color: "var(--text-1)", fontSize: "0.95rem", marginBottom: 2 }}>Live Recording</div>
                                <div style={{ color: "var(--text-3)", fontSize: "0.82rem" }}>Capture audio from your microphone and analyze it with AI.</div>
                            </div>
                            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                                {isRecording && (
                                    <span className="status-pill live"><span className="dot" /> Recording</span>
                                )}
                                {isRecording ? (
                                    <button className="primary-btn" onClick={stopMicrophone}
                                        style={{ background: "var(--red)", borderColor: "var(--red)" }}>
                                        ⏹ Stop &amp; Analyze
                                    </button>
                                ) : (
                                    <button className="primary-btn" onClick={startMicrophone} disabled={loading}>
                                        🎙&nbsp; Start Recording
                                    </button>
                                )}
                            </div>
                        </div>
                        <div className="form-group" style={{ marginBottom: 0 }}>
                            <label className="form-label">Meeting title (optional)</label>
                            <input className="form-input" style={{ maxWidth: 400 }}
                                placeholder="e.g., Q2 Planning Call"
                                value={meetingTitle} onChange={e => setMeetingTitle(e.target.value)} />
                        </div>
                    </div>
                ) : (
                    <div style={{ display: "flex", gap: 16, flexWrap: "wrap", alignItems: "flex-end" }}>
                        <div className="form-group" style={{ flex: 1, minWidth: 220, marginBottom: 0 }}>
                            <label className="form-label">Audio File</label>
                            <input className="form-input" type="file" accept="audio/*"
                                onChange={e => setFile(e.target.files[0])} />
                        </div>
                        <div className="form-group" style={{ minWidth: 180, marginBottom: 0 }}>
                            <label className="form-label">Meeting Title (optional)</label>
                            <input className="form-input" placeholder="e.g., Design Review"
                                value={meetingTitle} onChange={e => setMeetingTitle(e.target.value)} />
                        </div>
                        <button className="primary-btn" disabled={loading || !file}
                            onClick={() => handleFileUploadStream(file)}>
                            {loading ? "Processing…" : "✨ Analyze"}
                        </button>
                    </div>
                )}
                {error && <div className="alert alert-error">⚠ {error}</div>}
            </div>

            {/* ── Live Monitor ── */}
            {(isRecording || loading || fullTranscript || partialTranscript) && (
                <div className="live-monitor">
                    {isRecording && (
                        <div className="live-status-badge">
                            <span className="dot-pulse" /> LIVE
                        </div>
                    )}

                    <div className="active-viz" style={!isRecording ? {opacity: 0.3} : {}}>
                        {[...Array(8)].map((_, i) => <div key={i} className="viz-bar" />)}
                    </div>

                    {loading && !isRecording && (
                        <div className="process-stages" style={{ marginBottom: "1.5rem", marginTop: 0 }}>
                            {STAGES.map(s => {
                                const isDone   = doneStages.includes(s.key);
                                const isActive = currentStage === s.key && !isDone;
                                return (
                                    <div key={s.key} className={`process-stage ${isDone ? "done" : isActive ? "active" : ""}`}>
                                        {isDone   ? "✓" :
                                         isActive ? <div className="stage-spinner" /> :
                                                    <span style={{ width: 14, display: "inline-block", opacity: 0.3 }}>○</span>}
                                        {s.label}
                                    </div>
                                );
                            })}
                        </div>
                    )}

                    <div className="live-text" style={{ width: "90%" }}>
                        {fullTranscript}
                        {partialTranscript && <span className="live-partial"> {partialTranscript}</span>}
                        <div ref={captionsEndRef} />
                    </div>
                </div>
            )}

            {/* ── Results ── */}
            {result && (
                <div className="section-enter">
                    <div className="flex-between" style={{ marginBottom: 16 }}>
                        <div>
                            <h2 style={{ fontWeight: 800, fontSize: "1.1rem", color: "var(--text-1)", letterSpacing: "-0.02em" }}>
                                {result.title || result.inferred_agenda || "Meeting Results"}
                            </h2>
                            {result.meeting_id && (
                                <span className="badge badge-green" style={{ marginTop: 4 }}>✓ Saved as #{result.meeting_id}</span>
                            )}
                        </div>
                    </div>

                    <div className="tabs-header">
                        {RESULT_TABS.map(t => (
                            <button key={t} className={`tab-btn ${activeResultTab === t ? "active" : ""}`} onClick={() => setActiveResultTab(t)}>{t}</button>
                        ))}
                    </div>

                    <div className="tab-content">
                        {/* Summary */}
                        {activeResultTab === "Summary" && (
                            <div>
                                <div className="card" style={{ marginBottom: 14 }}>
                                    <div className="result-card-header"><div className="result-title">📝 Executive Brief</div></div>
                                    <p style={{ color: "var(--text-2)", lineHeight: 1.8, fontSize: "0.9rem" }}>{result.summary || "—"}</p>
                                </div>
                                <div className="results-grid">
                                    <div className="card">
                                        <div className="result-card-header"><div className="result-title">🔑 Key Points</div></div>
                                        <ul className="result-list">{(result.key_points||[]).map((k,i) => <li key={i}>{renderItem(k)}</li>)}</ul>
                                    </div>
                                    <div className="card">
                                        <div className="result-card-header"><div className="result-title" style={{ color: "var(--amber)" }}>⚡ Action Items</div></div>
                                        <ul className="result-list">{(result.action_items||[]).map((a,i) => <li key={i}>{renderItem(a)}</li>)}</ul>
                                    </div>
                                    {(result.role_summaries?.executive || result.role_summaries?.technical) && (<>
                                        <div className="card">
                                            <div className="result-card-header"><div className="result-title">👔 Executive View</div></div>
                                            <p style={{ color: "var(--text-2)", fontSize: "0.875rem" }}>{result.role_summaries.executive}</p>
                                        </div>
                                        <div className="card">
                                            <div className="result-card-header"><div className="result-title">🔧 Technical View</div></div>
                                            <p style={{ color: "var(--text-2)", fontSize: "0.875rem" }}>{result.role_summaries.technical}</p>
                                        </div>
                                    </>)}
                                </div>
                            </div>
                        )}

                        {/* Transcript */}
                        {activeResultTab === "Transcript" && (
                            <div className="card" style={{ maxHeight: 500, overflowY: "auto", padding: "4px 0" }}>
                                {segments.length > 0 ? segments.map((seg, i) => {
                                    const sp    = speakers.find(s => s.id === seg.speaker_id);
                                    const color = sp?.color || "#6366f1";
                                    return (
                                        <div key={i} className="segment-item">
                                            <div className="segment-speaker-dot" style={{ background: color }}>{(sp?.label || "?")[0]}</div>
                                            <div className="segment-body">
                                                <div className="segment-header">
                                                    <span className="segment-speaker-name" style={{ color }}>{sp?.label || seg.speaker_id || "Unknown"}</span>
                                                    <span className="segment-time">{seg.start?.toFixed ? `${seg.start.toFixed(1)}s` : ""}</span>
                                                </div>
                                                <div className="segment-text">{seg.text}</div>
                                            </div>
                                        </div>
                                    );
                                }) : (
                                    <pre style={{ padding: "1rem", color: "var(--text-2)", fontSize: "0.85rem", whiteSpace: "pre-wrap", lineHeight: 1.7 }}>{result.transcript || "No transcript."}</pre>
                                )}
                            </div>
                        )}

                        {/* Speakers */}
                        {activeResultTab === "Speakers" && (
                            <div className="card">
                                {speakers.length > 0 ? (
                                    <div className="speakers-grid">
                                        {speakers.map((s, i) => (
                                            <div key={i} className="speaker-chip">
                                                <div className="speaker-color-dot" style={{ background: s.color }} />
                                                <span>{s.label}</span>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="empty-state"><div className="empty-icon">👥</div><h3>No speaker data</h3><p>Diarization may not have run.</p></div>
                                )}
                            </div>
                        )}

                        {/* Roadmap */}
                        {activeResultTab === "Roadmap" && (
                            <div className="card markdown-body" style={{ maxHeight: 500, overflowY: "auto" }}>
                                {result.roadmap ? renderMarkdown(result.roadmap) : (
                                    <div className="empty-state"><div className="empty-icon">🗺</div><h3>No roadmap generated</h3></div>
                                )}
                            </div>
                        )}

                        {/* Insights */}
                        {activeResultTab === "Insights" && (
                            <div className="results-grid">
                                <div className="card">
                                    <div className="result-card-header"><div className="result-title" style={{ color: "var(--green)" }}>✅ Decisions</div></div>
                                    {(insights.decisions||result.decisions||[]).length > 0
                                        ? <ul className="result-list">{(insights.decisions||result.decisions||[]).map((d,i)=><li key={i}>{renderItem(d)}</li>)}</ul>
                                        : <p style={{ color: "var(--text-4)", fontSize: "0.85rem" }}>None extracted.</p>}
                                </div>
                                <div className="card">
                                    <div className="result-card-header"><div className="result-title" style={{ color: "var(--sky)" }}>🤝 Agreements</div></div>
                                    {(insights.agreements||[]).length > 0
                                        ? <ul className="result-list">{(insights.agreements||[]).map((a,i)=><li key={i}>{renderItem(a)}</li>)}</ul>
                                        : <p style={{ color: "var(--text-4)", fontSize: "0.85rem" }}>None extracted.</p>}
                                </div>
                                <div className="card">
                                    <div className="result-card-header"><div className="result-title" style={{ color: "var(--red)" }}>⚠ Conflicts</div></div>
                                    {(insights.conflicts||[]).length > 0
                                        ? <ul className="result-list">{(insights.conflicts||[]).map((c,i)=><li key={i}>{renderItem(c)}</li>)}</ul>
                                        : <p style={{ color: "var(--text-4)", fontSize: "0.85rem" }}>None detected.</p>}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default MeetingTab;
