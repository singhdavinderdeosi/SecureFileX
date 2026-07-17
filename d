{% load static %}
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{% block title %}SecureFileX{% endblock %}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">

  <!-- Favicons -->
  <link rel="icon" type="image/png" href="{% static 'img/favicon-96x96.png' %}" sizes="96x96" />
  <link rel="icon" type="image/svg+xml" href="{% static 'img/favicon.svg' %}" />
  <link rel="shortcut icon" href="{% static 'img/favicon.ico' %}" />
  <link rel="apple-touch-icon" sizes="180x180" href="{% static 'img/apple-touch-icon.png' %}" />
  <link rel="manifest" href="{% static 'site.webmanifest' %}" />
  <meta name="apple-mobile-web-app-title" content="SecureFileX" />

  <!-- External Libraries -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css" rel="stylesheet">

  <style>
    :root {
      --main-color: #00f0ff;
      --font-color: #ffffff;
      --btn-glow: 0 0 10px #00f0ff, 0 0 20px #00f0ff;
    }

    html, body {
      margin: 0;
      padding: 0;
      font-family: 'Segoe UI', sans-serif;
      background: linear-gradient(to bottom right, #0a0a0a, #111);
      color: var(--font-color);
      font-size: 1.05rem;
      scroll-behavior: smooth;
      overflow-x: hidden;
    }

    .btn-neon {
      background: transparent;
      border: 2px solid var(--main-color);
      color: var(--main-color);
      transition: all 0.3s ease;
    }

    .btn-neon:hover {
      background: var(--main-color);
      color: #000;
      box-shadow: var(--btn-glow);
    }

    .navbar {
      position: sticky;
      top: 0;
      z-index: 1000;
      width: 100%;
      background: transparent !important;
      transition: top 0.4s, backdrop-filter 0.4s;
    }

    .navbar.scrolled {
      backdrop-filter: blur(15px);
    }

    .navbar .navbar-brand {
      color: var(--main-color) !important;
      font-weight: bold;
      font-size: 1.4rem;
      animation: glowText 2s ease-in-out infinite alternate;
    }

    @keyframes glowText {
      from { text-shadow: 0 0 8px #00f0ff; }
      to { text-shadow: 0 0 20px #00f0ff; }
    }

    .nav-link {
      color: var(--main-color) !important;
      transition: all 0.3s;
    }

    .nav-link:hover {
      text-shadow: 0 0 5px var(--main-color);
      transform: scale(1.05);
    }

    .dropdown-menu {
      background: rgba(20, 20, 20, 0.95);
      border: 1px solid var(--main-color);
      border-radius: 10px;
      display: none;
      opacity: 0;
      transform: translateY(-10px);
      transition: opacity 0.4s ease, transform 0.3s ease;
    }

    .dropdown.show .dropdown-menu {
      display: block;
      opacity: 1;
      transform: translateY(0);
    }

    .dropdown-menu .dropdown-item {
      color: var(--font-color);
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .dropdown-menu .dropdown-item:hover {
      background-color: rgba(0, 240, 255, 0.1);
      color: var(--main-color);
    }

    main {
      padding-top: 90px;
      padding-bottom: 70px;
      animation: fadeInUp 0.7s ease;
      min-height: calc(100vh - 160px);
    }

    @keyframes fadeInUp {
      from { opacity: 0; transform: translateY(30px); }
      to { opacity: 1; transform: translateY(0); }
    }

    footer {
      position: sticky;
      bottom: 0;
      width: 100%;
      background-color: rgba(10, 10, 10, 0.4);
      backdrop-filter: blur(8px);
      color: #ccc;
      padding: 12px 0;
      border-top: 1px solid rgba(0, 255, 255, 0.1);
      text-align: center;
      z-index: 999;
    }
  </style>
</head>
<body>

<!-- Preloader -->
<div id="preloader" style="position:fixed;top:0;left:0;width:100%;height:100%;background:#000;z-index:2000;display:flex;align-items:center;justify-content:center;color:#00f0ff;font-size:2rem;">
  Loading SecureFileX...
</div>

<!-- Navbar -->
<nav class="navbar navbar-expand-lg">
  <div class="container-fluid">
    <a class="navbar-brand" href="{% url 'welcome' %}">SecureFileX</a>
    <button class="navbar-toggler text-white" type="button" onclick="this.classList.toggle('active'); document.getElementById('navbarNav').classList.toggle('show');">
      <i class="fa fa-bars"></i>
    </button>
    <div class="collapse navbar-collapse" id="navbarNav">
      <ul class="navbar-nav ms-auto align-items-center gap-2">
        <li class="nav-item"><a class="nav-link" href="{% url 'home' %}">Home</a></li>
        <li class="nav-item"><a class="nav-link" href="{% url 'about' %}">About</a></li>
        <li class="nav-item"><a class="nav-link" href="{% url 'docs' %}">Docs</a></li>

        {% if user.is_authenticated %}
        <li class="nav-item dropdown">
          <a class="nav-link dropdown-toggle" href="#" onclick="event.preventDefault(); this.parentElement.classList.toggle('show');">Tools</a>
          <ul class="dropdown-menu">
            <li><a class="dropdown-item" href="{% url 'encrypt_file' %}"><i class="fas fa-lock"></i> Encrypt</a></li>
            <li><a class="dropdown-item" href="{% url 'decrypt' %}"><i class="fas fa-unlock"></i> Decrypt</a></li>
            <li><a class="dropdown-item" href="{% url 'steganography' %}"><i class="fas fa-image"></i> Steganography</a></li>
            <li><a class="dropdown-item" href="{% url 'algo_comparison' %}"><i class="fas fa-chart-bar"></i> Algo Comparison</a></li>
            <li><a class="dropdown-item" href="{% url 'cyberchef_view' %}"><i class="fas fa-magic"></i> SecureX</a></li>
            <li><a class="dropdown-item" href="{% url 'share' %}"><i class="fas fa-share-alt"></i> File Sharing</a></li>
            <li><a class="dropdown-item" href="{% url 'result' %}"><i class="fas fa-list"></i> Results</a></li>
          </ul>
        </li>

        <li class="nav-item dropdown">
          <a class="nav-link dropdown-toggle" href="#" onclick="event.preventDefault(); this.parentElement.classList.toggle('show');">
            <i class="fa-solid fa-user-circle me-1"></i> {{ user.username|title }}
          </a>
          <ul class="dropdown-menu dropdown-menu-end">
            <li><a class="dropdown-item" href="{% url 'account' %}"><i class="fa fa-user me-2"></i>Profile</a></li>
            <li><a class="dropdown-item" href="{% url 'settings' %}"><i class="fa fa-gear me-2"></i>Settings</a></li>
            <li><hr class="dropdown-divider"></li>
            <li>
              <a class="dropdown-item text-danger" href="#" onclick="event.preventDefault(); document.getElementById('logout-form').submit();">
                <i class="fa fa-sign-out-alt me-2"></i>Logout
              </a>
              <form id="logout-form" action="{% url 'logout' %}" method="post" style="display: none;">{% csrf_token %}</form>
            </li>
          </ul>
        </li>
        {% else %}
        <li class="nav-item"><a class="nav-link" href="{% url 'login' %}">Login</a></li>
        <li class="nav-item"><a class="nav-link" href="{% url 'signup' %}">Sign Up</a></li>
        {% endif %}
      </ul>
    </div>
  </div>
</nav>

<main class="container">
  <div id="content">{% block content %}{% endblock %}</div>
</main>

<footer>
  <p>2025 <strong>SecureFileX</strong> | Built by GROUP_10 | <a href="mailto:you@example.com">Contact</a></p>
</footer>

<!-- Scripts -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script>
  window.addEventListener('scroll', () => {
    document.querySelector('.navbar').classList.toggle('scrolled', window.scrollY > 10);
  });
  window.addEventListener('load', () => {
    document.getElementById('preloader').style.display = 'none';
  });
</script>
</body>
</html>
