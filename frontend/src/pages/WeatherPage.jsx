import { useState } from "react";
import { api, num } from "../api";
import { Badge, Bullets, ErrorBox, MetaNote, Meter, Page, SubmitButton } from "../components/ui";
import { useRequest } from "../hooks";

const initial = { planned_activities: "", weather_conditions: "", temperature_c: "", wind_speed_kmph: "", rain_probability_percent: "", location: "" };

export default function WeatherPage() {
  const [form, setForm] = useState(initial);
  const { loading, error, data, run } = useRequest(api.weather);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  const optNum = (v) => (v === "" ? null : Number(v));

  const submit = (e) => {
    e.preventDefault();
    run({
      planned_activities: form.planned_activities,
      weather_conditions: form.weather_conditions,
      temperature_c: optNum(form.temperature_c),
      wind_speed_kmph: optNum(form.wind_speed_kmph),
      rain_probability_percent: optNum(form.rain_probability_percent),
      location: form.location || null,
    });
  };

  return (
    <Page title="Weather-Aware Advisory"
          intro="Describe planned activities and the prevailing or forecast weather. Get a GO / CAUTION / NO-GO decision with risks, precautions and mitigation.">
      <div className="grid">
        <form className="card" onSubmit={submit}>
          <h2>Inputs</h2>
          <label>Planned activities</label>
          <textarea value={form.planned_activities} onChange={set("planned_activities")} required placeholder="Roof slab concreting, tower crane lifts, external plastering" />
          <label>Weather conditions</label>
          <textarea value={form.weather_conditions} onChange={set("weather_conditions")} required placeholder="Overcast, thunderstorm expected after 2 pm, gusty winds" />
          <div className="row">
            <div><label>Temperature (°C)</label><input type="number" step="any" value={form.temperature_c} onChange={set("temperature_c")} placeholder="34" /></div>
            <div><label>Wind (km/h)</label><input type="number" min="0" step="any" value={form.wind_speed_kmph} onChange={set("wind_speed_kmph")} placeholder="25" /></div>
          </div>
          <div className="row">
            <div><label>Rain probability (%)</label><input type="number" min="0" max="100" value={form.rain_probability_percent} onChange={set("rain_probability_percent")} placeholder="60" /></div>
            <div><label>Location</label><input value={form.location} onChange={set("location")} placeholder="Mumbai" /></div>
          </div>
          <SubmitButton loading={loading}>Get advisory</SubmitButton>
        </form>

        <div>
          <ErrorBox error={error} />
          {!data && !error && <div className="card empty">The advisory will appear here.</div>}
          {data && (
            <div className="card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "1rem" }}>
                <h2>Advisory</h2>
                <Badge value={data.decision} />
              </div>
              <p>{data.rationale || "No rationale provided."}</p>
              {data.recommended_window && <div className="alert info"><strong>Recommended window:</strong> {data.recommended_window}</div>}
              <h3>Confidence {num(data.confidence)}%</h3>
              <Meter value={data.confidence} />
              <div className="two-col">
                <Bullets title="Identified risks" items={data.identified_risks} />
                <Bullets title="Affected activities" items={data.affected_activities} emptyText="None." />
                <Bullets title="Precautions" items={data.precautions} />
                <Bullets title="Mitigation steps" items={data.mitigation_steps} />
              </div>
              <MetaNote meta={data.meta} />
            </div>
          )}
        </div>
      </div>
    </Page>
  );
}
