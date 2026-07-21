/* Admin tag list widget: add/remove/drag-reorder for separator-delimited lists */

(function () {
  "use strict";

  function syncHiddenInput(widget) {
    var hiddenInput = widget.querySelector('input[type="hidden"]');
    if (!hiddenInput) return;
    var sep = widget.getAttribute("data-separator") || "|";
    var inputs = widget.querySelectorAll(".tag-list-input");
    var values = [];
    for (var i = 0; i < inputs.length; i++) {
      var val = inputs[i].value.trim();
      if (val !== "") {
        values.push(val);
      }
    }
    hiddenInput.value = values.join(sep);
  }

  function createItemRow(value) {
    var div = document.createElement("div");
    div.className = "tag-list-item";

    var handle = document.createElement("span");
    handle.className = "tag-list-drag-handle";
    handle.title = "Drag to reorder";
    handle.innerHTML = "&#x2630;";
    div.appendChild(handle);

    var input = document.createElement("input");
    input.type = "text";
    input.className = "tag-list-input";
    input.value = value || "";
    div.appendChild(input);

    var removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.className = "tag-list-remove-btn";
    removeBtn.title = "Remove";
    removeBtn.innerHTML = "&times;";
    div.appendChild(removeBtn);

    return div;
  }

  function makeDraggable(widget, item) {
    var handle = item.querySelector(".tag-list-drag-handle");
    if (!handle) return;

    handle.setAttribute("draggable", "true");

    handle.addEventListener("dragstart", function (e) {
      item.classList.add("dragging");
      e.dataTransfer.effectAllowed = "move";
      e.dataTransfer.setData("text/plain", "");
      widget._dragItem = item;
    });

    handle.addEventListener("dragend", function () {
      item.classList.remove("dragging");
      widget._dragItem = null;
      var items = widget.querySelectorAll(".tag-list-item");
      for (var i = 0; i < items.length; i++) {
        items[i].classList.remove("drag-over");
      }
    });

    item.addEventListener("dragover", function (e) {
      e.preventDefault();
      e.dataTransfer.dropEffect = "move";
      if (widget._dragItem && widget._dragItem !== item) {
        item.classList.add("drag-over");
      }
    });

    item.addEventListener("dragleave", function () {
      item.classList.remove("drag-over");
    });

    item.addEventListener("drop", function (e) {
      e.preventDefault();
      item.classList.remove("drag-over");
      var dragged = widget._dragItem;
      if (!dragged || dragged === item) return;
      var itemsContainer = widget.querySelector(".tag-list-items");
      var allItems = itemsContainer.querySelectorAll(".tag-list-item");
      var draggedIdx = Array.prototype.indexOf.call(allItems, dragged);
      var targetIdx = Array.prototype.indexOf.call(allItems, item);
      if (draggedIdx < targetIdx) {
        itemsContainer.insertBefore(dragged, item.nextSibling);
      } else {
        itemsContainer.insertBefore(dragged, item);
      }
      syncHiddenInput(widget);
    });
  }

  function initWidget(widget) {
    if (widget._taglistInit) return;
    widget._taglistInit = true;

    var itemsContainer = widget.querySelector(".tag-list-items");
    var addBtn = widget.querySelector(".tag-list-add-btn");
    if (!itemsContainer || !addBtn) return;

    var items = itemsContainer.querySelectorAll(".tag-list-item");
    for (var i = 0; i < items.length; i++) {
      makeDraggable(widget, items[i]);
    }

    addBtn.addEventListener("click", function () {
      var newItem = createItemRow("");
      itemsContainer.appendChild(newItem);
      makeDraggable(widget, newItem);
      newItem.querySelector(".tag-list-input").focus();
      syncHiddenInput(widget);
    });

    itemsContainer.addEventListener("click", function (e) {
      if (e.target.classList.contains("tag-list-remove-btn")) {
        var item = e.target.closest(".tag-list-item");
        if (item) {
          item.remove();
          syncHiddenInput(widget);
        }
      }
    });

    itemsContainer.addEventListener("keydown", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        var target = e.target;
        if (target.classList.contains("tag-list-input")) {
          var newItem = createItemRow("");
          target.closest(".tag-list-item").after(newItem);
          makeDraggable(widget, newItem);
          newItem.querySelector(".tag-list-input").focus();
          syncHiddenInput(widget);
        }
      }
    });

    itemsContainer.addEventListener("input", function (e) {
      if (e.target.classList.contains("tag-list-input")) {
        syncHiddenInput(widget);
      }
    });
  }

  function initAll() {
    var widgets = document.querySelectorAll(".tag-list-widget");
    for (var i = 0; i < widgets.length; i++) {
      initWidget(widgets[i]);
    }
  }

  document.addEventListener("DOMContentLoaded", initAll);
})();
