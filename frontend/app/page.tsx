"use client";

import { useEffect, useState } from "react";
import Spinner from "./components/Spinner";

export default function Home() {
  const [apiData, setApiData] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [userId, setUserId] = useState<string>("");
  const [userName, setUserName] = useState<string>("");
  const [userEmail, setUserEmail] = useState<string>("");
  const [responseMessage, setResponseMessage] = useState<string | null>(null);

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

  const handleAddUser = async () => {
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

    if (!apiBaseUrl) {
      setResponseMessage("API base URL is not defined.");
      return;
    }

    const apiUrl = `${apiBaseUrl}/users/`;

    try {
      const response = await fetch(apiUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: userId,
          name: userName,
          email: userEmail,
        }),
      });

      if (!response.ok) {
        throw new Error("Error adding user");
      }

      setResponseMessage("User added successfully.");
    } catch (error) {
      setResponseMessage("Error adding user.");
      console.error("Error adding user:", error);
    }
  };

  const handleDeleteUser = async () => {
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

    if (!apiBaseUrl) {
      setResponseMessage("API base URL is not defined.");
      return;
    }

    const apiUrl = `${apiBaseUrl}/users/${userId}`;

    try {
      const response = await fetch(apiUrl, {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error("Error deleting user");
      }

      setResponseMessage("User deleted successfully.");
    } catch (error) {
      setResponseMessage("Error deleting user.");
      console.error("Error deleting user:", error);
    }
  };

  const handleGetUser = async () => {
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

    if (!apiBaseUrl) {
      setResponseMessage("API base URL is not defined.");
      return;
    }

    const apiUrl = `${apiBaseUrl}/users/${userId}`;

    try {
      const response = await fetch(apiUrl);

      if (!response.ok) {
        throw new Error("Error fetching user data");
      }

      const data = await response.json();
      setResponseMessage(`User Data: ${JSON.stringify(data)}`);
    } catch (error) {
      setResponseMessage("Error fetching user data.");
      console.error("Error fetching user data:", error);
    }
  };

  return (
    <>
      <div>An absolutely raw website (but after the first commit!)</div>
      <div>Loading something from an API:</div>
      <div style={{ marginTop: "10px" }}>
        {loading ? <Spinner /> : <div>{apiData}</div>}
      </div>

      {/* Add User Section */}
      <div style={{ marginTop: "20px" }}>
        <h3>Add User</h3>
        <input
          type="text"
          placeholder="User ID"
          value={userId}
          onChange={(e) => setUserId(e.target.value)}
        />
        <input
          type="text"
          placeholder="Name"
          value={userName}
          onChange={(e) => setUserName(e.target.value)}
        />
        <input
          type="email"
          placeholder="Email"
          value={userEmail}
          onChange={(e) => setUserEmail(e.target.value)}
        />
        <button onClick={handleAddUser}>Add User</button>
      </div>

      {/* Delete User Section */}
      <div style={{ marginTop: "20px" }}>
        <h3>Delete User</h3>
        <input
          type="text"
          placeholder="User ID"
          value={userId}
          onChange={(e) => setUserId(e.target.value)}
        />
        <button onClick={handleDeleteUser}>Delete User</button>
      </div>

      {/* Get User Section */}
      <div style={{ marginTop: "20px" }}>
        <h3>Get User</h3>
        <input
          type="text"
          placeholder="User ID"
          value={userId}
          onChange={(e) => setUserId(e.target.value)}
        />
        <button onClick={handleGetUser}>Get User</button>
      </div>

      {/* Response Message */}
      {responseMessage && (
        <div style={{ marginTop: "20px", color: "green" }}>{responseMessage}</div>
      )}
    </>
  );
}
