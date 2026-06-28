/**
 * Aghahyar - Main JavaScript
 * Extracted from inline script blocks.
 */

function toggleMenu() {
    var nav = document.getElementById('navLinks');
    nav.classList.toggle('show');
}

document.addEventListener('DOMContentLoaded', function () {
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
