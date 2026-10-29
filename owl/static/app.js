"use strict";
const field = id => document.getElementById(id);
async function loadDefaults() {
  try {
    const response = await fetch("/api/config", {cache: "no-store"});
    if (!response.ok) return;
    const config = await response.json();
    if (["ollama", "ollama-cloud", "bedrock"].includes(config.provider)) field("provider").value = config.provider;
    if (["assistant", "workforce"].includes(config.mode)) field("mode").value = config.mode;
  } catch { /* Keep the local default on connection error. */ }
}
field("task-form").addEventListener("submit", async event => {
  event.preventDefault();
  const button = field("run");
  button.disabled = true;
  field("status").textContent = "Processing task...";
  field("answer").textContent = "";
  try {
    const response = await fetch("/api/run", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        task: field("task").value,
        provider: field("provider").value,
        mode: field("mode").value,
        model: field("model").value.trim()
      })
    });
    const result = await response.json();
    field("answer").textContent = response.ok ? result.answer : result.error;
    field("status").textContent = response.ok ? "Complete" : "Request failed";
  } catch {
    field("status").textContent = "Unable to connect";
    field("answer").textContent = "The server is unavailable.";
  } finally {
    button.disabled = false;
  }
});
loadDefaults();
