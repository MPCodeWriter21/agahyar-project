(function () {
  "use strict";

  function initCustomSelects() {
    var selects = document.querySelectorAll("select");
    selects.forEach(function (select) {
      if (select.dataset.customSelect === "initialized") return;
      select.dataset.customSelect = "initialized";

      var isSearchable = select.dataset.searchable === "true";
      var apiUrl = select.dataset.apiUrl || "";
      var searchOnly = select.dataset.searchOnly === "true";

      var wrapper = document.createElement("div");
      wrapper.className = "custom-select-wrapper";

      var trigger = document.createElement("div");
      trigger.className = "custom-select-trigger";
      trigger.tabIndex = 0;
      trigger.setAttribute("role", "combobox");
      trigger.setAttribute("aria-haspopup", "listbox");
      trigger.setAttribute("aria-expanded", "false");

      var valueEl = document.createElement("span");
      valueEl.className = "custom-select-value";

      var arrowEl = document.createElement("span");
      arrowEl.className = "custom-select-arrow";

      trigger.appendChild(valueEl);
      trigger.appendChild(arrowEl);

      var dropdown = document.createElement("div");
      dropdown.className = "custom-select-dropdown";
      dropdown.setAttribute("role", "listbox");

      var searchContainer = null;
      var searchInput = null;
      var loadMoreBtn = null;
      var currentApiPage = 1;
      var isLoading = false;
      var searchDebounceTimer = null;

      if (isSearchable) {
        searchContainer = document.createElement("div");
        searchContainer.className = "custom-select-search";

        searchInput = document.createElement("input");
        searchInput.type = "text";
        searchInput.className = "custom-select-search-input";
        searchInput.placeholder = "\u062C\u0633\u062A\u062C\u0648...";
        searchInput.setAttribute("role", "searchbox");

        searchContainer.appendChild(searchInput);
        dropdown.appendChild(searchContainer);

        if (!searchOnly) {
          loadMoreBtn = document.createElement("div");
          loadMoreBtn.className = "custom-select-load-more";
          loadMoreBtn.textContent =
            "\u0646\u0645\u0627\u06CC\u0634 \u0628\u06CC\u0634\u062A\u0631";
          loadMoreBtn.setAttribute("role", "button");
        }
      }

      function buildOptions() {
        var searchVal = searchInput ? searchInput.value.trim() : "";
        if (isSearchable && searchVal) {
          return;
        }
        dropdown.innerHTML = "";
        if (searchContainer) {
          dropdown.appendChild(searchContainer);
        }
        var options = select.querySelectorAll("option");
        options.forEach(function (opt) {
          var optEl = document.createElement("div");
          optEl.className = "custom-select-option";
          if (opt.disabled) optEl.classList.add("disabled");
          if (opt.selected) optEl.classList.add("selected");
          optEl.dataset.value = opt.value;
          optEl.textContent = opt.label || opt.textContent;
          optEl.setAttribute("role", "option");
          optEl.setAttribute("aria-selected", opt.selected ? "true" : "false");
          dropdown.appendChild(optEl);
        });
        if (loadMoreBtn) {
          dropdown.appendChild(loadMoreBtn);
        }
        bindOptionEvents();
      }

      function bindOptionEvents() {
        dropdown
          .querySelectorAll(".custom-select-option")
          .forEach(function (opt) {
            opt.addEventListener("click", function (e) {
              e.stopPropagation();
              selectOption(this);
            });
          });
      }

      function appendApiOptions(cities, hasNext) {
        cities.forEach(function (city) {
          var existing = select.querySelector(
            'option[value="' + city.name + '"]',
          );
          if (!existing) {
            var opt = document.createElement("option");
            opt.value = city.name;
            opt.textContent = city.name;
            select.appendChild(opt);
          }

          var optEl = document.createElement("div");
          optEl.className = "custom-select-option";
          optEl.dataset.value = city.name;
          optEl.textContent = city.name;
          optEl.setAttribute("role", "option");
          optEl.setAttribute("aria-selected", "false");
          dropdown.appendChild(optEl);
        });

        if (loadMoreBtn) {
          if (hasNext) {
            if (!loadMoreBtn.parentNode) {
              dropdown.appendChild(loadMoreBtn);
            }
          } else {
            loadMoreBtn.remove();
          }
        }

        bindOptionEvents();
        updateValue();
      }

      function fetchCities(page, search) {
        if (isLoading || !apiUrl) return;
        isLoading = true;

        var url = apiUrl + "?page=" + page + "&per_page=20";
        if (search) {
          url += "&search=" + encodeURIComponent(search);
        }

        fetch(url, {
          method: "GET",
          headers: { Accept: "application/json" },
        })
          .then(function (response) {
            return response.json();
          })
          .then(function (data) {
            appendApiOptions(data.cities, data.has_next);
            currentApiPage = data.page || page;
            isLoading = false;
          })
          .catch(function () {
            isLoading = false;
          });
      }

      function clearSearchResults() {
        var opts = dropdown.querySelectorAll(".custom-select-option");
        opts.forEach(function (o) {
          o.remove();
        });
        if (loadMoreBtn) {
          loadMoreBtn.remove();
        }
      }

      function updateValue() {
        var selected = select.options[select.selectedIndex];
        valueEl.textContent = selected ? selected.textContent : "";
        var opts = dropdown.querySelectorAll(".custom-select-option");
        opts.forEach(function (o) {
          var isSel = o.dataset.value === select.value;
          o.classList.toggle("selected", isSel);
          o.setAttribute("aria-selected", isSel ? "true" : "false");
        });
      }

      function openDropdown() {
        dropdown.classList.add("open");
        trigger.classList.add("open");
        trigger.setAttribute("aria-expanded", "true");
        if (searchInput) {
          searchInput.value = "";
          if (isSearchable && apiUrl) {
            clearSearchResults();
            currentApiPage = 1;
            fetchCities(1, "");
          }
          setTimeout(function () {
            searchInput.focus();
          }, 0);
        } else {
          var selOpt = dropdown.querySelector(".custom-select-option.selected");
          if (selOpt) {
            selOpt.scrollIntoView({ block: "nearest" });
          }
        }
      }

      function closeDropdown() {
        dropdown.classList.remove("open");
        trigger.classList.remove("open");
        trigger.setAttribute("aria-expanded", "false");
        if (searchInput) {
          searchInput.value = "";
        }
      }

      function toggleDropdown() {
        if (dropdown.classList.contains("open")) {
          closeDropdown();
        } else {
          openDropdown();
        }
      }

      function selectOption(optEl) {
        if (!optEl || optEl.classList.contains("disabled")) return;
        var val = optEl.dataset.value;
        var existing = select.querySelector('option[value="' + val + '"]');
        if (!existing) {
          var opt = document.createElement("option");
          opt.value = val;
          opt.textContent = optEl.textContent;
          select.appendChild(opt);
        }
        select.value = val;
        updateValue();
        closeDropdown();
        select.dispatchEvent(new Event("change", { bubbles: true }));
        trigger.focus();
      }

      buildOptions();
      updateValue();

      wrapper.appendChild(trigger);
      wrapper.appendChild(dropdown);

      if (select.classList.contains("field-error")) {
        trigger.classList.add("field-error");
      }

      select.parentNode.insertBefore(wrapper, select);
      select.style.display = "none";

      trigger.addEventListener("click", function (e) {
        e.stopPropagation();
        toggleDropdown();
      });

      trigger.addEventListener("keydown", function (e) {
        var opts = dropdown.querySelectorAll(
          ".custom-select-option:not(.disabled)",
        );
        var current = dropdown.querySelector(".custom-select-option.selected");
        var idx = Array.prototype.indexOf.call(opts, current);

        switch (e.key) {
          case "ArrowDown":
            e.preventDefault();
            if (idx < opts.length - 1) {
              selectOption(opts[idx + 1]);
            }
            break;
          case "ArrowUp":
            e.preventDefault();
            if (idx > 0) {
              selectOption(opts[idx - 1]);
            }
            break;
          case "Enter":
          case " ":
            e.preventDefault();
            if (isSearchable && document.activeElement === searchInput) {
              return;
            }
            toggleDropdown();
            break;
          case "Escape":
            e.preventDefault();
            closeDropdown();
            break;
        }
      });

      document.addEventListener("click", function (e) {
        if (!wrapper.contains(e.target)) {
          closeDropdown();
        }
      });

      if (searchInput) {
        searchInput.addEventListener("click", function (e) {
          e.stopPropagation();
        });

        searchInput.addEventListener("input", function () {
          var query = searchInput.value.trim();
          clearTimeout(searchDebounceTimer);
          searchDebounceTimer = setTimeout(function () {
            clearSearchResults();
            currentApiPage = 1;
            if (apiUrl) {
              fetchCities(1, query);
            } else {
              var opts = select.querySelectorAll("option");
              var lowerQuery = query.toLowerCase();
              opts.forEach(function (opt) {
                if (opt.value === "") return;
                var label = (opt.label || opt.textContent || "").toLowerCase();
                if (!lowerQuery || label.indexOf(lowerQuery) !== -1) {
                  var optEl = document.createElement("div");
                  optEl.className = "custom-select-option";
                  optEl.dataset.value = opt.value;
                  optEl.textContent = opt.label || opt.textContent;
                  optEl.setAttribute("role", "option");
                  optEl.setAttribute("aria-selected", "false");
                  dropdown.appendChild(optEl);
                }
              });
              bindOptionEvents();
            }
          }, 300);
        });

        searchInput.addEventListener("keydown", function (e) {
          if (e.key === "Escape") {
            closeDropdown();
            trigger.focus();
          }
        });
      }

      if (loadMoreBtn) {
        loadMoreBtn.addEventListener("click", function (e) {
          e.stopPropagation();
          if (!isLoading) {
            currentApiPage++;
            fetchCities(
              currentApiPage,
              searchInput ? searchInput.value.trim() : "",
            );
          }
        });
      }

      select.addEventListener("change", function () {
        updateValue();
      });

      var observer = new MutationObserver(function () {
        buildOptions();
        updateValue();
      });
      observer.observe(select, { childList: true, subtree: true });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initCustomSelects);
  } else {
    initCustomSelects();
  }
})();
