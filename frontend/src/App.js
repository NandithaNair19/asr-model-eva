import { useEffect, useState } from "react";

function App() {
  const [activeTab, setActiveTab] = useState("text");

  const [selectedLanguage, setSelectedLanguage] = useState("hindi");
  const [voiceReference, setVoiceReference] = useState("");
  const [recording, setRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [audioBlob, setAudioBlob] = useState(null);
  const [voiceResult, setVoiceResult] = useState(null);

  const [sentence, setSentence] = useState("");
  const [results, setResults] = useState(null);
  const [meta, setMeta] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const languages = [
    "hindi",
    "tamil",
    "telugu",
    "marathi",
    "malayalam",
    "gujarati",
    "kannada",
    "bengali",
    "punjabi",
  ];

  const fetchVoiceReference = async (language) => {
    try {
      setError(null);
      setVoiceResult(null);
      setAudioBlob(null);

      const response = await fetch(`http://localhost:8000/reference/${language}`);
      const data = await response.json();

      if (data.error) {
        setError(data.error);
        return;
      }

      setVoiceReference(data.reference);
    } catch (err) {
      setError("Failed to fetch reference sentence.");
    }
  };

  useEffect(() => {
    if (activeTab === "voice") {
      fetchVoiceReference(selectedLanguage);
    }
  }, [activeTab, selectedLanguage]);

  const startRecording = async () => {
    try {
      setError(null);
      setVoiceResult(null);
      setAudioBlob(null);

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks = [];

      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          chunks.push(event.data);
        }
      };

      recorder.onstop = () => {
        const blob = new Blob(chunks, {
          type: recorder.mimeType || "audio/webm",
        });

        console.log("Recorded blob size:", blob.size);
        setAudioBlob(blob);
        stream.getTracks().forEach((track) => track.stop());
      };

      recorder.start(1000);
      setMediaRecorder(recorder);
      setRecording(true);
    } catch (err) {
      setError("Microphone access denied or not available.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
      mediaRecorder.requestData();
      mediaRecorder.stop();
      setRecording(false);
    }
  };

  const runLiveVoiceTest = async () => {
    if (!audioBlob) {
      setError("Please record audio first.");
      return;
    }

    if (!voiceReference) {
      setError("Reference sentence is still loading. Please try again.");
      return;
    }

    setLoading(true);
    setError(null);
    setVoiceResult(null);

    const formData = new FormData();
    formData.append("file", audioBlob, "recording.webm");
    formData.append("language", selectedLanguage);
    formData.append("reference", voiceReference);

    try {
      const response = await fetch("http://localhost:8000/live-voice-test", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (data.error) {
        setError(data.error);
        return;
      }

      setVoiceResult(data);
    } catch (err) {
      setError("Failed to run live voice test.");
    } finally {
      setLoading(false);
    }
  };

  const evaluate = async () => {
    if (!sentence.trim()) return;

    setLoading(true);
    setError(null);
    setResults(null);
    setMeta(null);

    try {
      const response = await fetch("http://localhost:8000/evaluate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sentence }),
      });

      const data = await response.json();

      if (data.error) {
        setError(data.error);
        return;
      }

      setResults(data.results);
      setMeta(data);
    } catch (err) {
      setError("Failed to connect to backend. Make sure FastAPI is running.");
    } finally {
      setLoading(false);
    }
  };

  const getColor = (wer) => {
    if (wer <= 10) return "#4ade80";
    if (wer <= 20) return "#facc15";
    if (wer <= 35) return "#fb923c";
    return "#f87171";
  };

  return (
    <div style={pageStyle}>
      <h1 style={{ textAlign: "center" }}>Cross-Language ASR Evaluator</h1>

      <p style={{ textAlign: "center", color: "#666" }}>
        Evaluate ASR consistency across Indic languages.
      </p>

      <div style={tabContainerStyle}>
        <button
          onClick={() => setActiveTab("text")}
          style={activeTab === "text" ? activeTabStyle : inactiveTabStyle}
        >
          Text Evaluation
        </button>

        <button
          onClick={() => setActiveTab("voice")}
          style={activeTab === "voice" ? activeTabStyle : inactiveTabStyle}
        >
          Live Voice Test
        </button>
      </div>

      {activeTab === "text" && (
        <>
          <p style={{ textAlign: "center", color: "#666" }}>
            Type a sentence — it will be translated and evaluated across 9 Indic
            languages.
          </p>

          <div style={{ display: "flex", gap: 10, marginBottom: 20 }}>
            <input
              value={sentence}
              onChange={(e) => setSentence(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && evaluate()}
              placeholder="Type a sentence in any language..."
              style={inputStyle}
            />

            <button onClick={evaluate} disabled={loading} style={primaryButtonStyle}>
              {loading ? "Evaluating..." : "Evaluate"}
            </button>
          </div>
        </>
      )}

      {activeTab === "voice" && (
        <div style={voiceCardStyle}>
          <h2>Live Voice Test</h2>

          <p style={{ color: "#666" }}>
            Select a language, read the displayed sentence aloud, and test the
            ASR output against the known reference.
          </p>

          <div style={{ marginTop: 20 }}>
            <label style={{ fontWeight: "bold" }}>Language:</label>
            <br />

            <select
              value={selectedLanguage}
              onChange={(e) => {
                setSelectedLanguage(e.target.value);
                setVoiceResult(null);
                setAudioBlob(null);
              }}
              style={selectStyle}
            >
              {languages.map((lang) => (
                <option key={lang} value={lang}>
                  {lang.charAt(0).toUpperCase() + lang.slice(1)}
                </option>
              ))}
            </select>
          </div>

          <div style={referenceBoxStyle}>
            <h3>Reference Sentence</h3>
            <p style={referenceSentenceStyle}>{voiceReference || "Loading..."}</p>
          </div>

          <div style={{ marginTop: 25 }}>
            {!recording ? (
              <button onClick={startRecording} style={recordButtonStyle}>
                Start Recording
              </button>
            ) : (
              <button onClick={stopRecording} style={stopButtonStyle}>
                Stop Recording
              </button>
            )}
          </div>

          <p style={{ color: "#666", marginTop: 15 }}>
            {recording
              ? "Recording... please read the sentence aloud."
              : audioBlob
              ? "Recording saved. Click Run Live Voice Test."
              : "Click Start Recording and read the sentence aloud."}
          </p>

          {audioBlob && !recording && (
            <button
              onClick={runLiveVoiceTest}
              disabled={loading}
              style={{
                marginTop: 20,
                padding: "12px 24px",
                fontSize: 16,
                backgroundColor: "#6366f1",
                color: "white",
                border: "none",
                borderRadius: 8,
                cursor: "pointer",
              }}
            >
              {loading ? "Running..." : "Run Live Voice Test"}
            </button>
          )}

          {voiceResult && (
            <div style={voiceResultStyle}>
              <h3>Live Voice Result</h3>
              <p>
                <b>ASR Output:</b> {voiceResult.hypothesis}
              </p>
              <p>
                <b>WER:</b> {voiceResult["WER (%)"]}%
              </p>
              <p>
                <b>CER:</b> {voiceResult["CER (%)"]}%
              </p>
            </div>
          )}
        </div>
      )}

      {error && <p style={{ color: "red", textAlign: "center" }}>{error}</p>}

      {loading && activeTab === "text" && (
        <p style={{ textAlign: "center", color: "#666" }}>
          Detecting language, translating, generating audio and running ASR
          evaluation...
        </p>
      )}

      {meta && activeTab === "text" && (
        <p style={{ textAlign: "center", color: "#555" }}>
          Detected language: <b>{meta.detected_language}</b> | Mode:{" "}
          <b>{meta.mode}</b>
        </p>
      )}

      {results && activeTab === "text" && (
        <>
          <h2>Results</h2>

          <div style={resultCardsStyle}>
            {Object.entries(results).map(([lang, data]) => (
              <div
                key={lang}
                style={{
                  flex: 1,
                  minWidth: 100,
                  padding: 12,
                  borderRadius: 8,
                  backgroundColor: data.error
                    ? "#e2e8f0"
                    : getColor(data["WER (%)"]),
                  textAlign: "center",
                }}
              >
                <div style={{ fontWeight: "bold", textTransform: "capitalize" }}>
                  {lang}
                </div>

                {data.error ? (
                  <div style={{ fontSize: 12, color: "#666" }}>Error</div>
                ) : (
                  <>
                    <div style={{ fontSize: 20, fontWeight: "bold" }}>
                      {data["WER (%)"]}%
                    </div>
                    <div style={{ fontSize: 12 }}>WER</div>
                  </>
                )}
              </div>
            ))}
          </div>

          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ backgroundColor: "#f8fafc" }}>
                <th style={thStyle}>Language</th>
                <th style={thStyle}>Translation</th>
                <th style={thStyle}>ASR Output</th>
                <th style={thCenterStyle}>WER %</th>
                <th style={thCenterStyle}>CER %</th>
              </tr>
            </thead>

            <tbody>
              {Object.entries(results).map(([lang, data]) => (
                <tr key={lang}>
                  <td
                    style={{
                      ...tdStyle,
                      textTransform: "capitalize",
                      fontWeight: "bold",
                    }}
                  >
                    {lang}
                  </td>
                  <td style={tdStyle}>{data.error ? "—" : data.translation}</td>
                  <td style={tdStyle}>
                    {data.error ? data.error : data.hypothesis}
                  </td>
                  <td
                    style={{
                      ...tdCenterStyle,
                      backgroundColor: data.error
                        ? ""
                        : getColor(data["WER (%)"]),
                    }}
                  >
                    {data.error ? "—" : `${data["WER (%)"]}%`}
                  </td>
                  <td style={tdCenterStyle}>
                    {data.error ? "—" : `${data["CER (%)"]}%`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {meta && (
            <>
              <h2 style={{ marginTop: 35 }}>WER Heatmap</h2>
              <img
                src={`http://localhost:8000${meta.wer_heatmap}?t=${Date.now()}`}
                alt="WER Heatmap"
                style={imageStyle}
              />

              <h2 style={{ marginTop: 35 }}>CER Heatmap</h2>
              <img
                src={`http://localhost:8000${meta.cer_heatmap}?t=${Date.now()}`}
                alt="CER Heatmap"
                style={imageStyle}
              />
            </>
          )}
        </>
      )}
    </div>
  );
}

const pageStyle = {
  maxWidth: 1000,
  margin: "40px auto",
  fontFamily: "sans-serif",
  padding: "0 20px",
};

const tabContainerStyle = {
  display: "flex",
  justifyContent: "center",
  gap: 10,
  marginBottom: 25,
};

const activeTabStyle = {
  padding: "10px 20px",
  borderRadius: 8,
  border: "none",
  cursor: "pointer",
  backgroundColor: "#6366f1",
  color: "white",
  fontWeight: "bold",
};

const inactiveTabStyle = {
  padding: "10px 20px",
  borderRadius: 8,
  border: "none",
  cursor: "pointer",
  backgroundColor: "#e2e8f0",
  color: "black",
  fontWeight: "bold",
};

const inputStyle = {
  flex: 1,
  padding: "12px 16px",
  fontSize: 16,
  border: "2px solid #e2e8f0",
  borderRadius: 8,
  outline: "none",
};

const primaryButtonStyle = {
  padding: "12px 24px",
  fontSize: 16,
  backgroundColor: "#6366f1",
  color: "white",
  border: "none",
  borderRadius: 8,
  cursor: "pointer",
};

const voiceCardStyle = {
  padding: 24,
  border: "1px solid #e2e8f0",
  borderRadius: 12,
  backgroundColor: "#f8fafc",
  textAlign: "center",
  marginBottom: 25,
};

const selectStyle = {
  marginTop: 10,
  padding: 10,
  fontSize: 16,
  borderRadius: 8,
  border: "1px solid #cbd5e1",
};

const referenceBoxStyle = {
  marginTop: 30,
  padding: 20,
  border: "1px solid #ddd",
  borderRadius: 10,
  backgroundColor: "white",
};

const referenceSentenceStyle = {
  fontSize: 24,
  fontWeight: "bold",
  lineHeight: 1.6,
};

const recordButtonStyle = {
  padding: "12px 24px",
  fontSize: 16,
  backgroundColor: "#10b981",
  color: "white",
  border: "none",
  borderRadius: 8,
  cursor: "pointer",
};

const stopButtonStyle = {
  padding: "12px 24px",
  fontSize: 16,
  backgroundColor: "#ef4444",
  color: "white",
  border: "none",
  borderRadius: 8,
  cursor: "pointer",
};

const voiceResultStyle = {
  marginTop: 25,
  padding: 20,
  backgroundColor: "white",
  borderRadius: 10,
  border: "1px solid #e2e8f0",
};

const resultCardsStyle = {
  display: "flex",
  gap: 8,
  marginBottom: 30,
  flexWrap: "wrap",
};

const thStyle = {
  padding: 12,
  textAlign: "left",
  border: "1px solid #e2e8f0",
};

const thCenterStyle = {
  ...thStyle,
  textAlign: "center",
};

const tdStyle = {
  padding: 12,
  border: "1px solid #e2e8f0",
};

const tdCenterStyle = {
  ...tdStyle,
  textAlign: "center",
};

const imageStyle = {
  width: "100%",
  borderRadius: 12,
  border: "1px solid #e2e8f0",
};

export default App;