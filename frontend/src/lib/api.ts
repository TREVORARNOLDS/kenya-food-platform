export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:5000";

export type Paginated<T> = {
  items: T[];
  page: number;
  page_size: number;
  total: number;
  pages: number;
};

export type County = { id: number; name: string };
export type Commodity = { id: number; name: string; category: string | null };

export type Price = {
  id: number;
  observed_on: string;
  market_name: string;
  county_name: string;
  commodity_name: string;
  unit: string;
  price_type: string;
  currency: string;
  price: number;
  price_usd: number | null;
};

export async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`);
  if (!res.ok) {
    throw new Error(`Request failed (HTTP ${res.status})`);
  }
  return res.json();
}
