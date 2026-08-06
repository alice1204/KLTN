const API_BASE_URL = "http://127.0.0.1:8000";
const MAX_MESSAGE_LENGTH = 4000;
const REQUEST_TIMEOUT_MS = 120000;

const appShell = document.getElementById("app");
const sidebarOverlay = document.getElementById("sidebarOverlay");
const openSidebarButton = document.getElementById("openSidebarButton");
const closeSidebarButton = document.getElementById("closeSidebarButton");

const documentScopeSelect = document.getElementById("documentScope");
const facultySelect = document.getElementById("facultySelect");
const activeScope = document.getElementById("activeScope");
const activeFaculty = document.getElementById("activeFaculty");
const filterBadge = document.getElementById("filterBadge");

const chatForm = document.getElementById("chatForm");
const messageInput = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");
const newChatButton = document.getElementById("newChatButton");
const chatMessages = document.getElementById("chatMessages");
const sessionStatus = document.getElementById("sessionStatus");
const connectionBadge = document.getElementById("connectionBadge");
const connectionBadgeText = document.getElementById(
  "connectionBadgeText"
);
const characterCount = document.getElementById("characterCount");

let interactionId = null;
let isLoading = false;

setViewportHeight();
updateCharacterCount();
updateFilterLabels();
autoResizeTextarea();

window.addEventListener("resize", setViewportHeight);

if (window.visualViewport) {
  window.visualViewport.addEventListener("resize", setViewportHeight);
}

openSidebarButton.addEventListener("click", openSidebar);
closeSidebarButton.addEventListener("click", closeSidebar);
sidebarOverlay.addEventListener("click", closeSidebar);

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && appShell.classList.contains("sidebar-open")) {
    closeSidebar();
  }
});

documentScopeSelect.addEventListener("change", () => {
  updateFacultyAvailability();
  updateFilterLabels();
});

facultySelect.addEventListener("change", updateFilterLabels);

document.querySelectorAll("[data-question]").forEach((button) => {
  button.addEventListener("click", () => {
    messageInput.value = button.dataset.question || "";
    updateCharacterCount();
    autoResizeTextarea();
    closeSidebar();
    messageInput.focus();
  });
});

messageInput.addEventListener("input", () => {
  updateCharacterCount();
  autoResizeTextarea();
});

messageInput.addEventListener("keydown", (event) => {
  const isMobile = window.matchMedia("(max-width: 640px)").matches;

  if (
    event.key === "Enter" &&
    !event.shiftKey &&
    !event.isComposing &&
    !isMobile
  ) {
    event.preventDefault();
    chatForm.requestSubmit();
  }
});

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (isLoading) {
    return;
  }

  const message = messageInput.value.trim();

  if (!message) {
    showError("Bạn chưa nhập câu hỏi.");
    messageInput.focus();
    return;
  }

  if (message.length > MAX_MESSAGE_LENGTH) {
    showError(`Câu hỏi không được vượt quá ${MAX_MESSAGE_LENGTH} ký tự.`);
    return;
  }

  removeWelcomeCard();
  addMessage("user", message);

  messageInput.value = "";
  updateCharacterCount();
  autoResizeTextarea();

  const loadingMessage = addLoadingMessage();
  setLoading(true);

  try {
    const result = await sendChatRequest(message);

    if (!result.interaction_id) {
      throw new Error("Backend không trả về interaction_id.");
    }

    interactionId = result.interaction_id;
    loadingMessage.remove();

    addAssistantMessage(
      result.answer || "Hệ thống không trả về nội dung.",
      Array.isArray(result.sources) ? result.sources : []
    );

    sessionStatus.textContent = "Đang trong một phiên tra cứu";
    setBadge("Đã kết nối", "success");
    closeSidebar();
  } catch (error) {
    loadingMessage.remove();
    showError(normalizeError(error));
    setBadge("Có lỗi", "error");
  } finally {
    setLoading(false);
    messageInput.focus();
  }
});

newChatButton.addEventListener("click", () => {
  if (!isLoading) {
    resetConversation();
  }
});

async function sendChatRequest(message) {
  return fetchJson(`${API_BASE_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message,
      document_scope: documentScopeSelect.value,
      faculty_id: facultySelect.value,
      previous_interaction_id: interactionId,
    }),
  });
}

async function fetchJson(url, options) {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(
    () => controller.abort(),
    REQUEST_TIMEOUT_MS
  );

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });

    let data;

    try {
      data = await response.json();
    } catch {
      throw new Error("Backend trả về dữ liệu không hợp lệ.");
    }

    if (!response.ok) {
      const detail =
        typeof data.detail === "string"
          ? data.detail
          : JSON.stringify(data.detail || data);

      throw new Error(detail || `Lỗi HTTP ${response.status}.`);
    }

    return data;
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error(
        "Yêu cầu mất quá nhiều thời gian. Hãy thử lại sau."
      );
    }

    throw error;
  } finally {
    window.clearTimeout(timeoutId);
  }
}

function updateFacultyAvailability() {
  const onlyAcademy = documentScopeSelect.value === "academy";

  facultySelect.disabled = onlyAcademy;

  if (onlyAcademy) {
    facultySelect.value = "all";
  }
}

function updateFilterLabels() {
  const scopeText =
    documentScopeSelect.options[documentScopeSelect.selectedIndex].text;
  const facultyText =
    facultySelect.options[facultySelect.selectedIndex].text;

  activeScope.textContent = `Phạm vi: ${scopeText}`;
  activeFaculty.textContent = `Khoa: ${facultyText}`;
  filterBadge.textContent =
    facultySelect.value === "all"
      ? scopeText
      : `${scopeText} · ${facultyText}`;
}

function resetConversation() {
  interactionId = null;
  isLoading = false;

  chatMessages.innerHTML = `
    <div class="messages-inner">
      <section class="welcome-card">
        <div class="welcome-icon" aria-hidden="true">Q</div>
        <h2>Bạn cần tra cứu quy định nào?</h2>
        <p>
          Hãy nhập câu hỏi hoặc chọn một câu hỏi gợi ý. Hệ thống sẽ
          giải thích dựa trên kho tài liệu đã được chuẩn bị sẵn.
        </p>

        <div class="suggestion-grid">
          <button
            class="suggestion-button"
            type="button"
            data-question="Điều kiện để được làm khóa luận tốt nghiệp là gì?"
          >
            Điều kiện làm khóa luận
          </button>

          <button
            class="suggestion-button"
            type="button"
            data-question="Điều kiện để được xét tốt nghiệp là gì?"
          >
            Điều kiện xét tốt nghiệp
          </button>

          <button
            class="suggestion-button"
            type="button"
            data-question="Quy định về số tín chỉ tối thiểu trong một học kỳ là gì?"
          >
            Số tín chỉ mỗi học kỳ
          </button>

          <button
            class="suggestion-button"
            type="button"
            data-question="Khi nào sinh viên bị cảnh báo học tập?"
          >
            Cảnh báo học tập
          </button>
        </div>
      </section>
    </div>
  `;

  bindDynamicSuggestionButtons();

  messageInput.value = "";
  updateCharacterCount();
  autoResizeTextarea();

  sessionStatus.textContent =
    "Tra cứu quy chế chung và quy định các khoa";
  setBadge("Sẵn sàng", "success");
  closeSidebar();
  messageInput.focus();
}

function bindDynamicSuggestionButtons() {
  chatMessages.querySelectorAll("[data-question]").forEach((button) => {
    button.addEventListener("click", () => {
      messageInput.value = button.dataset.question || "";
      updateCharacterCount();
      autoResizeTextarea();
      messageInput.focus();
    });
  });
}

function removeWelcomeCard() {
  chatMessages.querySelector(".welcome-card")?.remove();
}

function addMessage(type, content) {
  const messagesInner = ensureMessagesInner();

  const article = document.createElement("article");
  article.className = `message ${type}`;

  const avatar = document.createElement("div");
  avatar.className =
    type === "user"
      ? "avatar user-avatar"
      : "avatar assistant-avatar";
  avatar.setAttribute("aria-hidden", "true");
  avatar.textContent = type === "user" ? "BẠN" : "AI";

  const messageContent = document.createElement("div");
  messageContent.className = "message-content";

  const meta = document.createElement("div");
  meta.className = "message-meta";
  meta.textContent = type === "user" ? "Bạn" : "Trợ lý quy chế";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = content;

  messageContent.appendChild(meta);
  messageContent.appendChild(bubble);
  article.appendChild(avatar);
  article.appendChild(messageContent);
  messagesInner.appendChild(article);

  scrollToBottom();
  return article;
}

function addAssistantMessage(content, sources) {
  const article = addMessage("assistant", content);

  if (sources.length === 0) {
    return article;
  }

  const messageContent = article.querySelector(".message-content");
  const sourcesContainer = document.createElement("div");
  sourcesContainer.className = "sources";

  sources.forEach((source) => {
    const card = document.createElement("div");
    card.className = "source-card";

    const title = document.createElement("strong");
    title.textContent =
      source.document_title || source.title || "Tài liệu tham khảo";

    const details = [
      source.section,
      source.page ? `Trang ${source.page}` : null,
      source.scope,
    ]
      .filter(Boolean)
      .join(" · ");

    card.appendChild(title);

    if (details) {
      card.appendChild(document.createTextNode(details));
    }

    sourcesContainer.appendChild(card);
  });

  messageContent.appendChild(sourcesContainer);
  scrollToBottom();

  return article;
}

function addLoadingMessage() {
  const messagesInner = ensureMessagesInner();

  const article = document.createElement("article");
  article.className = "message assistant";

  const avatar = document.createElement("div");
  avatar.className = "avatar assistant-avatar";
  avatar.setAttribute("aria-hidden", "true");
  avatar.textContent = "AI";

  const messageContent = document.createElement("div");
  messageContent.className = "message-content";

  const meta = document.createElement("div");
  meta.className = "message-meta";
  meta.textContent = "Đang tra cứu tài liệu...";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.innerHTML = `
    <span class="typing" aria-label="Đang trả lời">
      <span></span><span></span><span></span>
    </span>
  `;

  messageContent.appendChild(meta);
  messageContent.appendChild(bubble);
  article.appendChild(avatar);
  article.appendChild(messageContent);
  messagesInner.appendChild(article);

  scrollToBottom();
  return article;
}

function showError(message) {
  removeWelcomeCard();
  const article = addMessage("assistant", message);
  article.classList.add("error-message");
}

function setLoading(value) {
  isLoading = value;
  sendButton.disabled = value;
  newChatButton.disabled = value;
  messageInput.disabled = value;
  documentScopeSelect.disabled = value;
  facultySelect.disabled =
    value || documentScopeSelect.value === "academy";

  if (value) {
    setBadge("Đang xử lý", "loading");
  }
}

function setBadge(text, state) {
  connectionBadgeText.textContent = text;
  connectionBadge.className = "status-badge";

  if (state === "loading") {
    connectionBadge.classList.add("loading");
  } else if (state === "error") {
    connectionBadge.classList.add("error");
  }
}

function normalizeError(error) {
  if (error instanceof TypeError) {
    return (
      "Không kết nối được với backend. Hãy kiểm tra FastAPI đang chạy " +
      "tại http://127.0.0.1:8000 và cấu hình CORS đã đúng."
    );
  }

  return error?.message || "Đã xảy ra lỗi không xác định.";
}

function ensureMessagesInner() {
  let messagesInner = chatMessages.querySelector(".messages-inner");

  if (!messagesInner) {
    messagesInner = document.createElement("div");
    messagesInner.className = "messages-inner";
    chatMessages.appendChild(messagesInner);
  }

  return messagesInner;
}

function updateCharacterCount() {
  characterCount.textContent =
    `${messageInput.value.length} / ${MAX_MESSAGE_LENGTH}`;
}

function autoResizeTextarea() {
  messageInput.style.height = "auto";
  messageInput.style.height =
    `${Math.min(messageInput.scrollHeight, 180)}px`;
}

function scrollToBottom() {
  requestAnimationFrame(() => {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  });
}

function openSidebar() {
  if (window.matchMedia("(min-width: 901px)").matches) {
    return;
  }

  appShell.classList.add("sidebar-open");
  sidebarOverlay.hidden = false;
  openSidebarButton.setAttribute("aria-expanded", "true");
  closeSidebarButton.focus();
}

function closeSidebar() {
  appShell.classList.remove("sidebar-open");
  sidebarOverlay.hidden = true;
  openSidebarButton.setAttribute("aria-expanded", "false");
}

function setViewportHeight() {
  const height = window.visualViewport?.height ?? window.innerHeight;

  document.documentElement.style.setProperty(
    "--app-height",
    `${Math.round(height)}px`
  );
}
