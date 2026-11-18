"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { type Commodity, type County, type Paginated, getJson } from "@/lib/api";

type Point = {
  month: string;
  avg_price: number;
  min_price: number;
  max_price: number;
  observations: number;
};
type Trend = {
  unit: string | null;
  price_type: string;
  available_units: string[];
  points: Point[];
};
type Volatility = {
  stats: {
    months: number;
    mean_price: number | null;
    coefficient_of_variation_pct: number | null;
    mean_abs_monthly_change_pct: number | null;
    monthly_change_std_pct: number | null;
  };
};
type Result = { key: string; trend?: Trend; volatility?: Volatility; error?: string };

const field = "rounded border bg-white px-2 py-1 text-black";
const pct = (v: number | null) => (v == null ? "–" : `${v.toFixed(1)}%`);

export default function TrendsPage() {
  const [commodities, setCommodities] = useState<Commodity[]>([]);
  const [counties, setCounties] = useState<County[]>([]);
  const [filters, setFilters] = useState({ commodity: "", county: "", priceType: "retail", unit: "" });
  const [result, setResult] = useState<Result | null>(null);

  useEffect(() => {
    getJson<Paginated<Commodity>>("/api/v1/commodities/?page_size=200")
      .then((r) => setCommodities(r.items))
      .catch(() => {});
    getJson<Paginated<County>>("/api/v1/counties/?page_size=200")
      .then((r) => setCounties(r.items))
      .catch(() => {});
  }, []);

  // Default to the first commodity in the list until the user picks one
  const commodityId = filters.commodity || (commodities[0] ? String(commodities[0].id) : "");

  const qs = useMemo(() => {
    if (!commodityId) return "";
    const p = new URLSearchParams({ commodity_id: commodityId, price_type: filters.priceType });
    if (filters.county) p.set("county_id", filters.county);
    if (filters.unit) p.set("unit", filters.unit);
    return p.toString();
  }, [commodityId, filters.county, filters.priceType, filters.unit]);

  useEffect(() => {
    if (!qs) return;
    let cancelled = false;
    Promise.all([
      getJson<Trend>(`/api/v1/prices/trends/?${qs}`),
      getJson<Volatility>(`/api/v1/prices/volatility/?${qs}`),
    ])
      .then(([trend, volatility]) => !cancelled && setResult({ key: qs, trend, volatility }))
      .catch((e) => !cancelled && setResult({ key: qs, error: String(e.message ?? e) }));
    return () => {
      cancelled = true;
    };
  }, [qs]);

  const loading = qs !== "" && result?.key !== qs;
  const trend = result?.key === qs ? result.trend : undefined;
  const stats = result?.key === qs ? result.volatility?.stats : undefined;
  const chartData = trend?.points.map((p) => ({ ...p, month: p.month.slice(0, 7) })) ?? [];

  // Changing commodity, county or price type goes back to the automatic unit
  const update = (patch: Partial<typeof filters>) =>
    setFilters((f) => ({ ...f, unit: "", ...patch }));

  return (
    <main className="mx-auto max-w-6xl p-8">
      <Link href="/" className="text-sm text-blue-600 underline">
        ← System status
      </Link>
      <h1 className="mt-2 text-2xl font-bold">Price trends</h1>
      <p className="text-gray-500">Monthly average price for one commodity in one unit</p>

      <div className="mt-6 flex flex-wrap items-end gap-4 rounded-lg border p-4">
        <label className="flex flex-col text-sm">
          Commodity
          <select className={field} value={commodityId} onChange={(e) => update({ commodity: e.target.value })}>
            {commodities.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </label>
        <label className="flex flex-col text-sm">
          County
          <select className={field} value={filters.county} onChange={(e) => update({ county: e.target.value })}>
            <option value="">All counties</option>
            {counties.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </label>
        <label className="flex flex-col text-sm">
          Price type
          <select className={field} value={filters.priceType} onChange={(e) => update({ priceType: e.target.value })}>
            <option value="retail">Retail</option>
            <option value="wholesale">Wholesale</option>
          </select>
        </label>
        <label className="flex flex-col text-sm">
          Unit
          <select
            className={field}
            value={filters.unit || trend?.unit || ""}
            onChange={(e) => setFilters((f) => ({ ...f, unit: e.target.value }))}
          >
            {(trend?.available_units ?? []).map((u) => (
              <option key={u} value={u}>{u}</option>
            ))}
          </select>
        </label>
      </div>

      {result?.error && !loading && <p className="mt-4 text-red-600">Could not load trends: {result.error}</p>}

      <div className={`mt-6 ${loading ? "opacity-50" : ""}`}>
        {trend && trend.points.length === 0 && (
          <p className="text-gray-500">No prices for this selection. Try another price type or county.</p>
        )}
        {trend && trend.points.length > 0 && (
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" minTickGap={30} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="avg_price" name={`Average (KES per ${trend.unit})`} stroke="#2563eb" dot={false} strokeWidth={2} />
                <Line type="monotone" dataKey="max_price" name="Highest" stroke="#dc2626" dot={false} strokeDasharray="4 4" />
                <Line type="monotone" dataKey="min_price" name="Lowest" stroke="#16a34a" dot={false} strokeDasharray="4 4" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
        {!trend && !result?.error && <p>Loading...</p>}
      </div>

      {stats && stats.months > 0 && (
        <div className="mt-6 grid grid-cols-2 gap-4 md:grid-cols-4">
          <div className="rounded-lg border p-3">
            <div className="text-xs text-gray-500">Months with data</div>
            <div className="text-xl font-semibold">{stats.months}</div>
          </div>
          <div className="rounded-lg border p-3">
            <div className="text-xs text-gray-500">Price variation (CV)</div>
            <div className="text-xl font-semibold">{pct(stats.coefficient_of_variation_pct)}</div>
          </div>
          <div className="rounded-lg border p-3">
            <div className="text-xs text-gray-500">Avg monthly change</div>
            <div className="text-xl font-semibold">{pct(stats.mean_abs_monthly_change_pct)}</div>
          </div>
          <div className="rounded-lg border p-3">
            <div className="text-xs text-gray-500">Monthly change spread</div>
            <div className="text-xl font-semibold">{pct(stats.monthly_change_std_pct)}</div>
          </div>
        </div>
      )}
      <p className="mt-4 text-xs text-gray-500">
        Averages combine all markets in the selection, so they can shift when markets start or stop
        reporting. Pick a county to reduce this effect.
      </p>
    </main>
  );
}
