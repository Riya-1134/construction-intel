import { useState } from "react";
import { api, list, num } from "../api";
import { Badge, Bullets, ErrorBox, MetaNote, Page, SubmitButton } from "../components/ui";
import { useRequest } from "../hooks";

const initial = { project_stage: "Superstructure", planned_activities: "", workforce: "", site_conditions: "", weather: "", date: new Date().toISOString().slice(0, 10) };

export default function DailyPage() {
  const [form, setForm] = useState(initial);
  const { loading, error, data, run } = useRequest(api.daily);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  return (
    <Page title="Daily Site Assistant"
          intro="Turn today's high-level inputs into a prioritised task list with crews, materials, equipment, safety checks and risk alerts.">
      <div className="grid">
        <form className="card" onSubmit={(e) => { e.preventDefault(); run(form); }}>
          <h2>Today's inputs</h2>
          <div className="row">
            <div>
              <label>Project stage</label>
              <select value={form.project_stage} onChange={set("project_stage")}>
                {["Site preparation", "Foundation", "Plinth", "Superstructure", "Masonry", "MEP rough-in", "Plastering", "Finishing", "Handover"].map((o) => <option key={o}>{o}</option>)}
              </select>
            </div>
            <div><label>Date</label><input type="date" value={form.date} onChange={set("date")} /></div>
          </div>
          <label>Planned activities</label>
          <textarea value={form.planned_activities} onChange={set("planned_activities")} required
                    placeholder="Slab casting for 2nd floor (120 m3), brickwork on ground floor east wing, plumbing conduits in toilets..." />
          <label>Workforce available</label>
          <input value={form.workforce} onChange={set("workforce")} placeholder="20 masons, 12 helpers, 4 bar benders, 1 crane operator" />
          <label>Site conditions</label>
          <input value={form.site_conditions} onChange={set("site_conditions")} placeholder="Dry, access road clear, tower crane operational" />
          <label>Weather</label>
          <input value={form.weather} onChange={set("weather")} placeholder="Sunny, 36 C, light wind" />
          <SubmitButton loading={loading}>Generate daily plan</SubmitButton>
        </form>

        <div>
          <ErrorBox error={error} />
          {!data && !error && <div className="card empty">Your daily action plan will appear here.</div>}
          {data && (
            <div className="card">
              <h2>Daily action plan</h2>
              <p>{data.day_summary || "No summary provided."}</p>
              {list(data.risk_alerts).map((r, i) => <div className="alert warn" key={i}>{r}</div>)}
              <h3>Tasks</h3>
              {list(data.tasks).length === 0 ? <p className="empty">No tasks listed.</p> : (
                <table>
                  <thead><tr><th>#</th><th>Task</th><th>Priority</th><th>Crew</th><th className="num">Hours</th></tr></thead>
                  <tbody>
                    {data.tasks.map((t, i) => (
                      <tr key={i}><td>{i + 1}</td><td>{t.task}</td><td><Badge value={t.priority} /></td><td>{t.crew || "-"}</td><td className="num">{num(t.duration_hours)}</td></tr>
                    ))}
                  </tbody>
                </table>
              )}
              <div className="two-col" style={{ marginTop: "1rem" }}>
                <Bullets title="Materials required" items={data.materials_required} />
                <Bullets title="Equipment required" items={data.equipment_required} />
                <Bullets title="Safety checks" items={data.safety_checks} />
                <Bullets title="End-of-day checklist" items={data.end_of_day_checklist} />
              </div>
              <MetaNote meta={data.meta} />
            </div>
          )}
        </div>
      </div>
    </Page>
  );
}
