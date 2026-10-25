import { useState } from "react";
import { api, compactInr, inr, list, num } from "../api";
import { Bullets, ErrorBox, Kpi, MetaNote, Page, SubmitButton } from "../components/ui";
import { useRequest } from "../hooks";

const initial = { plot_length_ft: 30, plot_width_ft: 40, floors: 2, construction_type: "residential", quality: "standard", city: "Pune", additional_requirements: "" };

function Gantt({ schedule }) {
  const rows = list(schedule);
  if (!rows.length) return <p className="empty">No schedule provided.</p>;
  const total = Math.max(...rows.map((r) => num(r.start_week) + num(r.duration_weeks) - 1), 1);
  return (
    <div className="gantt">
      {rows.map((r, i) => {
        const left = ((num(r.start_week) - 1) / total) * 100;
        const width = Math.max(2, (num(r.duration_weeks) / total) * 100);
        return (
          <div className="gantt-row" key={i} title={list(r.tasks).join(", ")}>
            <span>{r.phase || `Phase ${i + 1}`} <small style={{ color: "var(--muted)" }}>(wk {num(r.start_week)}, {num(r.duration_weeks)} wk)</small></span>
            <div className="gantt-track"><div className="gantt-bar" style={{ left: `${left}%`, width: `${width}%` }} /></div>
          </div>
        );
      })}
    </div>
  );
}

export default function PlannerPage() {
  const [form, setForm] = useState(initial);
  const { loading, error, data, run } = useRequest(api.planner);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = (e) => {
    e.preventDefault();
    run({
      ...form,
      plot_length_ft: Number(form.plot_length_ft),
      plot_width_ft: Number(form.plot_width_ft),
      floors: Number(form.floors),
      additional_requirements: form.additional_requirements || null,
    });
  };

  return (
    <Page title="Construction Project Planner"
          intro="Enter plot size, floors, type, quality grade and city. Get a consolidated plan: material estimates, INR cost breakdown, phase-wise schedule and a conceptual visualization.">
      <div className="grid">
        <form className="card" onSubmit={submit}>
          <h2>Project inputs</h2>
          <div className="row">
            <div><label>Plot length (ft)</label><input type="number" min="1" step="any" value={form.plot_length_ft} onChange={set("plot_length_ft")} required /></div>
            <div><label>Plot width (ft)</label><input type="number" min="1" step="any" value={form.plot_width_ft} onChange={set("plot_width_ft")} required /></div>
          </div>
          <div className="row">
            <div><label>Floors</label><input type="number" min="1" max="50" value={form.floors} onChange={set("floors")} required /></div>
            <div>
              <label>Quality</label>
              <select value={form.quality} onChange={set("quality")}>
                <option value="basic">Basic</option><option value="standard">Standard</option><option value="premium">Premium</option>
              </select>
            </div>
          </div>
          <label>Construction type</label>
          <select value={form.construction_type} onChange={set("construction_type")}>
            {["residential", "duplex villa", "apartment block", "commercial", "warehouse / industrial shed", "mixed-use"].map((o) => <option key={o}>{o}</option>)}
          </select>
          <label>City</label>
          <input value={form.city} onChange={set("city")} placeholder="e.g. Pune" required />
          <label>Additional requirements (optional)</label>
          <textarea value={form.additional_requirements} onChange={set("additional_requirements")} placeholder="Basement parking, rooftop solar, vastu-compliant entrance..." />
          <SubmitButton loading={loading}>Generate plan</SubmitButton>
        </form>

        <div className="stack">
          <ErrorBox error={error} />
          {!data && !error && <div className="card empty">Your project plan will appear here.</div>}
          {data && (
            <>
              <div className="card">
                <h2>Plan summary</h2>
                <p>{data.project_summary || "No summary provided."}</p>
                <div className="kpis">
                  <Kpi label="Built-up area" value={`${num(data.built_up_area_sqft).toLocaleString("en-IN")} sq ft`} />
                  <Kpi label="Estimated cost" value={compactInr(data.total_estimated_cost_inr)} />
                  <Kpi label="Cost / sq ft" value={inr(data.cost_per_sqft_inr)} />
                  <Kpi label="Duration" value={`${num(data.duration_weeks)} weeks`} />
                </div>
                <Bullets title="Assumptions" items={data.assumptions} />
              </div>

              <div className="card">
                <h2>Material estimate</h2>
                {list(data.materials).length === 0 ? <p className="empty">No materials listed.</p> : (
                  <table>
                    <thead><tr><th>Material</th><th className="num">Quantity</th><th>Unit</th><th className="num">Cost (INR)</th></tr></thead>
                    <tbody>
                      {data.materials.map((m, i) => (
                        <tr key={i}><td>{m.material}</td><td className="num">{num(m.quantity).toLocaleString("en-IN")}</td><td>{m.unit}</td><td className="num">{inr(m.estimated_cost_inr)}</td></tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>

              <div className="card">
                <h2>Cost breakdown</h2>
                {list(data.cost_breakdown).length === 0 ? <p className="empty">No breakdown listed.</p> : (
                  <table>
                    <thead><tr><th>Category</th><th className="num">Amount</th><th className="num">Share</th></tr></thead>
                    <tbody>
                      {data.cost_breakdown.map((c, i) => (
                        <tr key={i}><td>{c.category}</td><td className="num">{inr(c.amount_inr)}</td><td className="num">{num(c.percentage)}%</td></tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>

              <div className="card">
                <h2>Schedule</h2>
                <Gantt schedule={data.schedule} />
                <div style={{ marginTop: "0.75rem" }}>
                  {list(data.schedule).map((p, i) => (
                    <details key={i}><summary>{p.phase}</summary><Bullets items={p.tasks} /></details>
                  ))}
                </div>
              </div>

              <div className="card">
                <h2>Architectural visualization</h2>
                <p>{data.visualization?.concept_description || "No concept description."}</p>
                {data.visualization?.style && <p><strong>Style:</strong> {data.visualization.style}</p>}
                {data.visualization?.svg && (
                  <div className="svg-wrap">
                    {/* Rendered as an <img> so the markup is inert (no scripts/handlers can run). */}
                    <img alt="Conceptual elevation and plot footprint sketch"
                         src={`data:image/svg+xml;charset=utf-8,${encodeURIComponent(data.visualization.svg)}`} />
                  </div>
                )}
                <Bullets title="Floor plan notes" items={data.visualization?.floor_plan_notes} />
                <MetaNote meta={data.meta} />
              </div>
            </>
          )}
        </div>
      </div>
    </Page>
  );
}
