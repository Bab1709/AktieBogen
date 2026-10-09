// Shows matching stocks under the search field while the user types.
(function () {
  const input = document.getElementById("ticker");
  const list = document.getElementById("suggestions");
  let timer = null;
  let request = null;
  let active = -1;

  function close() {
    list.hidden = true;
    list.replaceChildren();
    active = -1;
    input.setAttribute("aria-expanded", "false");
    input.removeAttribute("aria-activedescendant");
  }

  function open(children) {
    list.replaceChildren(...children);
    list.hidden = false;
    active = -1;
    input.setAttribute("aria-expanded", "true");
    input.removeAttribute("aria-activedescendant");
  }

  function message(text) {
    const item = document.createElement("li");
    item.className = "muted";
    item.textContent = text;
    return item;
  }

  function option(stock, index) {
    const item = document.createElement("li");
    item.id = "suggestion-" + index;
    item.setAttribute("role", "option");
    item.setAttribute("aria-selected", "false");
    item.dataset.symbol = stock.symbol;
    for (const [name, text] of [["symbol", stock.symbol], ["name", stock.name], ["exchange", stock.exchange]]) {
      const part = document.createElement("span");
      part.className = name;
      part.textContent = text;
      item.append(part);
    }
    return item;
  }

  function options() {
    return list.querySelectorAll("[role=option]");
  }

  function highlight(index) {
    const items = options();
    if (items.length === 0) return;
    active = (index + items.length) % items.length;
    items.forEach((item, i) => item.setAttribute("aria-selected", i === active ? "true" : "false"));
    input.setAttribute("aria-activedescendant", items[active].id);
    items[active].scrollIntoView({ block: "nearest" });
  }

  function choose(item) {
    input.value = item.dataset.symbol;
    close();
  }

  async function search(query) {
    if (request) request.abort();
    request = new AbortController();
    try {
      const response = await fetch(input.dataset.searchUrl + "?q=" + encodeURIComponent(query), {
        signal: request.signal,
      });
      const stocks = await response.json();
      if (!response.ok) {
        open([message(stocks.error || "Kunne ikke søge efter aktier lige nu.")]);
      } else if (stocks.length === 0) {
        open([message("Ingen aktier fundet.")]);
      } else {
        open(stocks.map(option));
      }
    } catch (error) {
      if (error.name !== "AbortError") open([message("Kunne ikke søge efter aktier lige nu.")]);
    }
  }

  input.addEventListener("input", () => {
    clearTimeout(timer);
    const query = input.value.trim();
    if (!query) {
      if (request) request.abort();
      close();
      return;
    }
    // Wait for a short pause in the typing before asking the server.
    timer = setTimeout(() => search(query), 200);
  });

  input.addEventListener("keydown", (event) => {
    if (list.hidden) return;
    if (event.key === "ArrowDown") {
      event.preventDefault();
      highlight(active + 1);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      highlight(active - 1);
    } else if (event.key === "Enter" && active >= 0) {
      event.preventDefault();
      choose(options()[active]);
    } else if (event.key === "Escape") {
      close();
    }
  });

  // mousedown instead of click, so the choice is made before the field loses focus.
  list.addEventListener("mousedown", (event) => {
    event.preventDefault();
    const item = event.target.closest("[role=option]");
    if (item) choose(item);
  });

  input.addEventListener("blur", () => {
    clearTimeout(timer);
    if (request) request.abort();
    close();
  });
})();
