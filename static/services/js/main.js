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
});
