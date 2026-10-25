import { useState } from "react";
import { api, list, num } from "../api";
import { Badge, Bullets, ErrorBox, ImageDrop, Kpi, MetaNote, Meter, Page, SubmitButton } from "../components/ui";
import { useRequest } from "../hooks";

export default function SafetyPage() {
  const [file, setFile] = useState(null);
  const [description, setDescription] = useState("");
  const [siteType, setSiteType] = useState("");
  const { loading, error, data, run } = useRequest(api.safety);

  const submit = (e) => {
    e.preventDefault();
    run({ image: file, description, site_type: siteType });
  };

  return (
    <Page title="Site Safety Monitoring"
          intro="Upload a construction site photo (and optionally describe the scene). The AI identifies hazards, PPE gaps, risk level and corrective actions.">
      <div className="grid">
        <form className="card" onSubmit={submit}>
          <h2>Input</h2>
          <label>Site image</label>
          <ImageDrop file={file} onChange={setFile} />
          <label>Work / site type (optional)</label>
          <input value={siteType} onChange={(e) => setSiteType(e.target.value)} placeholder="e.g. RCC slab casting, excavation" />
          <label>Description (optional)</label>
          <textarea value={description} onChange={(e) => setDescription(e.target.value)}
                    placeholder="Workers on 3rd-floor slab edge, scaffolding on east side..." />
          <p className="hint">Provide an image, a description, or both.</p>
          <SubmitButton loading={loading}>Analyse safety</SubmitButton>
        </form>

        <div>
          <ErrorBox error={error} />
          {!data && !error && <div className="card empty">Results will appear here.</div>}
          {data && (
            <div className="card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "1rem" }}>
                <h2>Safety report</h2>
                <Badge value={data.risk_level} />
              </div>
              <p>{data.summary || "No summary provided."}</p>
              <div className="kpis">
                <Kpi label="Risk score" value={`${num(data.risk_score)} / 100`} />
                <Kpi label="Hazards found" value={list(data.hazards).length} />
                <Kpi label="Image quality" value={data.image_quality || "unknown"} />
              </div>
              <Meter value={data.risk_score} />
              <div className="two-col">
                <Bullets title="Identified hazards" items={data.hazards} />
                <Bullets title="Corrective actions" items={data.corrective_actions} />
                <Bullets title="PPE observed" items={data.ppe_observed} emptyText="None confirmed." />
                <Bullets title="PPE missing" items={data.ppe_missing} emptyText="No gaps identified." />
                <Bullets title="Recommended PPE" items={data.recommended_ppe} />
                <Bullets title="Safety guidelines" items={data.safety_guidelines} />
              </div>
              <MetaNote meta={data.meta} />
            </div>
          )}
        </div>
      </div>
    </Page>
  );
}
