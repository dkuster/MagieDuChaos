/*
  Choix du skin dans le navigateur, mémorisé dans localStorage (aucun cookie, rien n'est envoyé au serveur).
  Inséré en ligne dans <head> par _partials/head.html, avant toute feuille de style : il écrit le bon CSS
  avant le premier affichage, donc sans « flash » de l'autre skin. Sans JavaScript, le <noscript>
  qui suit charge le skin par défaut et le sélecteur reste caché.

  Mode « au hasard » (params.randomSkin = "option" ou "default") : la valeur mémorisée est "random",
  et un skin est tiré au sort à chaque page, différent de celui de la page précédente
  (retenu dans sessionStorage, le temps de l'onglet).
*/
(function () {
  // Clé du choix du visiteur. La changer « remet à zéro » tous les visiteurs sur le réglage du site
  // (defaultSkin / randomSkin) ; les anciennes clés sont alors listées dans OLD_KEYS et effacées.
  var KEY = "magieduchaos-apparence";
  var OLD_KEYS = ["magieduchaos-skin"];
  var LAST = "magieduchaos-skin-last";
  var RANDOM = "random";
  var script = document.currentScript;
  var skins = JSON.parse(script.getAttribute("data-skins"));
  var names = Object.keys(skins);
  var randomMode = script.getAttribute("data-random") || "off"; // off | option | default
  var randomOn = randomMode !== "off" && names.length > 1;
  var current = script.getAttribute("data-default");
  var mode = current; // nom du skin choisi, ou RANDOM
  var root = document.documentElement;
  var pending = null;

  function valid(v) {
    return !!v && (!!skins[v] || (v === RANDOM && randomOn));
  }

  function saved() {
    try {
      var v = localStorage.getItem(KEY);
      return valid(v) ? v : null;
    } catch (e) {
      return null; // stockage bloqué : on reste sur le défaut
    }
  }

  function remember(v) {
    try { localStorage.setItem(KEY, v); } catch (e) { /* choix valable pour cette page seulement */ }
  }

  // Skin au hasard, autre que « avoid » quand c'est possible.
  function pick(avoid) {
    var pool = names.filter(function (n) { return n !== avoid; });
    if (!pool.length) pool = names;
    return pool[Math.floor(Math.random() * pool.length)];
  }

  function lastShown() {
    try { return sessionStorage.getItem(LAST); } catch (e) { return null; }
  }

  function noteShown(name) {
    try { sessionStorage.setItem(LAST, name); } catch (e) { /* sans importance */ }
  }

  function setMeta(name, content) {
    var m = document.querySelector('meta[name="' + name + '"]');
    if (m && content) m.setAttribute("content", content);
  }

  function syncSelect() {
    var sel = document.getElementById("skin-select");
    if (sel) sel.value = mode;
  }

  try { OLD_KEYS.forEach(function (k) { localStorage.removeItem(k); }); } catch (e) { /* stockage bloqué */ }

  // 1. Premier affichage : CSS du skin mémorisé (ou tiré au sort), écrit directement dans <head>.
  mode = saved() || (randomMode === "default" && randomOn ? RANDOM : current);
  current = mode === RANDOM ? pick(lastShown()) : mode;
  noteShown(current);
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
  //    newMode : nom du skin, ou RANDOM ; en cas d'échec de chargement, tout revient à l'état précédent.
  function apply(name, newMode) {
    var previousMode = mode;
    mode = newMode;
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
      noteShown(name);
    };
    link.onerror = function () {
      if (pending !== link) return;
      pending = null;
      link.remove();
      current = previous;
      mode = previousMode;
      syncSelect();
    };
    document.head.appendChild(link);
  }

  document.addEventListener("DOMContentLoaded", function () {
    var box = document.getElementById("skin-switcher");
    var sel = document.getElementById("skin-select");
    if (!box || !sel) return;
    syncSelect();
    box.hidden = false;
    sel.addEventListener("change", function () {
      var v = sel.value;
      if (!valid(v)) return;
      // Passer en mode hasard change tout de suite de skin, pour que l'effet soit visible.
      apply(v === RANDOM ? pick(current) : v, v);
      remember(v);
    });
  });

  // Choix fait dans un autre onglet : en mode hasard, la page affichée garde son skin.
  window.addEventListener("storage", function (e) {
    if (e.key !== KEY || !valid(e.newValue)) return;
    if (e.newValue === RANDOM) mode = RANDOM;
    else apply(e.newValue, e.newValue);
    syncSelect();
  });

  // Page revenue du cache « précédent » du navigateur : on garde le skin déjà affiché en mode hasard.
  window.addEventListener("pageshow", function (e) {
    var v = e.persisted && saved();
    if (!v) return;
    if (v === RANDOM) { mode = RANDOM; noteShown(current); }
    else apply(v, v);
    syncSelect();
  });
})();
