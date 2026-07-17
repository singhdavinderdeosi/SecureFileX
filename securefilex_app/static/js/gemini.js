function sendToGemini() {
    const input = document.getElementById("gemini-input").value;
    fetch("/gemini/ask/", {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ prompt: input }),
    })
    .then(res => res.json())
    .then(data => {
      document.getElementById("gemini-response").innerText = data.response;
    });
  }
  