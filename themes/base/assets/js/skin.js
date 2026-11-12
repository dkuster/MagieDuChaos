/*
  Choix du skin dans le navigateur, mémorisé dans localStorage (aucun cookie, rien n'est envoyé au serveur).
  Inséré en ligne dans <head> par _partials/head.html, avant toute feuille de style : il écrit le bon CSS
  avant le premier affichage, donc sans « flash » de l'autre skin. Sans JavaScript, le <noscript>
  qui suit charge le skin par défaut et le sélecteur reste caché.
*/
(function () {
  var KEY = "magieduchaos-skin";
  var script = document.currentScript;
  var skins = JSON.parse(script.getAttribute("data-skins"));
  var current = script.getAttribute("data-default");
  var root = document.documentElement;
  var pending = null;

  function saved() {
    try {
      var v = localStorage.getItem(KEY);
      return v && skins[v] ? v : null;
    } catch (e) {
      return null; // stockage bloqué : on reste sur le défaut
    }
  }

  function setMeta(name, content) {
    var m = document.querySelector('meta[name="' + name + '"]');
    if (m && content) m.setAttribute("content", content);
  }

  function syncSelect() {
    var sel = document.getElementById("skin-select");
    if (sel) sel.value = current;
  }

  // 1. Premier affichage : CSS du skin mémorisé, écrit directement dans <head>.
  current = saved() || current;
  var s = skins[current];
  root.setAttribute("data-skin", current);
  var tags = '<meta name="color-scheme" content="' + s.colorscheme + '">';
  if (s.themecolor) tags += '<meta name="theme-color" content="' + s.themecolor + '">';
  s.preload.forEach(function (href) {
    tags += '<link rel="preload" href="' + href + '" as="font" type="font/woff2" crossorigin>';
  });
  tags += '<link rel="stylesheet" id="skin-css" href="' + s.href + '" integrity="' + s.integrity + '">';
  document.write(tags);

  // 2. Changement en cours de visite : le nouveau CSS remplace l'ancien une fois chargé.
  function apply(name) {
    var next = skins[name];
    if (!next || name === current) return;
    var previous = current;
    current = name;
    if (pending) pending.remove();
    var link = document.createElement("link");
    pending = link;
    link.rel = "stylesheet";
    link.integrity = next.integrity;
    link.href = next.href;
    link.onload = function () {
      if (pending !== link) return;
      pending = null;
      var old = document.getElementById("skin-css");
      if (old) old.remove();
      link.id = "skin-css";
      root.setAttribute("data-skin", name);
      setMeta("color-scheme", next.colorscheme);
      setMeta("theme-color", next.themecolor);
    };
    link.onerror = function () {
      if (pending !== link) return;
      pending = null;
      link.remove();
      current = previous;
      syncSelect();
    };
    document.head.appendChild(link);
  }

  document.addEventListener("DOMContentLoaded", function () {
    var box = document.getElementById("skin-switcher");
    var sel = document.getElementById("skin-select");
    if (!box || !sel) return;
    sel.value = current;
    box.hidden = false;
    sel.addEventListener("change", function () {
      apply(sel.value);
      try { localStorage.setItem(KEY, sel.value); } catch (e) { /* choix valable pour cette page seulement */ }
    });
  });

  // Choix fait dans un autre onglet, ou page revenue du cache « précédent » du navigateur.
  window.addEventListener("storage", function (e) {
    if (e.key === KEY && skins[e.newValue]) { apply(e.newValue); syncSelect(); }
  });
  window.addEventListener("pageshow", function (e) {
    var v = e.persisted && saved();
    if (v) { apply(v); syncSelect(); }
  });
})();
