/**
 * Agahyar - Main JavaScript
 */

function toPersianDigits(str) {
  var persian = ["۰", "۱", "۲", "۳", "۴", "۵", "۶", "۷", "۸", "۹"];
  return String(str).replace(/\d/g, function (d) {
    return persian[parseInt(d)];
  });
}

function toggleMenu() {
  var nav = document.getElementById("navLinks");
  nav.classList.toggle("show");
}

function closeMenu() {
  var nav = document.getElementById("navLinks");
  nav.classList.remove("show");
}

document.addEventListener("DOMContentLoaded", function () {
  var navLinks = document.getElementById("navLinks");
  if (navLinks) {
    navLinks.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", closeMenu);
    });
  }

  updateThemeButton();
});

function toggleTheme() {
  var current = document.documentElement.getAttribute("data-theme");
  var next = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("theme", next);
  updateThemeButton();
}

function updateThemeButton() {
  var btn = document.getElementById("themeToggle");
  if (btn) {
    var theme = document.documentElement.getAttribute("data-theme");
    btn.innerHTML =
      theme === "dark"
        ? '<i class="fas fa-sun"></i>'
        : '<i class="fas fa-moon"></i>';
    btn.setAttribute(
      "aria-label",
      theme === "dark"
        ? "\u062A\u0645 \u0631\u0648\u0632"
        : "\u062A\u0645 \u0634\u0628",
    );
  }
}

function toggleReplyForm(commentId) {
  var form = document.getElementById("reply-form-" + commentId);
  if (form) {
    var isHidden = form.style.display === "none";
    form.style.display = isHidden ? "block" : "none";
  }
}

function toggleEditForm(commentId) {
  var textEl = document.getElementById("comment-text-" + commentId);
  var editForm = document.getElementById("comment-edit-form-" + commentId);
  if (!textEl || !editForm) return;
  var isHidden = editForm.style.display === "none";
  textEl.style.display = isHidden ? "none" : "block";
  editForm.style.display = isHidden ? "block" : "none";
}

function submitEdit(commentId) {
  var textarea = document.getElementById("comment-edit-textarea-" + commentId);
  if (!textarea) return;
  var text = textarea.value.trim();
  if (!text) return;

  var csrfToken = getCsrfToken();
  var editUrl = "/comment/" + commentId + "/edit/";

  fetch(editUrl, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      "X-CSRFToken": csrfToken,
    },
    body: "text=" + encodeURIComponent(text),
  })
    .then(function (response) {
      if (response.redirected) {
        window.location.reload();
        return;
      }
      return response.text();
    })
    .then(function () {
      window.location.reload();
    });
}

var _pendingDeleteId = null;

function showDeleteModal(commentId) {
  _pendingDeleteId = commentId;
  var modal = document.getElementById("delete-comment-modal");
  if (modal) modal.showModal();
}

function cancelDelete() {
  _pendingDeleteId = null;
  var modal = document.getElementById("delete-comment-modal");
  if (modal) modal.close();
}

function confirmDelete() {
  if (_pendingDeleteId === null) return;
  var commentId = _pendingDeleteId;
  _pendingDeleteId = null;

  var modal = document.getElementById("delete-comment-modal");
  if (modal) modal.close();

  var csrfToken = getCsrfToken();
  var deleteUrl = "/comment/" + commentId + "/delete/";

  fetch(deleteUrl, {
    method: "POST",
    headers: {
      "X-CSRFToken": csrfToken,
    },
  }).then(function () {
    window.location.reload();
  });
}

function getCsrfToken() {
  var inputEl = document.querySelector("[name=csrfmiddlewaretoken]");
  if (inputEl) return inputEl.value;
  var cookies = document.cookie.split(";");
  for (var i = 0; i < cookies.length; i++) {
    var cookie = cookies[i].trim();
    if (cookie.startsWith("csrftoken=")) {
      return cookie.substring("csrftoken=".length);
    }
  }
  return "";
}

function toggleReplies(commentId, btn) {
  var replies = document.getElementById("replies-" + commentId);
  if (!replies) return;
  var icon = btn.querySelector(".toggle-icon");
  if (replies.style.display === "none") {
    replies.style.display = "block";
    icon.classList.replace("fa-chevron-down", "fa-chevron-up");
  } else {
    replies.style.display = "none";
    icon.classList.replace("fa-chevron-up", "fa-chevron-down");
  }
}

function loadMoreComments(btn) {
  var target = btn.getAttribute("data-target");
  var targetId = btn.getAttribute("data-target-id");
  var page = parseInt(btn.getAttribute("data-page"), 10);
  var listEl = document.getElementById("comments-list");

  btn.disabled = true;
  btn.textContent =
    "\u062F\u0631 \u062D\u0627\u0644 \u0628\u0627\u0631\u06AF\u0630\u0627\u0631\u06CC...";

  fetch("/api/load-comments/" + target + "/" + targetId + "/?page=" + page, {
    method: "GET",
    headers: { Accept: "application/json" },
  })
    .then(function (response) {
      return response.json();
    })
    .then(function (data) {
      if (data.html) {
        listEl.insertAdjacentHTML("beforeend", data.html);
      }

      if (data.has_next) {
        btn.disabled = false;
        btn.textContent =
          "\u0646\u0645\u0627\u06CC\u0634 \u0646\u0638\u0631\u0627\u062A \u0628\u06CC\u0634\u062A\u0631";
        btn.setAttribute("data-page", page + 1);
      } else {
        btn.remove();
      }
    })
    .catch(function () {
      btn.disabled = false;
      btn.textContent =
        "\u0646\u0645\u0627\u06CC\u0634 \u0646\u0638\u0631\u0627\u062A \u0628\u06CC\u0634\u062A\u0631";
    });
}

function loadMoreCenters(btn) {
  var serviceId = btn.getAttribute("data-service-id");
  var page = parseInt(btn.getAttribute("data-page"), 10);
  var listEl = document.getElementById("centers-list");

  btn.disabled = true;
  btn.textContent =
    "\u062F\u0631 \u062D\u0627\u0644 \u0628\u0627\u0631\u06AF\u0630\u0627\u0631\u06CC...";

  fetch("/api/load-centers/" + serviceId + "/?page=" + page, {
    method: "GET",
    headers: { Accept: "application/json" },
  })
    .then(function (response) {
      return response.json();
    })
    .then(function (data) {
      if (data.centers && data.centers.length > 0) {
        var newBounds = [];
        data.centers.forEach(function (center) {
          var item = document.createElement("div");
          item.className = "center-item";
          item.setAttribute("data-center-id", center.id);

          var header = document.createElement("div");
          header.className = "center-item-header";

          var nameLink = document.createElement("a");
          nameLink.className = "center-item-name";
          nameLink.href = "/center/" + center.id + "/";
          nameLink.textContent = center.name;
          header.appendChild(nameLink);

          if (center.avg_rating) {
            var rating = document.createElement("span");
            rating.className = "center-item-rating";
            rating.innerHTML =
              '<i class="fas fa-star"></i> ' + center.avg_rating;
            header.appendChild(rating);
          }

          item.appendChild(header);

          var addr = document.createElement("div");
          addr.className = "center-item-address";
          addr.textContent = center.address;
          item.appendChild(addr);

          if (center.description) {
            var desc = document.createElement("div");
            desc.className = "center-item-description";
            desc.textContent = center.description;
            item.appendChild(desc);
          }

          if (center.phones && center.phones.length > 0) {
            var phone = document.createElement("div");
            phone.className = "center-item-phone";
            var phoneNum = center.phones[0].phone;
            phone.innerHTML =
              '<i class="fas fa-phone"></i> <a href="tel:' +
              phoneNum +
              '" class="center-phone-link">' +
              toPersianDigits(phoneNum) +
              "</a>";
            item.appendChild(phone);
          }

          listEl.appendChild(item);

          if (
            window.serviceMap &&
            center.lat !== undefined &&
            center.lng !== undefined
          ) {
            var phoneStr =
              center.phones && center.phones.length > 0
                ? center.phones[0].phone
                : "";
            var marker = L.marker([center.lat, center.lng])
              .addTo(window.serviceMap)
              .bindPopup(
                "<b>" +
                  center.name +
                  "</b><br>" +
                  center.address +
                  (phoneStr
                    ? '<br><a href="tel:' +
                      phoneStr +
                      '" class="center-phone-link">' +
                      toPersianDigits(phoneStr) +
                      "</a>"
                    : ""),
              );
            if (window.serviceMarkers) {
              window.serviceMarkers.push(marker);
            }
            newBounds.push(marker.getLatLng());
          }
        });

        if (newBounds.length > 0 && window.serviceMap) {
          var allBounds = L.latLngBounds(newBounds);
          window.serviceMap.fitBounds(allBounds, {
            padding: [30, 30],
            maxZoom: 15,
          });
        }
      }

      if (data.has_next) {
        btn.disabled = false;
        btn.textContent =
          "\u0646\u0645\u0627\u06CC\u0634 \u0645\u0631\u06A9\u0632\u0627\u0632 \u0628\u06CC\u0634\u062A\u0631";
        btn.setAttribute("data-page", page + 1);
      } else {
        btn.remove();
      }
    })
    .catch(function () {
      btn.disabled = false;
      btn.textContent =
        "\u0646\u0645\u0627\u06CC\u0634 \u0645\u0631\u06A9\u0632\u0627\u0632 \u0628\u06CC\u0634\u062A\u0631";
    });
}

function suggestClosestCenter(btn) {
  var serviceId = btn.getAttribute("data-service-id");
  var resultDiv = document.getElementById("geolocate-result");

  if (!navigator.geolocation) {
    resultDiv.style.display = "block";
    resultDiv.textContent =
      "\u0627\u0645\u06A9\u0627\u0646 \u062F\u0631\u06CC\u0627\u0641\u062A \u0645\u0648\u0642\u0639\u06CC\u062A \u062C\u063A\u0631\u0627\u0641\u06CC\u0627\u0626\u06CC \u0648\u062C\u0648\u062F \u0646\u062F\u0627\u0631\u062F.";
    return;
  }

  btn.disabled = true;
  var originalHtml = btn.innerHTML;
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

  navigator.geolocation.getCurrentPosition(
    function (position) {
      var lat = position.coords.latitude;
      var lng = position.coords.longitude;

      var csrfToken = document.querySelector("[name=csrfmiddlewaretoken]");
      if (!csrfToken) {
        var cookies = document.cookie.split(";");
        for (var i = 0; i < cookies.length; i++) {
          var cookie = cookies[i].trim();
          if (cookie.startsWith("csrftoken=")) {
            csrfToken = cookie.substring("csrftoken=".length);
            break;
          }
        }
      } else {
        csrfToken = csrfToken.value;
      }

      fetch("/api/suggest-center/" + serviceId + "/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({ lat: lat, lng: lng }),
      })
        .then(function (response) {
          return response.json();
        })
        .then(function (data) {
          btn.disabled = false;
          btn.innerHTML = originalHtml;

          if (data.center) {
            resultDiv.style.display = "block";
            resultDiv.innerHTML =
              "<strong>" +
              data.center.name +
              "</strong><br>" +
              data.center.address +
              (data.center.phones && data.center.phones.length > 0
                ? '<br><a href="tel:' +
                  data.center.phones[0] +
                  '" class="center-phone-link">' +
                  toPersianDigits(data.center.phones[0]) +
                  "</a>"
                : "") +
              "<br>\u0627\u0637\u0644\u0627\u0639\u0627\u062A: " +
              data.center.distance_km +
              " \u06A9\u06CC\u0644\u0648\u0645\u062A\u0631 " +
              '<a href="/center/' +
              data.center.id +
              '/">\u062C\u0632\u0626\u06CC\u0627\u062A \u0645\u0631\u06A9\u0632</a>';

            if (window.serviceMap) {
              if (window._geoCircle) {
                window.serviceMap.removeLayer(window._geoCircle);
              }
              if (window._geoMarker) {
                window.serviceMap.removeLayer(window._geoMarker);
              }

              var userLatLng = L.latLng(lat, lng);
              var centerLatLng = L.latLng(data.center.lat, data.center.lng);

              window._geoCircle = L.circle(userLatLng, {
                radius: 50,
                color: "#1a73e8",
                fillColor: "#4285f4",
                fillOpacity: 0.25,
                weight: 2,
              }).addTo(window.serviceMap);

              window._geoMarker = L.marker(centerLatLng)
                .addTo(window.serviceMap)
                .bindPopup(
                  "<b>" + data.center.name + "</b><br>" + data.center.address,
                )
                .openPopup();

              var bounds = L.latLngBounds([userLatLng, centerLatLng]);
              window.serviceMap.fitBounds(bounds, { padding: [50, 50] });
            }
          } else {
            resultDiv.style.display = "block";
            resultDiv.textContent =
              "\u0645\u0631\u06A9\u0632\u06CC \u062F\u0631 \u0645\u0648\u0642\u0639\u06CC\u062A \u062C\u063A\u0631\u0627\u0641\u06CC\u0627\u06CC \u0634\u0645\u0627 \u06CC\u0627\u0641\u062A \u0646\u0634\u062F.";
          }
        })
        .catch(function () {
          btn.disabled = false;
          btn.innerHTML = originalHtml;
          resultDiv.style.display = "block";
          resultDiv.textContent =
            "\u062E\u0637\u0627 \u062F\u0631 \u062F\u0631\u06CC\u0627\u0641\u062A \u0645\u0648\u0642\u0639\u06CC\u062A \u062C\u063A\u0631\u0627\u0641\u06CC\u0627\u06CC\u06CC \u0631\u062E \u062F\u0627\u062F.";
        });
    },
    function () {
      btn.disabled = false;
      btn.innerHTML = originalHtml;
      resultDiv.style.display = "block";
      resultDiv.textContent =
        "\u0627\u0645\u06A9\u0627\u0646 \u062F\u0631\u06CC\u0627\u0641\u062A \u0645\u0648\u0642\u0639\u06CC\u062A \u062C\u063A\u0631\u0627\u0641\u06CC\u0627\u06CC \u062C\u0648\u0627\u0628\u0632 \u0646\u0634\u062F \u06CC\u0627 \u062E\u0637\u0627 \u062F\u0631 \u062F\u0631\u06CC\u0627\u0641\u062A \u0622\u0646 \u0631\u062E \u062F\u0627\u062F\u0647 \u0627\u0633\u062A.";
    },
  );
}

var _reportTargetType = null;
var _reportTargetId = null;

function openReportDialog(targetType, targetId) {
  _reportTargetType = targetType;
  _reportTargetId = targetId;
  var errorEl = document.getElementById("report-error");
  if (errorEl) {
    errorEl.style.display = "none";
    errorEl.textContent = "";
  }
  var reasonEl = document.getElementById("report-reason");
  if (reasonEl) reasonEl.value = "";
  var descEl = document.getElementById("report-description");
  if (descEl) descEl.value = "";
  var dialog = document.getElementById("report-dialog");
  if (dialog) dialog.showModal();
}

function closeReportDialog() {
  _reportTargetType = null;
  _reportTargetId = null;
  var dialog = document.getElementById("report-dialog");
  if (dialog) dialog.close();
}

function submitReport() {
  var reasonEl = document.getElementById("report-reason");
  var descEl = document.getElementById("report-description");
  var errorEl = document.getElementById("report-error");

  if (!reasonEl || !reasonEl.value) {
    if (errorEl) {
      errorEl.textContent =
        "\u0644\u0637\u0641\u0627 \u062F\u0644\u06CC\u0644 \u06AF\u0632\u0627\u0631\u0634 \u0631\u0627 \u0627\u0646\u062A\u062E\u0627\u0628 \u06A9\u0646\u06CC\u062F.";
      errorEl.style.display = "block";
    }
    return;
  }

  var csrfToken = getCsrfToken();
  var reason = reasonEl.value;
  var description = descEl ? descEl.value : "";

  var submitBtn = document.querySelector(".btn-report-submit");
  if (submitBtn) submitBtn.disabled = true;

  fetch("/api/report/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken,
      "X-Requested-With": "XMLHttpRequest",
    },
    body: JSON.stringify({
      target_type: _reportTargetType,
      target_id: _reportTargetId,
      reason: reason,
      description: description,
    }),
  })
    .then(function (response) {
      return response.json().then(function (data) {
        return { status: response.status, data: data };
      });
    })
    .then(function (result) {
      if (submitBtn) submitBtn.disabled = false;

      if (result.status === 200) {
        closeReportDialog();
        showReportSuccess(result.data.message);
      } else {
        if (errorEl) {
          errorEl.textContent = result.data.error || "\u062E\u0637\u0627";
          errorEl.style.display = "block";
        }
      }
    })
    .catch(function () {
      if (submitBtn) submitBtn.disabled = false;
      if (errorEl) {
        errorEl.textContent =
          "\u062E\u0637\u0627 \u062F\u0631 \u0627\u0631\u0633\u0627\u0644 \u06AF\u0632\u0627\u0631\u0634.";
        errorEl.style.display = "block";
      }
    });
}

function showReportSuccess(message) {
  var toast = document.createElement("div");
  toast.className = "report-toast";
  toast.textContent =
    message ||
    "\u06AF\u0632\u0627\u0631\u0634 \u0634\u0645\u0627 \u062B\u0628\u062A \u0634\u062F.";
  document.body.appendChild(toast);
  setTimeout(function () {
    toast.classList.add("show");
  }, 10);
  setTimeout(function () {
    toast.classList.remove("show");
    setTimeout(function () {
      toast.remove();
    }, 300);
  }, 3000);
}
