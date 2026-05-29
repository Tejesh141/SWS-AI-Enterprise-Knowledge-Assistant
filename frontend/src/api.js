import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
  timeout: 30000,
});

export const sendQuestion = async (question) => {
  const { data } = await api.post("/api/chat", { question });
  return data; // { answer, sources: [{ document, page }] }
};

export default api;
