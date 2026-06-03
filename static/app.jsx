const { useState } = React;

function App() {
  const [prompt, setPrompt] = useState("");
  const [response, setResponse] = useState("");
  const [status, setStatus] = useState("");

  async function handleAsk() {
    const p = prompt.trim();
    if (!p) {
      setStatus("Please enter a prompt.");
      return;
    }
    setStatus("Thinking...");
    setResponse("");
    try {
      const res = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: p })
      });
      const data = await res.json();
      if (res.ok) {
        setResponse(data.response || JSON.stringify(data));
        setStatus("");
      } else {
        setResponse(data.error || JSON.stringify(data));
        setStatus('Error');
      }
    } catch (err) {
      setResponse(String(err));
      setStatus('Network error');
    }
  }

  return (
    <div className="ai-box">
      <h2>Ask MoneyBuddy</h2>
      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Type a question for the AI..."
        rows={5}
      />

      <div className="controls">
        <button onClick={handleAsk}>Ask</button>
        <span className="status">{status}</span>
      </div>

      <div className="response" aria-live="polite">{response}</div>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(React.createElement(App));
