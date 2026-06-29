/**
 * Aghahyar - Main JavaScript
 */

function toggleMenu() {
    var nav = document.getElementById('navLinks');
    nav.classList.toggle('show');
}

function closeMenu() {
    var nav = document.getElementById('navLinks');
    nav.classList.remove('show');
}

document.addEventListener('DOMContentLoaded', function () {
    var navLinks = document.getElementById('navLinks');
    if (navLinks) {
        navLinks.querySelectorAll('a').forEach(function (link) {
            link.addEventListener('click', closeMenu);
        });
    }

    var messageContainer = document.getElementById('message-container');
    if (messageContainer) {
        setTimeout(function () {
            var messages = messageContainer.querySelectorAll('.message-box');
            messages.forEach(function (msg) {
                msg.style.opacity = '0';
            });
            setTimeout(function () {
                messageContainer.style.display = 'none';
            }, 500);
        }, 2000);
    }

    updateThemeButton();
});

function toggleTheme() {
    var current = document.documentElement.getAttribute('data-theme');
    var next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
    updateThemeButton();
}

function updateThemeButton() {
    var btn = document.getElementById('themeToggle');
    if (btn) {
        var theme = document.documentElement.getAttribute('data-theme');
        btn.innerHTML = theme === 'dark' ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
        btn.setAttribute('aria-label', theme === 'dark' ? '\u062A\u0645 \u0631\u0648\u0632' : '\u062A\u0645 \u0634\u0628');
    }
}
