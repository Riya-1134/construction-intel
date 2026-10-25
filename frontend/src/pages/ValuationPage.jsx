import { useState } from "react";
import { api, compactInr, inr, num } from "../api";
import { Badge, Bullets, ErrorBox, Kpi, MetaNote, Meter, Page, SubmitButton } from "../components/ui";
import { useRequest } from "../hooks";

const initial = { city: "Bengaluru", locality: "", property_type: "apartment", area_sqft: 1200, bedrooms: 2, building_age_years: 5, floor_number: "", furnishing: "semi-furnished", amenities: "", nearby_landmarks: "" };

export default function ValuationPage() {
  const [form, setForm] = useState(initial);
  const { loading, error, data, run } = useRequest(api.valuation);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = (e) => {
    e.preventDefault();
    run({
      city: form.city,
      locality: form.locality || null,
      property_type: form.property_type,
      area_sqft: Number(form.area_sqft),
      bedrooms: form.bedrooms === "" ? null : Number(form.bedrooms),
      building_age_years: Number(form.building_age_years) || 0,
      floor_number: form.floor_number === "" ? null : Number(form.floor_number),
      furnishing: form.furnishing || null,
      amenities: form.amenities.split(",").map((s) => s.trim()).filter(Boolean),
      nearby_landmarks: form.nearby_landmarks || null,
    });
  };

  return (
    <Page title="Real Estate Valuation"
          intro="Indicative Indian-market valuation: value range, price per sq ft, rental potential, yield and appreciation outlook. Not a registered valuation.">
      <div className="grid">
        <form className="card" onSubmit={submit}>
          <h2>Property details</h2>
          <div className="row">
            <div><label>City</label><input value={form.city} onChange={set("city")} required /></div>
            <div><label>Locality</label><input value={form.locality} onChange={set("locality")} placeholder="e.g. Whitefield" /></div>
          </div>
          <div className="row">
            <div>
              <label>Property type</label>
              <select value={form.property_type} onChange={set("property_type")}>
                {["apartment", "independent house", "villa", "plot", "commercial office", "retail shop"].map((o) => <option key={o}>{o}</option>)}
              </select>
            </div>
            <div><label>Area (sq ft)</label><input type="number" min="1" step="any" value={form.area_sqft} onChange={set("area_sqft")} required /></div>
          </div>
          <div className="row">
            <div><label>Bedrooms</label><input type="number" min="0" value={form.bedrooms} onChange={set("bedrooms")} /></div>
            <div><label>Building age (years)</label><input type="number" min="0" value={form.building_age_years} onChange={set("building_age_years")} /></div>
          </div>
          <div className="row">
            <div><label>Floor number</label><input type="number" value={form.floor_number} onChange={set("floor_number")} placeholder="optional" /></div>
            <div>
              <label>Furnishing</label>
              <select value={form.furnishing} onChange={set("furnishing")}>
                <option value="">Not specified</option><option>unfurnished</option><option>semi-furnished</option><option>fully furnished</option>
              </select>
            </div>
          </div>
          <label>Amenities (comma separated)</label>
          <input value={form.amenities} onChange={set("amenities")} placeholder="gym, swimming pool, covered parking" />
          <label>Nearby landmarks</label>
          <textarea value={form.nearby_landmarks} onChange={set("nearby_landmarks")} placeholder="2 km from metro station, IT park nearby..." />
          <SubmitButton loading={loading}>Estimate value</SubmitButton>
        </form>

        <div>
          <ErrorBox error={error} />
          {!data && !error && <div className="card empty">Valuation will appear here.</div>}
          {data && (
            <div className="card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "1rem" }}>
                <h2>Valuation report</h2>
                <Badge value={data.investment_outlook} />
              </div>
              <p>{data.summary || "No summary provided."}</p>
              <div className="kpis">
                <Kpi label="Estimated value" value={compactInr(data.estimated_value_inr)} />
                <Kpi label="Range" value={`${compactInr(data.estimated_value_min_inr)} – ${compactInr(data.estimated_value_max_inr)}`} />
                <Kpi label="Price / sq ft" value={inr(data.price_per_sqft_inr)} />
                <Kpi label="Monthly rent" value={`${inr(data.monthly_rent_min_inr)} – ${inr(data.monthly_rent_max_inr)}`} />
                <Kpi label="Rental yield" value={`${num(data.rental_yield_percent)}%`} />
                <Kpi label="Appreciation / yr" value={`${num(data.expected_annual_appreciation_percent)}%`} />
                <Kpi label="5-year ROI" value={`${num(data.five_year_roi_percent)}%`} />
              </div>
              <h3>Confidence {num(data.confidence)}%</h3>
              <Meter value={data.confidence} />
              <div className="two-col">
                <Bullets title="Value drivers" items={data.value_drivers} />
                <Bullets title="Risk factors" items={data.risk_factors} />
              </div>
              <MetaNote meta={data.meta} />
            </div>
          )}
        </div>
      </div>
    </Page>
  );
}
