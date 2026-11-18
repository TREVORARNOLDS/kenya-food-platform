"use client";

import { useEffect, useState } from "react";

type Health = {
  status: string;
  service: string;
  database: { connected: boolean; postgis_version?: string };
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:5000";

export default function Home() {
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/api/v1/health/`)
      .then((r) => r.json())
      .then(setHealth)
      .catch((e) => setError(String(e)));
  }, []);

  return (
    <main className="mx-auto max-w-2xl p-10">
      <h1 className="text-2xl font-bold">
        Kenya Food Security &amp; Market Intelligence
      </h1>
      <p className="mt-1 text-gray-500">System status</p>

      <div className="mt-6 rounded-lg border p-4">
        {error && <p className="text-red-600">Backend unreachable: {error}</p>}
        {!error && !health && <p>Checking backend...</p>}
        {health && (
          <ul className="space-y-1">
            <li>
              API: <strong>{health.status}</strong>
            </li>
            <li>
              Database:{" "}
              <strong>{health.database.connected ? "connected" : "down"}</strong>
            </li>
            {health.database.postgis_version && (
              <li>PostGIS: {health.database.postgis_version}</li>
            )}
          </ul>
        )}
      </div>
    </main>
  );
}