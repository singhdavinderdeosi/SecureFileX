document.addEventListener('DOMContentLoaded', () => {
  // ===============================
  // 🔁 AOS + Binary Rain Init
  // ===============================
  AOS.init();
  const canvas = document.getElementById("binaryRain");
  const ctx = canvas?.getContext("2d");

  function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  resizeCanvas();
  window.addEventListener('resize', resizeCanvas);

  const chars = "01";
  const fontSize = 14;
  const columns = Math.floor(canvas.width / fontSize);
  const drops = Array(columns).fill(1);

  function drawRain() {
    ctx.fillStyle = "rgba(0, 0, 0, 0.05)";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "#00f0ff";
    ctx.font = `${fontSize}px monospace`;

    drops.forEach((y, x) => {
      const text = chars[Math.floor(Math.random() * chars.length)];
      ctx.fillText(text, x * fontSize, y * fontSize);
      drops[x] = (y * fontSize > canvas.height && Math.random() > 0.975) ? 0 : y + 1;
    });
  }
  setInterval(drawRain, 33);

  // ===============================
  // 🧭 Wizard Navigation
  // ===============================
  document.querySelectorAll('.next-step').forEach(btn => {
    btn.addEventListener('click', () => {
      const current = document.querySelector('.step-content.active-step');
      const next = current?.nextElementSibling;
      if (next?.classList.contains('step-content')) {
        current.classList.remove('active-step');
        next.classList.add('active-step');
        document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
        document.querySelectorAll('.tab')[
          [...document.querySelectorAll('.step-content')].indexOf(next)
        ]?.classList.add('active');
      }
    });
  });

  // ===============================
  // 📂 File Upload
  // ===============================
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('file');
  const preview = document.getElementById('preview');

  dropzone?.addEventListener('click', () => fileInput?.click());
  ['dragover', 'dragleave', 'drop'].forEach(event =>
    dropzone?.addEventListener(event, e => e.preventDefault())
  );

  dropzone?.addEventListener('dragover', () => dropzone.classList.add('drag-over'));
  dropzone?.addEventListener('dragleave', () => dropzone.classList.remove('drag-over'));
  dropzone?.addEventListener('drop', e => {
    const file = e.dataTransfer.files[0];
    if (file) {
      fileInput.files = e.dataTransfer.files;
      preview.textContent = `✔️ Selected: ${file.name}`;
      preview.classList.add("fade-in");
    }
  });

  fileInput?.addEventListener('change', () => {
    if (fileInput.files.length) {
      preview.textContent = `✔️ Selected: ${fileInput.files[0].name}`;
      preview.classList.add("fade-in");
      document.querySelector('.next-step')?.click();
    }
  });

  // ===============================
  // 🔐 Toggle Password/KeyFile
  // ===============================
  document.getElementById('opt_password')?.addEventListener('change', () => {
    toggleClass(document.getElementById('passwordField'), 'd-none', false);
    toggleClass(document.getElementById('keyFileField'), 'd-none', true);
  });

  document.getElementById('opt_keyfile')?.addEventListener('change', () => {
    toggleClass(document.getElementById('passwordField'), 'd-none', true);
    toggleClass(document.getElementById('keyFileField'), 'd-none', false);
  });

  // ===============================
  // ⚡ Password Generator
  // ===============================
  const generateRandomPassword = (length = 20) => {
    const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*";
    return Array.from({ length }, () => chars[Math.floor(Math.random() * chars.length)]).join('');
  };

  document.getElementById('generatePass')?.addEventListener('click', () => {
    const pass = generateRandomPassword();
    const input = document.getElementById('password');
    input.value = pass;
    updateStrength(pass);
    showKeyPreview(pass);
    updateQRPreview(pass);
    showToast("🔐 Password generated!", "info");
  });

  document.getElementById('copyPass')?.addEventListener('click', () => {
    const val = document.getElementById('password')?.value.trim();
    if (val) {
      navigator.clipboard.writeText(val);
      showToast("📋 Password copied to clipboard!", "success");
    }
  });

  document.getElementById('password')?.addEventListener('input', e => {
    const val = e.target.value;
    updateStrength(val);
    showKeyPreview(val);
    updateQRPreview(val);
  });

  function updateStrength(pass) {
    const bar = document.getElementById('passStrength');
    let score = 0;
    if (pass.length >= 8) score++;
    if (/[a-z]/.test(pass)) score++;
    if (/[A-Z]/.test(pass)) score++;
    if (/[0-9]/.test(pass)) score++;
    if (/[^A-Za-z0-9]/.test(pass)) score++;

    const percent = (score / 5) * 100;
    bar.style.width = `${percent}%`;
    bar.className = "progress-bar";
    bar.classList.add(
      percent < 40 ? "bg-danger" :
      percent < 80 ? "bg-warning" : "bg-success"
    );
  }

  function showKeyPreview(key) {
    const container = document.getElementById('displayKeyContainer');
    const output = document.getElementById('displayKey');
    toggleClass(container, 'd-none', !key.trim());
    output.textContent = key;
  }

  function updateQRPreview(content) {
    const qr = document.getElementById('qr-preview');
    if (qr) {
      qr.innerHTML = "";
      if (content.trim()) {
        new QRCode(qr, {
          text: content,
          width: 150,
          height: 150,
          colorDark: "#00ffe1",
          colorLight: "#000",
          correctLevel: QRCode.CorrectLevel.H
        });
      }
    }
  }

  document.getElementById("toggleShare")?.addEventListener("change", function () {
    toggleClass(document.getElementById("share-options"), 'd-none', !this.checked);
  });

  // ===============================
  // 🚀 AJAX Encryption Submit
  // ===============================
  document.getElementById('encrypt-form')?.addEventListener('submit', e => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const xhr = new XMLHttpRequest();
    xhr.open("POST", e.target.action || window.location.href);

    xhr.upload.addEventListener("progress", e => {
      if (e.lengthComputable) updateProgress(Math.min((e.loaded / e.total) * 90, 90));
    });

    xhr.onload = () => {
      if (xhr.status === 200) {
        try {
          const data = JSON.parse(xhr.responseText.trim());
          updateProgress(100);
          setTimeout(() => showResult(data), 500);
        } catch (err) {
          console.error("❌ JSON parse error:", err);
          showToast("⚠️ Failed to process server response.", "danger");
        }
      } else {
        console.error("❌ Server error:", xhr.status, xhr.responseText);
        showToast("❌ Error occurred during encryption.", "danger");
      }
    };

    xhr.onerror = () => {
      showToast("⚠️ Network issue. Please try again.", "danger");
    };

    xhr.send(formData);
  });

  function updateProgress(percent) {
    const bar = document.getElementById('progress-bar');
    const label = document.getElementById('progress-text');
    bar.style.width = `${percent}%`;
    bar.innerText = `${Math.floor(percent)}%`;
    label.innerText = `Encrypting... (${Math.floor(percent)}%)`;
  }

  function showResult(data) {
    document.getElementById('encrypt-form')?.classList.add('d-none');
    document.getElementById('result')?.classList.remove('d-none');

    document.getElementById('downloadEncrypted').href = data.download_url || "#";
    document.getElementById('downloadMetadata').href = data.metadata_url || "#";
    document.getElementById('downloadQRImage').href = data.qr_code_url || "#";
    document.getElementById('shortlink').innerText = data.shortlink || "-";
    document.getElementById('qr-code').innerHTML = data.qr_html || "";

    const bar = document.getElementById('progress-bar');
    bar.classList.remove("bg-info");
    bar.classList.add("bg-success");
    document.getElementById('progress-text').innerText = "✅ Encryption Complete!";
    showToast("✅ File encrypted successfully!", "success");
  }

  // ===============================
  // 🔔 Toast Notifications
  // ===============================
  function showToast(message, type = "info") {
    const toast = document.getElementById("toast");
    const body = document.getElementById("toast-body");
    body.textContent = message;
    toast.className = `toast align-items-center text-white bg-${type} border-0 slide-in`;
    new bootstrap.Toast(toast, { delay: 4000 }).show();
  }

  // ===============================
  // 🛠️ Utility: Toggle Class
  // ===============================
  function toggleClass(el, className, show) {
    if (!el) return;
    el.classList[show ? 'remove' : 'add'](className);
  }
});
