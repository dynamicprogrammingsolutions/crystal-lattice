(function () {
  function markdownPathname(pathname) {
    var path = pathname || "/";

    if (path.endsWith(".md")) {
      return path;
    }

    if (path.endsWith("/index.html")) {
      return path.slice(0, -"/index.html".length) + "/index.md";
    }

    if (path.endsWith(".html")) {
      return path.slice(0, -".html".length) + ".md";
    }

    if (!path.endsWith("/")) {
      path += "/";
    }

    return path + "index.md";
  }

  function markdownUrl() {
    return new URL(markdownPathname(window.location.pathname), window.location.origin);
  }

  function setStatus(root, message) {
    var label = root.querySelector("[data-cl-llm-actions-toggle] .cl-llm-actions__toggle-label");
    if (!label) {
      return;
    }

    var original = root.getAttribute("data-cl-original-label") || label.textContent;
    root.setAttribute("data-cl-original-label", original);
    label.textContent = message;

    window.clearTimeout(root.__clStatusTimer);
    root.__clStatusTimer = window.setTimeout(function () {
      label.textContent = original;
    }, 1800);
  }

  function closeMenu(root) {
    var toggle = root.querySelector("[data-cl-llm-actions-toggle]");
    var menu = root.querySelector("[data-cl-llm-actions-menu]");
    if (!toggle || !menu) {
      return;
    }

    menu.hidden = true;
    toggle.setAttribute("aria-expanded", "false");
    root.classList.remove("cl-llm-actions--open");
  }

  function openMenu(root) {
    var toggle = root.querySelector("[data-cl-llm-actions-toggle]");
    var menu = root.querySelector("[data-cl-llm-actions-menu]");
    if (!toggle || !menu) {
      return;
    }

    menu.hidden = false;
    toggle.setAttribute("aria-expanded", "true");
    root.classList.add("cl-llm-actions--open");
  }

  function getMarkdownText(root) {
    if (root.__clMarkdownText) {
      return Promise.resolve(root.__clMarkdownText);
    }

    if (root.__clMarkdownError) {
      return Promise.reject(root.__clMarkdownError);
    }

    if (!root.__clMarkdownPromise) {
      root.__clMarkdownPromise = fetch(markdownUrl().toString(), {
        headers: {
          Accept: "text/plain, text/markdown, */*"
        }
      })
        .then(function (response) {
          if (!response.ok) {
            throw new Error("Unable to load Markdown");
          }
          return response.text();
        })
        .then(function (text) {
          root.__clMarkdownText = text;
          return text;
        })
        .catch(function (error) {
          root.__clMarkdownError = error;
          throw error;
        });
    }

    return root.__clMarkdownPromise;
  }

  function preloadMarkdown(root) {
    getMarkdownText(root).catch(function (error) {
      console.warn("Crystal Lattice docs Markdown preload failed", error);
    });
  }

  function copyWithTextarea(text) {
    var textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.top = "-1000px";
    textarea.style.left = "-1000px";
    textarea.style.width = "1px";
    textarea.style.height = "1px";
    textarea.style.opacity = "0";
    document.body.appendChild(textarea);
    textarea.select();
    textarea.setSelectionRange(0, textarea.value.length);

    try {
      return document.execCommand("copy");
    } finally {
      document.body.removeChild(textarea);
    }
  }

  async function writeClipboard(text) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (error) {
      console.warn("Crystal Lattice docs clipboard API copy failed", error);
      return copyWithTextarea(text);
    }
  }

  async function copyMarkdown(root) {
    try {
      if (!root.__clMarkdownText) {
        setStatus(root, "Loading...");
        await getMarkdownText(root);
        setStatus(root, "Ready");
        return;
      }

      var copied = await writeClipboard(root.__clMarkdownText);
      if (!copied) {
        throw new Error("Clipboard copy was rejected");
      }
      setStatus(root, "Copied");
      closeMenu(root);
    } catch (error) {
      console.warn("Crystal Lattice docs copy failed", error);
      setStatus(root, "Copy failed");
    }
  }

  function setupRoot(root) {
    if (root.__clLlmActionsReady) {
      return;
    }
    root.__clLlmActionsReady = true;

    var toggle = root.querySelector("[data-cl-llm-actions-toggle]");
    var menu = root.querySelector("[data-cl-llm-actions-menu]");
    var copy = root.querySelector("[data-cl-llm-copy]");
    var markdown = root.querySelector("[data-cl-llm-markdown]");

    if (!toggle || !menu || !copy || !markdown) {
      return;
    }

    markdown.href = markdownUrl().toString();
    preloadMarkdown(root);

    toggle.addEventListener("click", function (event) {
      event.stopPropagation();
      if (menu.hidden) {
        openMenu(root);
        preloadMarkdown(root);
      } else {
        closeMenu(root);
      }
    });

    copy.addEventListener("click", function (event) {
      event.preventDefault();
      copyMarkdown(root);
    });

    menu.addEventListener("click", function () {
      closeMenu(root);
    });

    root.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        closeMenu(root);
        toggle.focus();
      }
    });
  }

  function setup() {
    document.querySelectorAll("[data-cl-llm-actions]").forEach(setupRoot);
  }

  document.addEventListener("click", function (event) {
    document.querySelectorAll("[data-cl-llm-actions]").forEach(function (root) {
      if (!root.contains(event.target)) {
        closeMenu(root);
      }
    });
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setup);
  } else {
    setup();
  }

  if (window.document$ && typeof window.document$.subscribe === "function") {
    window.document$.subscribe(setup);
  }
})();