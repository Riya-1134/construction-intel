import { Component, useEffect, useState } from "react";
import { api } from "./api";
import SafetyPage from "./pages/SafetyPage";
import CrackPage from "./pages/CrackPage";
import PlannerPage from "./pages/PlannerPage";
import ValuationPage from "./pages/ValuationPage";
import ChatPage from "./pages/ChatPage";
import DailyPage from "./pages/DailyPage";
import WeatherPage from "./pages/WeatherPage";

const FEATURES = [
  { id: "safety", label: "Site Safety", icon: "🦺", component: SafetyPage },
  { id: "crack", label: "Crack Analysis", icon: "🧱", component: CrackPage },
  { id: "planner", label: "Project Planner", icon: "📐", component: PlannerPage },
  { id: "valuation", label: "Valuation", icon: "🏠", component: ValuationPage },
  { id: "daily", label: "Daily Assistant", icon: "📋", component: DailyPage },
  { id: "weather", label: "Weather Advisory", icon: "⛅", component: WeatherPage },
  { id: "chat", label: "Knowledge Chat", icon: "💬", component: ChatPage },
];

class ErrorBoundary extends Component {
  constructor(props) { super(props); this.state = { error: null }; }
  static getDerivedStateFromError(error) { return { error }; }
  componentDidCatch(error, info) { console.error("UI error", error, info); }
  render() {
    if (this.state.error) {
      return (
        <div className="card">
          <div className="alert"><strong>This view hit an unexpected error.</strong> {String(this.state.error?.message || "")}</div>
          <button className="btn ghost" onClick={() => this.setState({ error: null })}>Try again</button>
        </div>
      );
    }
    return this.props.children;
  }
}

function readHash() {
  const id = window.location.hash.replace("#", "");
  return FEATURES.some((f) => f.id === id) ? id : FEATURES[0].id;
}

export default function App() {
  const [active, setActive] = useState(readHash);
  const [health, setHealth] = useState({ state: "checking" });

  useEffect(() => {
    const onHash = () => setActive(readHash());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  useEffect(() => {
    let cancelled = false;
    const check = () => api.health()
      .then((h) => !cancelled && setHealth({ state: "up", ...h }))
      .catch(() => !cancelled && setHealth({ state: "down" }));
    check();
    const t = setInterval(check, 30000);
    return () => { cancelled = true; clearInterval(t); };
  }, []);

  const feature = FEATURES.find((f) => f.id === active) || FEATURES[0];
  const View = feature.component;

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <strong>Construction Intelligence</strong>
          <span>Multimodal AI decision support</span>
        </div>
        {FEATURES.map((f) => (
          <button key={f.id} className={`nav-btn ${f.id === active ? "active" : ""}`}
                  onClick={() => { window.location.hash = f.id; setActive(f.id); }}>
            <span className="icon" aria-hidden="true">{f.icon}</span>{f.label}
          </button>
        ))}
        <div className="status-pill">
          <span className={`dot ${health.state === "up" ? (health.ai_enabled ? "ok" : "") : health.state === "down" ? "bad" : ""}`} />
          {health.state === "checking" && "Checking backend..."}
          {health.state === "down" && <>Backend <b>offline</b>. Start the FastAPI server.</>}
          {health.state === "up" && (health.ai_enabled
            ? <>Backend online · <b>AI live</b></>
            : <>Backend online · <b>demo mode</b> (no GROQ_API_KEY)</>)}
        </div>
      </aside>
      <main className="main">
        <ErrorBoundary key={active}>
          <View />
        </ErrorBoundary>
      </main>
    </div>
  );
}
