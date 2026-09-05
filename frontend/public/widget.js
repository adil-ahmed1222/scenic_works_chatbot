/**
 * Scenic Works embeddable chat widget.
 * Usage: <script src="https://chat.adroitiame.com/widget.js"></script>
 */
(function () {
  if (window.__SCENIC_WORKS_WIDGET_LOADED__) return;
  window.__SCENIC_WORKS_WIDGET_LOADED__ = true;

  var script =
    document.currentScript ||
    document.querySelector('script[src*="widget.js"]');
  var origin = script
    ? script.src.replace(/\/widget\.js(?:\?.*)?$/, "")
    : "https://chat.adroitiame.com";
  var iframeSrc = origin + "/embed";

  var iframe = document.createElement("iframe");
  iframe.src = iframeSrc;
  iframe.title = "Scenic Works Assistant";
  iframe.allow = "autoplay; clipboard-write";
  iframe.setAttribute("aria-label", "Scenic Works chat widget");
  iframe.style.cssText = [
    "position:fixed",
    "bottom:0",
    "left:auto",
    "right:0",
    "width:96px",
    "height:96px",
    "border:0",
    "z-index:2147483647",
    "background:transparent",
    "color-scheme:normal",
    "max-width:100vw",
    "max-height:100vh",
  ].join(";");

  window.addEventListener("message", function (event) {
    if (event.origin !== origin) return;
    if (event.source !== iframe.contentWindow) return;
    if (!event.data || event.data.source !== "scenic-works-widget") return;
    iframe.style.left = "auto";
    iframe.style.right = "0";
    if (event.data.open) {
      var mobile = window.innerWidth < 640;
      iframe.style.width = mobile ? "100vw" : "min(540px, 100vw)";
      iframe.style.height = mobile ? "100vh" : "min(780px, 100vh)";
    } else {
      iframe.style.width = "96px";
      iframe.style.height = "96px";
    }
  });

  function mount() {
    document.body.appendChild(iframe);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mount);
  } else {
    mount();
  }
})();
