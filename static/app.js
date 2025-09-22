const chat = document.getElementById("chat");
const form = document.getElementById("composer");
const input = document.getElementById("message");
const sendBtn = document.getElementById("send");

function addMessage(who, text) {
  const item = document.createElement("div");
  item.className = `msg ${who}`;
  const whoEl = document.createElement("div");
  whoEl.className = "who";
  whoEl.textContent = who === "user" ? "You" : "BankBot";
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  item.appendChild(whoEl);
  item.appendChild(bubble);
  chat.appendChild(item);
  chat.scrollTop = chat.scrollHeight;
}

async function sendToBot(message) {
  const res = await fetch("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });

  if (!res.ok) {
    const errText = await res.text().catch(() => res.statusText);
    throw new Error(`Server error (${res.status}): ${errText}`);
  }

  const data = await res.json();
  return data.response || "Sorry, I didn’t get that.";
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;

  addMessage("user", text);
  input.value = "";
  input.focus();

  // typing indicator
  sendBtn.disabled = true;
  const typingId = `typing-${Date.now()}`;
  addMessage("bot", "…");
  const typingNode = chat.lastElementChild;

  try {
    const reply = await sendToBot(text);
    typingNode.querySelector(".bubble").textContent = reply;
  } catch (err) {
    typingNode.querySelector(".bubble").textContent =
      "⚠️ " + (err.message || "Network error");
  } finally {
    sendBtn.disabled = false;
  }
});

// greet on load
addMessage("bot", "Hello! How can I help you today?");
