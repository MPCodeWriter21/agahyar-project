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

document.addEventListener("click", function (e) {
  var reactionBtn = e.target.closest(".btn-reaction:not(.disabled)");
  if (reactionBtn) {
    var commentId = reactionBtn.getAttribute("data-comment-id");
    var value = parseInt(reactionBtn.getAttribute("data-value"), 10);
    if (!commentId) return;
    var csrfToken = getCsrfToken();
    if (!csrfToken) return;

    reactionBtn.disabled = true;
    fetch("/api/v1/comments/" + commentId + "/react/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
        "X-Requested-With": "XMLHttpRequest",
      },
      body: JSON.stringify({ value: value }),
    })
      .then(function (response) {
        if (response.status === 401) {
          window.location.href = "/auth/login/";
          return;
        }
        if (!response.ok) {
          reactionBtn.disabled = false;
          return response.json().then(function (err) {
            if (err.detail) showToast(err.detail, "error");
          });
        }
        return response.json();
      })
      .then(function (data) {
        if (!data) return;
        var likesEl = document.getElementById("likes-count-" + commentId);
        var dislikesEl = document.getElementById("dislikes-count-" + commentId);
        if (likesEl) likesEl.textContent = toPersianDigits(data.likes);
        if (dislikesEl) dislikesEl.textContent = toPersianDigits(data.dislikes);

        var parent = reactionBtn.closest(".comment-reactions");
        if (parent) {
          parent.querySelectorAll(".btn-reaction").forEach(function (btn) {
            btn.classList.remove("active");
          });
        }
        if (data.user_reaction) {
          var activeBtn = parent
            ? parent.querySelector('[data-value="' + data.user_reaction + '"]')
            : null;
          if (activeBtn) activeBtn.classList.add("active");
        }
        reactionBtn.disabled = false;
      })
      .catch(function () {
        reactionBtn.disabled = false;
      });
    return;
  }

  var btn = e.target.closest(".btn-bookmark-icon");
  if (!btn) {
    return;
  }
  var serviceId = btn.getAttribute("data-service-id");
  if (!serviceId) return;
  var csrfToken = getCsrfToken();
  if (!csrfToken) return;

  btn.disabled = true;
  fetch("/bookmark/" + serviceId + "/", {
    method: "POST",
    headers: {
      "X-CSRFToken": csrfToken,
      "X-Requested-With": "XMLHttpRequest",
    },
  })
    .then(function (response) {
      if (response.status === 401) {
        window.location.href = "/auth/login/";
        return;
      }
      return response.json();
    })
    .then(function (data) {
      if (!data) return;
      btn.setAttribute("data-bookmarked", data.bookmarked ? "true" : "false");
      var icon = btn.querySelector("i");
      if (data.bookmarked) {
        icon.classList.replace("far", "fas");
      } else {
        icon.classList.replace("fas", "far");
      }
      btn.title = data.bookmarked ? "حذف از نشانک‌ها" : "افزودن به نشانک‌ها";
      if (
        !data.bookmarked &&
        btn.closest(".service-card") &&
        window.location.pathname.indexOf("/bookmarks/") !== -1
      ) {
        var card = btn.closest(".service-card");
        if (card) {
          card.style.transition = "opacity 0.3s";
          card.style.opacity = "0";
          setTimeout(function () {
            card.remove();
            var grid = document.querySelector(".services-grid");
            if (grid && grid.children.length === 0) {
              var empty =
                '<div class="no-results">' +
                "<h3>نشانکی وجود ندارد</h3>" +
                "<p>شما هنوز هیچ خدمتی را نشانک نکرده‌اید.</p>" +
                '<a href="/services/" class="btn-back">مشاهده خدمات</a>' +
                "</div>";
              grid.insertAdjacentHTML("afterend", empty);
            }
          }, 300);
        }
      }
      btn.disabled = false;
    })
    .catch(function () {
      btn.disabled = false;
    });
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
    btn.setAttribute("aria-label", theme === "dark" ? "تم روز" : "تم شب");
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
  btn.textContent = "در حال بارگذاری...";

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
        btn.textContent = "نمایش نظرات بیشتر";
        btn.setAttribute("data-page", page + 1);
      } else {
        btn.remove();
      }
    })
    .catch(function () {
      btn.disabled = false;
      btn.textContent = "نمایش نظرات بیشتر";
    });
}

function loadMoreCenters(btn) {
  var serviceId = btn.getAttribute("data-service-id");
  var page = parseInt(btn.getAttribute("data-page"), 10);
  var listEl = document.getElementById("centers-list");

  btn.disabled = true;
  btn.textContent = "در حال بارگذاری...";

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
          nameLink.textContent = toPersianDigits(center.name);
          header.appendChild(nameLink);

          if (center.avg_rating) {
            var rating = document.createElement("span");
            rating.className = "center-item-rating";
            rating.innerHTML =
              '<i class="fas fa-star"></i> ' +
              toPersianDigits(center.avg_rating);
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
                  toPersianDigits(center.name) +
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
        btn.textContent = "نمایش مراکز بیشتر";
        btn.setAttribute("data-page", page + 1);
      } else {
        btn.remove();
      }
    })
    .catch(function () {
      btn.disabled = false;
      btn.textContent = "نمایش مراکز بیشتر";
    });
}

function suggestClosestCenter(btn) {
  var serviceId = btn.getAttribute("data-service-id");
  var resultDiv = document.getElementById("geolocate-result");

  if (!navigator.geolocation) {
    resultDiv.style.display = "block";
    resultDiv.textContent = "امکان دریافت موقعیت جغرافیائی وجود ندارد.";
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
              toPersianDigits(data.center.name) +
              "</strong><br>" +
              data.center.address +
              (data.center.phones && data.center.phones.length > 0
                ? '<br><a href="tel:' +
                  data.center.phones[0] +
                  '" class="center-phone-link">' +
                  toPersianDigits(data.center.phones[0]) +
                  "</a>"
                : "") +
              "<br>اطلاعات: " +
              toPersianDigits(data.center.distance_km) +
              " کیلومتر " +
              '<a href="/center/' +
              data.center.id +
              '/">جزئیات مرکز</a>';

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
                  "<b>" +
                    toPersianDigits(data.center.name) +
                    "</b><br>" +
                    data.center.address,
                )
                .openPopup();

              var bounds = L.latLngBounds([userLatLng, centerLatLng]);
              window.serviceMap.fitBounds(bounds, { padding: [50, 50] });
            }
          } else {
            resultDiv.style.display = "block";
            resultDiv.textContent = "مرکزی در موقعیت جغرافیای شما یافت نشد.";
          }
        })
        .catch(function () {
          btn.disabled = false;
          btn.innerHTML = originalHtml;
          resultDiv.style.display = "block";
          resultDiv.textContent = "خطا در دریافت موقعیت جغرافیایی رخ داد.";
        });
    },
    function () {
      btn.disabled = false;
      btn.innerHTML = originalHtml;
      resultDiv.style.display = "block";
      resultDiv.textContent =
        "امکان دریافت موقعیت جغرافیایی وجود ندارد یا خطا در دریافت آن رخ داده است.";
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
      errorEl.textContent = "لطفا دلیل گزارش را انتخاب کنید.";
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
          errorEl.textContent = result.data.error || "خطا";
          errorEl.style.display = "block";
        }
      }
    })
    .catch(function () {
      if (submitBtn) submitBtn.disabled = false;
      if (errorEl) {
        errorEl.textContent = "خطا در ارسال گزارش.";
        errorEl.style.display = "block";
      }
    });
}

function showToast(message, variant) {
  var toast = document.createElement("div");
  toast.className =
    "app-toast" + (variant === "error" ? " app-toast--error" : "");
  toast.textContent = message;
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

function showReportSuccess(message) {
  showToast(message || "گزارش شما ثبت شد.");
}
