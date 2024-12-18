"use client";

import { useEffect, useState } from "react";
import Spinner from "./components/Spinner";

export default function Home() {
  const [apiData, setApiData] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchData = async () => {
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

      if (!apiBaseUrl) {
        setApiData("API base URL is not defined.");
        setLoading(false);
        return;
      }

      const apiUrl = `${apiBaseUrl}/api/example`;

      try {
        const response = await fetch(apiUrl);
        if (!response.ok) {
          throw new Error("Network response was not ok");
        }
        const data = await response.json();
        setApiData(data.message || "No data received");
      } catch (error) {
        setApiData("Error fetching data");
        console.error("Error fetching API data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return (
    <>
      <div>An absolutely raw website (but after the first commit!)</div>
      <div>Loading something from an api:</div>
      <div style={{ marginTop: "10px" }}>
        {loading ? <Spinner /> : <div>{apiData}</div>}
      </div>
    </>
  );
}
