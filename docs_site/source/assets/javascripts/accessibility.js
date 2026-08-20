(function () {
  function enhanceToggle(label, input, closedLabel, openLabel) {
    if (!label || !input || label.__clAccessibilityReady) {
      return;
    }
    label.__clAccessibilityReady = true;
    label.setAttribute("role", "button");
    label.setAttribute("tabindex", "0");
    label.setAttribute("aria-controls", input.id);

    function update() {
      label.setAttribute("aria-expanded", input.checked ? "true" : "false");
      label.setAttribute("aria-label", input.checked ? openLabel : closedLabel);
    }

    label.addEventListener("keydown", function (event) {
      if (event.key !== "Enter" && event.key !== " ") {
        return;
      }
      event.preventDefault();
      event.stopPropagation();
    });
    label.addEventListener("keyup", function (event) {
      if (event.key !== "Enter" && event.key !== " ") {
        return;
      }
      event.preventDefault();
      event.stopPropagation();
      var currentInput = document.getElementById(label.htmlFor);
      if (!currentInput) {
        return;
      }
      currentInput.checked = !currentInput.checked;
      currentInput.dispatchEvent(new Event("change", { bubbles: true }));
    });
    input.addEventListener("change", update);
    update();
  }

  function enhanceAction(label, input, accessibleName) {
    if (!label || !input || label.__clAccessibilityReady) {
      return;
    }
    label.__clAccessibilityReady = true;
    label.setAttribute("role", "button");
    label.setAttribute("tabindex", "0");
    label.setAttribute("aria-controls", input.id);
    label.setAttribute("aria-label", accessibleName);

    label.addEventListener("keydown", function (event) {
      if (event.key !== "Enter" && event.key !== " ") {
        return;
      }
      event.preventDefault();
      event.stopPropagation();
    });
    label.addEventListener("keyup", function (event) {
      if (event.key !== "Enter" && event.key !== " ") {
        return;
      }
      event.preventDefault();
      event.stopPropagation();
      var currentInput = document.getElementById(label.htmlFor);
      if (currentInput) {
        currentInput.click();
      }
    });
  }

  function setup() {
    enhanceToggle(
      document.querySelector('.md-header label[for="__drawer"]'),
      document.getElementById("__drawer"),
      "Open navigation",
      "Close navigation"
    );
    enhanceToggle(
      document.querySelector('.md-header label[for="__search"]'),
      document.getElementById("__search"),
      "Open search",
      "Close search"
    );

    document
      .querySelectorAll('.md-header label[for^="__palette_"]')
      .forEach(function (label) {
        var input = document.getElementById(label.htmlFor);
        var accessibleName = input && input.getAttribute("aria-label");
        if (accessibleName) {
          enhanceAction(label, input, accessibleName);
        }
      });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setup);
  } else {
    setup();
  }

  if (window.document$ && typeof window.document$.subscribe === "function") {
    window.document$.subscribe(setup);
  }
})();