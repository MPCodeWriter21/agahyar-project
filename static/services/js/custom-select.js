(function () {
    'use strict';

    function initCustomSelects() {
        var selects = document.querySelectorAll('select');
        selects.forEach(function (select) {
            if (select.dataset.customSelect === 'initialized') return;
            select.dataset.customSelect = 'initialized';

            var wrapper = document.createElement('div');
            wrapper.className = 'custom-select-wrapper';

            var trigger = document.createElement('div');
            trigger.className = 'custom-select-trigger';
            trigger.tabIndex = 0;
            trigger.setAttribute('role', 'combobox');
            trigger.setAttribute('aria-haspopup', 'listbox');
            trigger.setAttribute('aria-expanded', 'false');

            var valueEl = document.createElement('span');
            valueEl.className = 'custom-select-value';

            var arrowEl = document.createElement('span');
            arrowEl.className = 'custom-select-arrow';

            trigger.appendChild(valueEl);
            trigger.appendChild(arrowEl);

            var dropdown = document.createElement('div');
            dropdown.className = 'custom-select-dropdown';
            dropdown.setAttribute('role', 'listbox');

            function buildOptions() {
                dropdown.innerHTML = '';
                var options = select.querySelectorAll('option');
                options.forEach(function (opt) {
                    var optEl = document.createElement('div');
                    optEl.className = 'custom-select-option';
                    if (opt.disabled) optEl.classList.add('disabled');
                    if (opt.selected) optEl.classList.add('selected');
                    optEl.dataset.value = opt.value;
                    optEl.textContent = opt.label || opt.textContent;
                    optEl.setAttribute('role', 'option');
                    optEl.setAttribute('aria-selected', opt.selected ? 'true' : 'false');
                    dropdown.appendChild(optEl);
                });
            }

            function updateValue() {
                var selected = select.options[select.selectedIndex];
                valueEl.textContent = selected ? selected.textContent : '';
                var opts = dropdown.querySelectorAll('.custom-select-option');
                opts.forEach(function (o) {
                    var isSel = o.dataset.value === select.value;
                    o.classList.toggle('selected', isSel);
                    o.setAttribute('aria-selected', isSel ? 'true' : 'false');
                });
            }

            function openDropdown() {
                dropdown.classList.add('open');
                trigger.classList.add('open');
                trigger.setAttribute('aria-expanded', 'true');
                var selOpt = dropdown.querySelector('.custom-select-option.selected');
                if (selOpt) {
                    selOpt.scrollIntoView({ block: 'nearest' });
                }
            }

            function closeDropdown() {
                dropdown.classList.remove('open');
                trigger.classList.remove('open');
                trigger.setAttribute('aria-expanded', 'false');
            }

            function toggleDropdown() {
                if (dropdown.classList.contains('open')) {
                    closeDropdown();
                } else {
                    openDropdown();
                }
            }

            function selectOption(optEl) {
                if (!optEl || optEl.classList.contains('disabled')) return;
                select.value = optEl.dataset.value;
                updateValue();
                closeDropdown();
                select.dispatchEvent(new Event('change', { bubbles: true }));
                trigger.focus();
            }

            buildOptions();
            updateValue();

            wrapper.appendChild(trigger);
            wrapper.appendChild(dropdown);

            if (select.classList.contains('field-error')) {
                trigger.classList.add('field-error');
            }

            select.parentNode.insertBefore(wrapper, select);
            select.style.display = 'none';

            trigger.addEventListener('click', function (e) {
                e.stopPropagation();
                toggleDropdown();
            });

            dropdown.querySelectorAll('.custom-select-option').forEach(function (opt) {
                opt.addEventListener('click', function (e) {
                    e.stopPropagation();
                    selectOption(this);
                });
            });

            trigger.addEventListener('keydown', function (e) {
                var opts = dropdown.querySelectorAll('.custom-select-option:not(.disabled)');
                var current = dropdown.querySelector('.custom-select-option.selected');
                var idx = Array.prototype.indexOf.call(opts, current);

                switch (e.key) {
                    case 'ArrowDown':
                        e.preventDefault();
                        if (idx < opts.length - 1) {
                            selectOption(opts[idx + 1]);
                        }
                        break;
                    case 'ArrowUp':
                        e.preventDefault();
                        if (idx > 0) {
                            selectOption(opts[idx - 1]);
                        }
                        break;
                    case 'Enter':
                    case ' ':
                        e.preventDefault();
                        toggleDropdown();
                        break;
                    case 'Escape':
                        e.preventDefault();
                        closeDropdown();
                        break;
                }
            });

            document.addEventListener('click', function (e) {
                if (!wrapper.contains(e.target)) {
                    closeDropdown();
                }
            });

            select.addEventListener('change', function () {
                updateValue();
            });

            var observer = new MutationObserver(function () {
                buildOptions();
                updateValue();
            });
            observer.observe(select, { childList: true, subtree: true });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initCustomSelects);
    } else {
        initCustomSelects();
    }
})();
