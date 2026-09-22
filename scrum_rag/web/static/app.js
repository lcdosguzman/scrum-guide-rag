const form = document.querySelector("#chat-form");
const input = document.querySelector("#question");
const messages = document.querySelector("#messages");
const sendButton = document.querySelector("#send-button");

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const question = input.value.trim();
  if (!question) return;

  addMessage("user", question);
  input.value = "";
  resizeInput();

  const loading = addMessage("assistant", "Consultando la guia...", true);
  sendButton.disabled = true;

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const payload = await response.json();

    if (!response.ok) {
      throw new Error(payload.error || "No se pudo generar la respuesta.");
    }

    loading.remove();
    addAssistantMessage(payload.answer, payload.sources || []);
  } catch (error) {
    loading.remove();
    addMessage("assistant", error.message);
  } finally {
    sendButton.disabled = false;
    input.focus();
  }
});

input.addEventListener("input", resizeInput);
input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

function resizeInput() {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 180)}px`;
}

function addMessage(role, text, isLoading = false) {
  const article = document.createElement("article");
  article.className = `message ${role}${isLoading ? " loading" : ""}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = role === "user" ? "TU" : "AI";

  const bubble = document.createElement("div");
  bubble.className = "bubble";

  const paragraph = document.createElement("p");
  paragraph.textContent = text;
  bubble.append(paragraph);

  article.append(avatar, bubble);
  messages.append(article);
  messages.scrollTop = messages.scrollHeight;
  return article;
}

function addAssistantMessage(answer, sources) {
  const article = addMessage("assistant", answer);
  if (!sources.length) return;

  const bubble = article.querySelector(".bubble");
  const sourceList = document.createElement("div");
  sourceList.className = "sources";

  const title = document.createElement("h3");
  title.textContent = "Fuentes recuperadas";
  sourceList.append(title);

  for (const source of sources) {
    const item = document.createElement("details");
    const summary = document.createElement("summary");
    const page = source.page ? `, pagina ${source.page}` : "";
    summary.textContent = `[${source.index}] ${source.source}${page}`;

    const preview = document.createElement("p");
    preview.textContent = source.preview;

    item.append(summary, preview);
    sourceList.append(item);
  }

  bubble.append(sourceList);
}
