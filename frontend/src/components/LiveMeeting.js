import React, { useState, useRef, useEffect } from "react";

const API_BASE_WS = "ws://127.0.0.1:8000/ws/meeting";

function LiveMeeting() {
    const [status, setStatus] = useState("idle"); // idle | connecting | live | error | finished
    const [transcript, setTranscript] = useState("");
    const [summary, setSummary] = useState("");
    const [keyPoints, setKeyPoints] = useState([]);
    const [actionItems, setActionItems] = useState([]);
    const [error, setError] = useState("");

    const socketRef = useRef(null);
    const mediaRecorderRef = useRef(null);

    const startSession = async () => {
        setError("");
        setStatus("connecting");
        setTranscript("");
        setSummary("");
        setKeyPoints([]);
        setActionItems([]);

        try {
            // 1. Open WebSocket
            const socket = new WebSocket(API_BASE_WS);
            socketRef.current = socket;

            socket.onopen = () => {
                // Send start message
                socket.send(JSON.stringify({ type: "start", language: "en", model_size: "base" }));
            };

            socket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === "started") {
                    setStatus("live");
                    startRecording();
                } else if (data.type === "partial_transcript") {
                    setTranscript(data.full_transcript);
                } else if (data.type === "summary_update") {
                    setSummary(data.summary);
                    setKeyPoints(data.key_points || []);
                    setActionItems(data.action_items || []);
                } else if (data.type === "final") {
                    setTranscript(data.transcript);
                    setSummary(data.summary);
                    setKeyPoints(data.key_points || []);
                    setActionItems(data.action_items || []);
                    setStatus("finished");
                } else if (data.type === "error") {
                    setError(data.message);
                    setStatus("error");
                }
            };

            socket.onerror = (err) => {
                console.error("WebSocket error:", err);
                setError("Connection failed.");
                setStatus("error");
            };

            socket.onclose = () => {
                if (status === "live") {
                    // Unexpected close
                    setStatus("finished");
                }
            };

        } catch (err) {
            setError(err.message);
            setStatus("error");
        }
    };

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
            mediaRecorderRef.current = recorder;

            recorder.ondataavailable = (e) => {
                if (e.data.size > 0 && socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
                    // Send binary data
                    socketRef.current.send(e.data);
                }
            };

            recorder.start(1000); // Send chunks every 1s
        } catch (err) {
            setError("Microphone access failed: " + err.message);
            setStatus("error");
            if (socketRef.current) socketRef.current.close();
        }
    };

    const stopSession = () => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
            mediaRecorderRef.current.stop();
        }
        if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
            socketRef.current.send(JSON.stringify({ type: "end" }));
        }
        // Status will update to 'finished' when backend sends 'final' message
    };

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (mediaRecorderRef.current) mediaRecorderRef.current.stop();
            if (socketRef.current) socketRef.current.close();
        };
    }, []);

    return (
        <div className="live-meeting">
            <div className="controls">
                {status === "idle" || status === "finished" || status === "error" ? (
                    <button className="primary-btn" onClick={startSession}>
                        {status === "idle" ? "Start Live Session" : "Start New Session"}
                    </button>
                ) : (
                    <button className="primary-btn danger" onClick={stopSession} disabled={status !== "live"}>
                        {status === "connecting" ? "Connecting..." : "Stop Session"}
                    </button>
                )}
                {status === "live" && <span className="live-indicator">🔴 Live</span>}
            </div>

            {error && <div className="error">{error}</div>}

            <div className="live-content">
                <div className="panel">
                    <h3>Live Transcript</h3>
                    <div className="transcript-box">
                        {transcript || <span className="placeholder">Waiting for speech...</span>}
                    </div>
                </div>

                <div className="panel">
                    <h3>Live Summary</h3>
                    <div className="summary-box">
                        <p>{summary || <span className="placeholder">Summary will update periodically...</span>}</p>

                        {keyPoints.length > 0 && (
                            <>
                                <h4>Key Points</h4>
                                <ul>
                                    {keyPoints.map((kp, i) => <li key={i}>{kp}</li>)}
                                </ul>
                            </>
                        )}

                        {actionItems.length > 0 && (
                            <>
                                <h4>Action Items</h4>
                                <ul>
                                    {actionItems.map((ai, i) => <li key={i}>{ai}</li>)}
                                </ul>
                            </>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default LiveMeeting;
