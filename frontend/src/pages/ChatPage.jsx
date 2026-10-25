import { useEffect, useRef, useState } from "react";
import { api, list } from "../api";
import { ErrorBox, Page } from "../components/ui";

const starters = [
  "What concrete grade should I use for a residential slab?",
  "How long must I cure an RCC slab before removing props?",
  "Checklist before a roof slab concrete pour",
  "Difference between M-sand and river sand for plastering",
];

export default function ChatPage() {
  const [messages, setMessages] = useState([
    { role: "assistant", content: "Hi, I am your construction knowledge assistant. Ask about materials, IS codes, site procedures, safety or planning." },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const logRef = useRef(null);

  useEffect(() => { logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: "smooth" }); }, [messages, loading]);

  const send = async (text) => {
    const message = (text ?? input).trim();
    if (!message || loading) return;
    setInput("");
    setError(null);
    const history = messages.filter((m) => !m.isIntro).slice(-10).map((m) => ({ role: m.role, content: m.content }));
    setMessages((m) => [...m, { role: "user", content: message }]);
    setLoading(true);
    try {
      const res = await api.chat({ message, history });
      setMessages((m) => [...m, {
        role: "assistant",
        content: res.answer || "I could not produce an answer. Please rephrase.",
        key_points: list(res.key_points),
        references: list(res.references),
        follow_up_questions: list(res.follow_up_questions),
        disclaimer: res.disclaimer,
      }]);
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Page title="Construction Knowledge Assistant"
          intro="Concise, technical answers with key points and relevant Indian standards. Assistive only; verify with a qualified engineer.">
      <div className="card chat">
        <div className="chat-log" ref={logRef}>
          {messages.map((m, i) => (
            <div key={i} className={`msg ${m.role}`}>
              {m.content}
              {m.role === "assistant" && (list(m.key_points).length > 0 || list(m.references).length > 0) && (
                <div className="extras">
                  {list(m.key_points).length > 0 && <><strong>Key points</strong><ul>{m.key_points.map((k, j) => <li key={j}>{k}</li>)}</ul></>}
                  {list(m.references).length > 0 && <div><strong>References:</strong> {m.references.join(" · ")}</div>}
                  {m.disclaimer && <div style={{ marginTop: "0.3rem", fontStyle: "italic" }}>{m.disclaimer}</div>}
                </div>
              )}
              {m.role === "assistant" && list(m.follow_up_questions).length > 0 && (
                <div className="chips">
                  {m.follow_up_questions.map((q, j) => <button key={j} type="button" className="chip" onClick={() => send(q)}>{q}</button>)}
                </div>
              )}
            </div>
          ))}
          {loading && <div className="msg assistant">Thinking...</div>}
        </div>
        <ErrorBox error={error} />
        {messages.length === 1 && (
          <div className="chips">{starters.map((s) => <button key={s} type="button" className="chip" onClick={() => send(s)}>{s}</button>)}</div>
        )}
        <form className="chat-input" onSubmit={(e) => { e.preventDefault(); send(); }}>
          <textarea value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask a construction question..." maxLength={4000}
                    onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }} />
          <button className="btn" type="submit" disabled={loading || !input.trim()}>Send</button>
        </form>
      </div>
    </Page>
  );
}
