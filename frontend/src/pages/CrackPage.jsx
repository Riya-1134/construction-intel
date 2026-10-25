import { useState } from "react";
import { api, num } from "../api";
import { Badge, Bullets, ErrorBox, ImageDrop, Kpi, MetaNote, Meter, Page, SubmitButton } from "../components/ui";
import { useRequest } from "../hooks";

export default function CrackPage() {
  const [file, setFile] = useState(null);
  const [description, setDescription] = useState("");
  const [element, setElement] = useState("");
  const [age, setAge] = useState("");
  const { loading, error, data, run } = useRequest(api.crack);

  const submit = (e) => {
    e.preventDefault();
    run({ image: file, description, element, building_age_years: age });
  };

  return (
    <Page title="Crack Detection & Analysis"
          intro="Upload a photo of a crack. The AI classifies type, orientation and severity, suggests probable causes, and recommends repair and prevention.">
      <div className="grid">
        <form className="card" onSubmit={submit}>
          <h2>Input</h2>
          <label>Crack image</label>
          <ImageDrop file={file} onChange={setFile} />
          <div className="row">
            <div>
              <label>Structural element</label>
              <select value={element} onChange={(e) => setElement(e.target.value)}>
                <option value="">Not specified</option>
                {["wall (masonry)", "RCC beam", "RCC column", "slab", "foundation / plinth", "plaster surface", "floor"].map((o) => (
                  <option key={o} value={o}>{o}</option>
                ))}
              </select>
            </div>
            <div>
              <label>Building age (years)</label>
              <input type="number" min="0" max="300" value={age} onChange={(e) => setAge(e.target.value)} placeholder="e.g. 12" />
            </div>
          </div>
          <label>Description (optional)</label>
          <textarea value={description} onChange={(e) => setDescription(e.target.value)}
                    placeholder="Diagonal crack above window, widening over 2 months, damp patch nearby..." />
          <SubmitButton loading={loading}>Analyse crack</SubmitButton>
        </form>

        <div>
          <ErrorBox error={error} />
          {!data && !error && <div className="card empty">Results will appear here.</div>}
          {data && (
            <div className="card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "1rem" }}>
                <h2>Crack assessment</h2>
                <Badge value={data.severity} />
              </div>
              {!data.crack_detected && <div className="alert warn">No clear crack was detected in the input. Results below are provisional.</div>}
              {data.structural_concern && <div className="alert">Possible structural concern. Priority: {data.inspection_priority}.</div>}
              <div className="kpis">
                <Kpi label="Crack type" value={data.crack_type || "unknown"} />
                <Kpi label="Orientation" value={data.orientation || "unknown"} />
                <Kpi label="Est. width" value={`${num(data.estimated_width_mm)} mm`} />
                <Kpi label="Priority" value={data.inspection_priority || "n/a"} />
              </div>
              <h3>Confidence {num(data.confidence)}%</h3>
              <Meter value={data.confidence} />
              <div className="two-col">
                <Bullets title="Probable causes" items={data.probable_causes} />
                <Bullets title="Potential risks" items={data.potential_risks} />
                <Bullets title="Repair methods" items={data.repair_methods} />
                <Bullets title="Preventive measures" items={data.preventive_measures} />
              </div>
              <MetaNote meta={data.meta} />
            </div>
          )}
        </div>
      </div>
    </Page>
  );
}
