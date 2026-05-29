import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
  timeout: 60000,
});

export const checkHealth = () =>
  fetch("http://localhost:8000/health").then((r) => r.ok);

export const sendQuestion = async (question) => {
  const { data } = await api.post("/api/chat", { question });
  return data;
};

export default api;
