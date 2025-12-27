import axios from "axios";
import logger from "../utils/logger";

const API = axios.create({
  //baseURL: "/api",
  baseURL: "http://localhost:5000/api",
});

// Upload dataset
export async function uploadDataset(file) {
  const form = new FormData();
  form.append("file", file);

  const response = await API.post("/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });

  logger.debug("UPLOAD API RESPONSE:", response.data);
  return response.data;  // <-- this works 100%
}

// Preprocess
export async function preprocessData(payload) {
  const response = await API.post("/preprocess", payload);
  return response.data;
}

// Train model
export async function trainModel(payload) {
  const response = await API.post("/train", payload);
  return response.data;
}

// Save model
export async function saveModel(payload) {
  const response = await API.post("/save_model", payload);
  return response.data;
}

// Get confusion matrix and metrics for a trained model in a session
export async function getConfusionMatrix({ session_id, model_type, format = "json" }) {
  const response = await API.get("/confusion_matrix", {
    params: { session_id, model_type, format },
  });
  return response.data;
}
