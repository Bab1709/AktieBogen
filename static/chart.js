// Draws the price chart on the stock page as an SVG line with a hover tooltip.
(function () {
  const SVG = "http://www.w3.org/2000/svg";
  const HEIGHT = 340;
  const MARGIN = { top: 12, right: 12, bottom: 28, left: 64 };

  const container = document.getElementById("chart");
  const points = JSON.parse(document.getElementById("chart-data").textContent).map(([day, close]) => ({
    day: new Date(day + "T00:00:00"),
    close,
  }));
  const currency = container.dataset.currency;
  const years = (points[points.length - 1].day - points[0].day) / (365 * 24 * 60 * 60 * 1000);

  function amount(value) {
    return value.toLocaleString("da-DK", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function axisDate(day) {
    const options = years > 1 ? { month: "short", year: "numeric" } : { day: "numeric", month: "short" };
    return day.toLocaleDateString("da-DK", options);
  }

  function node(name, attributes, parent) {
    const element = document.createElementNS(SVG, name);
    for (const [key, value] of Object.entries(attributes)) element.setAttribute(key, value);
    parent.append(element);
    return element;
  }

  // Round the distance between gridlines to 1, 2 or 5 times a power of ten.
  function niceStep(span) {
    const rough = span / 4;
    const power = Math.pow(10, Math.floor(Math.log10(rough)));
    const step = [1, 2, 5, 10].find((multiple) => multiple * power >= rough);
    return step * power;
  }

  function draw() {
    const width = container.clientWidth - 32;
    const plotWidth = width - MARGIN.left - MARGIN.right;
    const plotHeight = HEIGHT - MARGIN.top - MARGIN.bottom;

    const closes = points.map((point) => point.close);
    let low = Math.min(...closes);
    let high = Math.max(...closes);
    const padding = (high - low) * 0.05 || high * 0.01 || 1;
    low -= padding;
    high += padding;

    const x = (index) => MARGIN.left + (index / (points.length - 1)) * plotWidth;
    const y = (value) => MARGIN.top + (1 - (value - low) / (high - low)) * plotHeight;

    container.replaceChildren();
    const svg = node(
      "svg",
      { viewBox: `0 0 ${width} ${HEIGHT}`, height: HEIGHT, role: "img", "aria-label": container.dataset.label },
      container
    );

    const step = niceStep(high - low);
    for (let value = Math.ceil(low / step) * step; value <= high; value += step) {
      node("line", { class: "grid", x1: MARGIN.left, x2: width - MARGIN.right, y1: y(value), y2: y(value) }, svg);
      const label = node("text", { x: MARGIN.left - 8, y: y(value), "text-anchor": "end", "dominant-baseline": "middle" }, svg);
      label.textContent = amount(value);
    }

    const labels = Math.max(2, Math.min(6, Math.floor(plotWidth / 110)));
    for (let i = 0; i < labels; i++) {
      const index = Math.round((i / (labels - 1)) * (points.length - 1));
      const anchor = i === 0 ? "start" : i === labels - 1 ? "end" : "middle";
      const label = node("text", { x: x(index), y: HEIGHT - 8, "text-anchor": anchor }, svg);
      label.textContent = axisDate(points[index].day);
    }

    const path = points.map((point, index) => `${index ? "L" : "M"}${x(index).toFixed(1)},${y(point.close).toFixed(1)}`).join("");
    const bottom = MARGIN.top + plotHeight;
    node("path", { class: "area", d: `${path}L${x(points.length - 1)},${bottom}L${x(0)},${bottom}Z` }, svg);
    node("path", { class: "line", d: path }, svg);

    const crosshair = node("line", { class: "crosshair", y1: MARGIN.top, y2: bottom, visibility: "hidden" }, svg);
    const dot = node("circle", { class: "dot", r: 5, visibility: "hidden" }, svg);
    const tip = document.createElement("div");
    tip.className = "chart-tip";
    tip.hidden = true;
    container.append(tip);

    function hide() {
      crosshair.setAttribute("visibility", "hidden");
      dot.setAttribute("visibility", "hidden");
      tip.hidden = true;
    }

    svg.addEventListener("pointermove", (event) => {
      const box = svg.getBoundingClientRect();
      const ratio = (event.clientX - box.left - MARGIN.left) / plotWidth;
      const index = Math.max(0, Math.min(points.length - 1, Math.round(ratio * (points.length - 1))));
      const point = points[index];
      crosshair.setAttribute("x1", x(index));
      crosshair.setAttribute("x2", x(index));
      crosshair.setAttribute("visibility", "visible");
      dot.setAttribute("cx", x(index));
      dot.setAttribute("cy", y(point.close));
      dot.setAttribute("visibility", "visible");

      const price = document.createElement("strong");
      price.textContent = `${amount(point.close)} ${currency}`;
      tip.replaceChildren(price, point.day.toLocaleDateString("da-DK", { day: "numeric", month: "short", year: "numeric" }));
      tip.hidden = false;
      // Keep the tooltip beside the crosshair, on whichever side has room.
      const left = 16 + x(index);
      const fitsRight = left + 12 + tip.offsetWidth <= container.clientWidth - 16;
      tip.style.left = (fitsRight ? left + 12 : left - 12 - tip.offsetWidth) + "px";
      tip.style.top = 16 + MARGIN.top + "px";
    });
    svg.addEventListener("pointerleave", hide);
  }

  draw();
  let lastWidth = container.clientWidth;
  window.addEventListener("resize", () => {
    if (container.clientWidth !== lastWidth) {
      lastWidth = container.clientWidth;
      draw();
    }
  });
})();
