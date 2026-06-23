import { useState } from "react";

function App() {
  const [sentence, setSentence] = useState("");
  const [results, setResults] = useState(null);
  const [meta, setMeta] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

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
    <div style={{ maxWidth: 1000, margin: "40px auto", fontFamily: "sans-serif", padding: "0 20px" }}>
      <h1 style={{ textAlign: "center" }}>🎤 Cross-Language ASR Evaluator</h1>

      <p style={{ textAlign: "center", color: "#666" }}>
        Type a sentence — it will be translated and evaluated across 9 Indic languages.
      </p>

      <div style={{ display: "flex", gap: 10, marginBottom: 20 }}>
        <input
          value={sentence}
          onChange={(e) => setSentence(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && evaluate()}
          placeholder="Type a sentence in any language..."
          style={{
            flex: 1,
            padding: "12px 16px",
            fontSize: 16,
            border: "2px solid #e2e8f0",
            borderRadius: 8,
            outline: "none",
          }}
        />

        <button
          onClick={evaluate}
          disabled={loading}
          style={{
            padding: "12px 24px",
            fontSize: 16,
            backgroundColor: "#6366f1",
            color: "white",
            border: "none",
            borderRadius: 8,
            cursor: "pointer",
          }}
        >
          {loading ? "Evaluating..." : "Evaluate"}
        </button>
      </div>

      {error && <p style={{ color: "red", textAlign: "center" }}>{error}</p>}

      {loading && (
        <p style={{ textAlign: "center", color: "#666" }}>
          Detecting language, translating, generating audio and running ASR evaluation...
        </p>
      )}

      {meta && (
        <p style={{ textAlign: "center", color: "#555" }}>
          Detected language: <b>{meta.detected_language}</b> | Mode: <b>{meta.mode}</b>
        </p>
      )}

      {results && (
        <>
          <h2>Results</h2>

          <div style={{ display: "flex", gap: 8, marginBottom: 30, flexWrap: "wrap" }}>
            {Object.entries(results).map(([lang, data]) => (
              <div
                key={lang}
                style={{
                  flex: 1,
                  minWidth: 100,
                  padding: 12,
                  borderRadius: 8,
                  backgroundColor: data.error ? "#e2e8f0" : getColor(data["WER (%)"]),
                  textAlign: "center",
                }}
              >
                <div style={{ fontWeight: "bold", textTransform: "capitalize" }}>{lang}</div>

                {data.error ? (
                  <div style={{ fontSize: 12, color: "#666" }}>Error</div>
                ) : (
                  <>
                    <div style={{ fontSize: 20, fontWeight: "bold" }}>{data["WER (%)"]}%</div>
                    <div style={{ fontSize: 12 }}>WER</div>
                  </>
                )}
              </div>
            ))}
          </div>

          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ backgroundColor: "#f8fafc" }}>
                <th style={{ padding: 12, textAlign: "left", border: "1px solid #e2e8f0" }}>Language</th>
                <th style={{ padding: 12, textAlign: "left", border: "1px solid #e2e8f0" }}>Translation</th>
                <th style={{ padding: 12, textAlign: "left", border: "1px solid #e2e8f0" }}>ASR Output</th>
                <th style={{ padding: 12, textAlign: "center", border: "1px solid #e2e8f0" }}>WER %</th>
                <th style={{ padding: 12, textAlign: "center", border: "1px solid #e2e8f0" }}>CER %</th>
              </tr>
            </thead>

            <tbody>
              {Object.entries(results).map(([lang, data]) => (
                <tr key={lang}>
                  <td style={{ padding: 12, border: "1px solid #e2e8f0", textTransform: "capitalize", fontWeight: "bold" }}>
                    {lang}
                  </td>
                  <td style={{ padding: 12, border: "1px solid #e2e8f0" }}>
                    {data.error ? "—" : data.translation}
                  </td>
                  <td style={{ padding: 12, border: "1px solid #e2e8f0" }}>
                    {data.error ? data.error : data.hypothesis}
                  </td>
                  <td
                    style={{
                      padding: 12,
                      border: "1px solid #e2e8f0",
                      textAlign: "center",
                      backgroundColor: data.error ? "" : getColor(data["WER (%)"]),
                    }}
                  >
                    {data.error ? "—" : `${data["WER (%)"]}%`}
                  </td>
                  <td style={{ padding: 12, border: "1px solid #e2e8f0", textAlign: "center" }}>
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
                style={{ width: "100%", borderRadius: 12, border: "1px solid #e2e8f0" }}
              />

              <h2 style={{ marginTop: 35 }}>CER Heatmap</h2>
              <img
                src={`http://localhost:8000${meta.cer_heatmap}?t=${Date.now()}`}
                alt="CER Heatmap"
                style={{ width: "100%", borderRadius: 12, border: "1px solid #e2e8f0" }}
              />
            </>
          )}
        </>
      )}
    </div>
  );
}

export default App;