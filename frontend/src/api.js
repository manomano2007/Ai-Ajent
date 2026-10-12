export const API_BASE_URL = "https://ai-ajent.onrender.com";
const CHAT_TIMEOUT_MS = 60000;
const HEALTH_TIMEOUT_MS = 5000;

export class ApiError extends Error {
  constructor(message, { network = false } = {}) {
    super(message);
    this.name = "ApiError";
    this.network = network;
  }
}

function readErrorDetail(data) {
  if (data && typeof data.detail === "string") {
    return data.detail;
  }
  if (data && Array.isArray(data.detail)) {
    return "Please check your message and try again. It may be empty or too long.";
  }
  return "Something went wrong. Please try again.";
}

export async function sendChatMessage(message) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), CHAT_TIMEOUT_MS);

  let response;
  try {
    response = await fetch(`${API_BASE_URL}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
      signal: controller.signal,
    });
  } catch (err) {
    if (err.name === "AbortError") {
      throw new ApiError("The request took too long. Please try again.");
    }
    throw new ApiError(
      "Could not reach the PyMate AI backend. Make sure the backend server is running at https://ai-ajent.onrender.com0.",
      { network: true }
    );
  } finally {
    clearTimeout(timer);
  }

  let data = null;
  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    throw new ApiError(readErrorDetail(data));
  }

  if (!data || typeof data.reply !== "string") {
    throw new ApiError("The backend sent an unexpected response. Please try again.");
  }

  return data.reply;
}

export async function checkBackendHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`, {
      method: "GET",
      signal: AbortSignal.timeout(HEALTH_TIMEOUT_MS),
    });
    return response.ok;
  } catch {
    return false;
  }
}