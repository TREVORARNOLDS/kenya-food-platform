"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import {
  type Commodity,
  type County,
  type Paginated,
  type Price,
  getJson,
} from "@/lib/api";

const PAGE_SIZE = 25;

type Filters = {
  county: string;
  commodity: string;
  priceType: string;
  dateFrom: string;
  dateTo: string;
  sort: string;
  order: string;
  page: number;
};

const INITIAL: Filters = {
  county: "",
  commodity: "",
  priceType: "",
  dateFrom: "",
  dateTo: "",
  sort: "observed_on",
  order: "desc",
  page: 1,
};

type Result = { key: string; data?: Paginated<Price>; error?: string };

const field = "rounded border bg-white px-2 py-1 text-black";

export default function PricesPage() {
  const [filters, setFilters] = useState<Filters>(INITIAL);
  const [counties, setCounties] = useState<County[]>([]);
  const [commodities, setCommodities] = useState<Commodity[]>([]);
  const [result, setResult] = useState<Result | null>(null);

  // Dropdown options, loaded once
  useEffect(() => {
    getJson<Paginated<County>>("/api/v1/counties/?page_size=200")
      .then((r) => setCounties(r.items))
      .catch(() => {});
    getJson<Paginated<Commodity>>("/api/v1/commodities/?page_size=200")
      .then((r) => setCommodities(r.items))
      .catch(() => {});
  }, []);

  const queryString = useMemo(() => {
    const p = new URLSearchParams({
      page: String(filters.page),
      page_size: String(PAGE_SIZE),
      sort: filters.sort,
      order: filters.order,
    });
    if (filters.county) p.set("county_id", filters.county);
    if (filters.commodity) p.set("commodity_id", filters.commodity);
    if (filters.priceType) p.set("price_type", filters.priceType);
    if (filters.dateFrom) p.set("date_from", filters.dateFrom);
    if (filters.dateTo) p.set("date_to", filters.dateTo);
    return p.toString();
  }, [filters]);

  useEffect(() => {
    let cancelled = false;
    getJson<Paginated<Price>>(`/api/v1/prices/?${queryString}`)
      .then((data) => !cancelled && setResult({ key: queryString, data }))
      .catch((e) => !cancelled && setResult({ key: queryString, error: String(e.message ?? e) }));
    return () => {
      cancelled = true;
    };
  }, [queryString]);

  const loading = result?.key !== queryString;
  const data = result?.data;

  // Any filter change goes back to page 1
  const update = (patch: Partial<Filters>) =>
    setFilters((f) => ({ ...f, ...patch, page: 1 }));

  return (
    <main className="mx-auto max-w-6xl p-8">
      <Link href="/" className="text-sm text-blue-600 underline">
        ← System status
      </Link>
      <h1 className="mt-2 text-2xl font-bold">Food price explorer</h1>
      <p className="text-gray-500">WFP market prices for Kenya</p>

      <div className="mt-6 flex flex-wrap items-end gap-4 rounded-lg border p-4">
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
          Commodity
          <select className={field} value={filters.commodity} onChange={(e) => update({ commodity: e.target.value })}>
            <option value="">All commodities</option>
            {commodities.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </label>

        <label className="flex flex-col text-sm">
          Price type
          <select className={field} value={filters.priceType} onChange={(e) => update({ priceType: e.target.value })}>
            <option value="">Any</option>
            <option value="retail">Retail</option>
            <option value="wholesale">Wholesale</option>
          </select>
        </label>

        <label className="flex flex-col text-sm">
          From
          <input type="date" className={field} value={filters.dateFrom} onChange={(e) => update({ dateFrom: e.target.value })} />
        </label>

        <label className="flex flex-col text-sm">
          To
          <input type="date" className={field} value={filters.dateTo} onChange={(e) => update({ dateTo: e.target.value })} />
        </label>

        <label className="flex flex-col text-sm">
          Sort by
          <select
            className={field}
            value={`${filters.sort}:${filters.order}`}
            onChange={(e) => {
              const [sort, order] = e.target.value.split(":");
              update({ sort, order });
            }}
          >
            <option value="observed_on:desc">Newest first</option>
            <option value="observed_on:asc">Oldest first</option>
            <option value="price:desc">Price, high to low</option>
            <option value="price:asc">Price, low to high</option>
          </select>
        </label>

        <button className="rounded border px-3 py-1 text-sm" onClick={() => setFilters(INITIAL)}>
          Reset
        </button>
      </div>

      {result?.error && !loading && (
        <p className="mt-4 text-red-600">Could not load prices: {result.error}</p>
      )}

      <div className={`mt-4 overflow-x-auto ${loading ? "opacity-50" : ""}`}>
        <table className="w-full text-left text-sm">
          <thead className="border-b">
            <tr>
              <th className="p-2">Date</th>
              <th className="p-2">County</th>
              <th className="p-2">Market</th>
              <th className="p-2">Commodity</th>
              <th className="p-2">Unit</th>
              <th className="p-2">Type</th>
              <th className="p-2 text-right">Price</th>
              <th className="p-2 text-right">USD</th>
            </tr>
          </thead>
          <tbody>
            {data?.items.map((p) => (
              <tr key={p.id} className="border-b">
                <td className="p-2">{p.observed_on}</td>
                <td className="p-2">{p.county_name}</td>
                <td className="p-2">{p.market_name}</td>
                <td className="p-2">{p.commodity_name}</td>
                <td className="p-2">{p.unit}</td>
                <td className="p-2">{p.price_type}</td>
                <td className="p-2 text-right">
                  {p.price.toLocaleString(undefined, { maximumFractionDigits: 2 })} {p.currency}
                </td>
                <td className="p-2 text-right">
                  {p.price_usd == null ? "–" : p.price_usd.toFixed(2)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {data && data.items.length === 0 && (
          <p className="p-4 text-gray-500">No prices match these filters.</p>
        )}
        {!data && !result?.error && <p className="p-4">Loading...</p>}
      </div>

      {data && data.total > 0 && (
        <div className="mt-4 flex items-center gap-4 text-sm">
          <button
            className="rounded border px-3 py-1 disabled:opacity-40"
            disabled={filters.page <= 1}
            onClick={() => setFilters((f) => ({ ...f, page: f.page - 1 }))}
          >
            Previous
          </button>
          <span>
            Page {data.page} of {data.pages} ({data.total.toLocaleString()} prices)
          </span>
          <button
            className="rounded border px-3 py-1 disabled:opacity-40"
            disabled={filters.page >= data.pages}
            onClick={() => setFilters((f) => ({ ...f, page: f.page + 1 }))}
          >
            Next
          </button>
        </div>
      )}
    </main>
  );
}
