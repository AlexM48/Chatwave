console.log("room.js connected");

const messagesArea = document.getElementById('messages-area');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const messageCount = document.getElementById('message-count');
const participantsList = document.getElementById('participants-list');

const chatMediaInput = document.getElementById('chat-media');

chatMediaInput.addEventListener('change', function(event) {
    const maxSize = 50 * 1024 * 1024; // 50 МБ
    const file = event.target.files[0];
    if (file && file.size > maxSize) {
        alert("Выбранный файл превышает лимит 50 МБ. Пожалуйста, выберите файл поменьше.");
        event.target.value = ""; // Очистить поле выбора файла
    }
});


// === Цвета пользователей ===
let userColors = JSON.parse(localStorage.getItem("userColors") || "{}");

function getUserColor(username) {
    if (username === "Admin") return "#ccf8d1";
    if (!userColors[username]) {
        const colors = [
            "#f2eaff", "#ffecc7", "#ffd4d4", "#d4f7ff",
            "#e1ffd4", "#fcd4ff", "#fff1d4"
        ];
        userColors[username] = colors[Math.floor(Math.random() * colors.length)];
        localStorage.setItem("userColors", JSON.stringify(userColors));
    }
    return userColors[username];
}

function scrollDown() {
    messagesArea.scrollTop = messagesArea.scrollHeight;
}

function updateMessageCount() {
    if (messageCount) {
        const count = messagesArea.querySelectorAll(".message").length;
        messageCount.textContent = count;
    }
}

// === Лайтбокс для фото и видео ===
const lightbox = document.createElement("div");
lightbox.className = "lightbox-overlay";
document.body.appendChild(lightbox);

document.addEventListener("click", (e) => {
    const media = e.target.closest(".chat-photo, video.chat-video");
    if (media) {
        lightbox.innerHTML = "";
        const clone = media.cloneNode(true);
        clone.style.maxWidth = "80%";
        clone.style.maxHeight = "80%";
        lightbox.appendChild(clone);
        lightbox.classList.add("active");
    } else if (e.target === lightbox) {
        lightbox.classList.remove("active");
    }
});

// === Отправка сообщения (AJAX, не ломает Daphne) ===
chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const text = chatInput.value.trim();
    const file = document.getElementById("chat-media").files[0];
    if (!text && !file) {
        alert("Пустое сообщение ❌");
        return;
    }

    const formData = new FormData(chatForm);
    const response = await fetch(window.location.pathname, {
        method: "POST",
        body: formData,
        headers: { "X-Requested-With": "XMLHttpRequest" },
    });

    if (!response.ok) {
        let errorMsg = "Ошибка отправки сообщения!";
        try {
            const errorData = await response.json();
            if (errorData.error) {
                errorMsg = errorData.error;
            }
        } catch (err) {
            if (file && file.size > 50 * 1024 * 1024) {
                errorMsg = "Файл слишком большой (максимум 50 МБ)";
            }
        }
        alert(errorMsg);
        return;
    }

    const data = await response.json();
    if (!data.success) {
        alert(data.error);
        return;
    }

    // Добавляем сообщение
    const msgDiv = document.createElement("div");
    msgDiv.classList.add("message", "self-msg");

    let html = `<span class="msg-username">${data.username}:</span>`;
    if (data.content) html += `<span class="msg-text">${data.content}</span>`;
    if (data.image_url)
        html += `<div class="msg-image"><img src="${data.image_url}" class="chat-photo"></div>`;
    if (data.video_url)
        html += `<div class="msg-video"><video class="chat-video" controls><source src="${data.video_url}" type="video/mp4"></video></div>`;

    msgDiv.innerHTML = html;
    messagesArea.appendChild(msgDiv);
    chatInput.value = "";
    document.getElementById("chat-media").value = "";
    updateMessageCount();
    scrollDown();
});

// === Применяем цвета пользователям ===
document.querySelectorAll(".message").forEach((msg) => {
    if (msg.classList.contains("self-msg") || msg.classList.contains("admin-msg")) return;
    const username = msg.querySelector(".msg-username")?.innerText.replace(":", "").trim();
    if (username) {
        msg.style.background = getUserColor(username);
    }
});
updateMessageCount();

// ====== Удаление сообщений ======
document.addEventListener("click", e => {
    const delBtn = e.target.closest(".msg-delete-btn");
    if (!delBtn) return;

    const msgId = delBtn.dataset.id;
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    if (confirm("Удалить это сообщение?")) {
        fetch(`/chat/delete_message/${msgId}/`, {
            method: "POST",
            headers: { "X-CSRFToken": csrftoken },
        })
        .then(r => {
            if (!r.ok) throw new Error("Ошибка удаления");
            // Убираем сообщение с экрана
            const el = document.getElementById(`message-${msgId}`);
            if (el) el.remove();
            // Обновляем счётчик
            const countEl = document.getElementById("message-count");
            if (countEl) countEl.textContent = document.querySelectorAll(".message").length;
        })
        .catch(err => console.error(err));
    }
});
