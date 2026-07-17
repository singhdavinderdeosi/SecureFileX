document.addEventListener("DOMContentLoaded", function () {
    const aiBtn = document.getElementById("ai-assistant-btn");
    const aiWidget = document.getElementById("ai-widget");
    const aiSendBtn = document.getElementById("ai-send-btn");
    const aiInput = document.getElementById("ai-input");
    const aiMessages = document.getElementById("ai-messages");
  
    aiBtn.addEventListener("click", () => {
      aiWidget.style.display = aiWidget.style.display === "flex" ? "none" : "flex";
    });
  
    aiSendBtn.addEventListener("click", sendMessage);
    aiInput.addEventListener("keypress", function (e) {
      if (e.key === "Enter") sendMessage();
    });
  
    function sendMessage() {
      const msg = aiInput.value.trim();
      if (!msg) return;
      appendMessage("🧑‍💻 You", msg);
      aiInput.value = "";
  
      // Fake response
      setTimeout(() => {
        appendMessage("🤖 AI", "This is a sample reply. Connect me to your backend to go live!");
      }, 800);
  
      // Real integration (optional)
      // fetch("/ai-response/", {
      //   method: "POST",
      //   headers: { "Content-Type": "application/json" },
      //   body: JSON.stringify({ prompt: msg })
      // })
      // .then(res => res.json())
      // .then(data => appendMessage("🤖 AI", data.reply));
    }
  
    function appendMessage(sender, text) {
      const el = document.createElement("div");
      el.className = "ai-msg";
      el.innerHTML = `<strong>${sender}:</strong> ${text}`;
      aiMessages.appendChild(el);
      aiMessages.scrollTop = aiMessages.scrollHeight;
    }
  });
  