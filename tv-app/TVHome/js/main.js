/* Customizable Apple TV style home screen for Samsung Tizen TVs.
 * Lists installed apps through tizen.application.getAppsInfo(), lets the user pin
 * favourites to a dock, launches them with tizen.application.launch(), and offers a
 * Settings screen for backgrounds, widgets and look. Outside a TV (plain browser)
 * it falls back to a demo app list for previewing. */
(function () {
  'use strict';

  var KEY = { LEFT: 37, UP: 38, RIGHT: 39, DOWN: 40, ENTER: 13, BACK: 10009, ESC: 27, BACKSPACE: 8 };
  var LONG_PRESS_MS = 650;
  var FAVS_KEY = 'tvhome.favs';
  var SETTINGS_KEY = 'tvhome.settings';
  var DEFAULT_NAMES = [/youtube/i, /netflix/i, /prime/i, /disney/i, /apple tv/i, /spotify/i, /plex/i, /crave/i];
  var CUSTOM = window.TVHOME_CUSTOM || { backgrounds: [] };

  var onTv = typeof window.tizen !== 'undefined';
  var allApps = [];      // [{id, name, icon}]
  var favs = [];         // [app id]
  var mode = 'home';     // home | menu | move | picker | settings
  var dockIndex = 0;
  var menuIndex = 0;
  var pickIndex = 0;
  var setIndex = 0;
  var enterDownAt = 0;
  var longTimer = null;
  var longFired = false;
  var slideTimer = null;
  var slideIndex = 0;
  var bgFront = 'bg-a';
  var onlinePhotos = []; // image URLs from CUSTOM.photoFeed

  var $ = function (id) { return document.getElementById(id); };

  // ---------- settings ----------

  function opt(v, label) { return { v: v, label: label }; }
  function onOff() { return [opt(true, 'On'), opt(false, 'Off')]; }

  var SETTINGS = [
    { key: 'background', label: 'Background', options: [opt('gradient', 'Color gradient')]
        .concat(CUSTOM.backgrounds.map(function (b, i) { return opt(i, b.name); }))
        .concat(CUSTOM.backgrounds.length > 1 ? [opt('slideshow', 'Slideshow (all)')] : [])
        .concat(CUSTOM.photoFeed ? [opt('online', 'My photos (from phone)')] : []) },
    { key: 'interval', label: 'Slideshow every', options: [opt(1, '1 min'), opt(5, '5 min'), opt(15, '15 min'), opt(60, '60 min')] },
    { key: 'dim', label: 'Darken background', options: [opt(0, 'None'), opt(0.4, 'Light'), opt(0.7, 'Medium'), opt(1, 'Strong')] },
    { key: 'clock', label: 'Clock', options: [opt('12', '12-hour'), opt('24', '24-hour'), opt('off', 'Off')] },
    { key: 'date', label: 'Date', options: onOff() },
    { key: 'greeting', label: 'Greeting', options: onOff() },
    { key: 'weather', label: 'Weather (' + (CUSTOM.city || 'location') + ')', options: onOff() },
    { key: 'tileSize', label: 'Tile size', options: [opt('s', 'Small'), opt('m', 'Medium'), opt('l', 'Large')] },
    { key: 'tileStyle', label: 'Tile style', options: [opt('color', 'Colorful'), opt('glass', 'Glass')] },
    { key: 'corners', label: 'Corners', options: [opt(22, 'Rounded'), opt(48, 'Extra round'), opt(4, 'Square')] },
    { key: 'accent', label: 'Highlight color', options: [opt('#ffffff', 'White'), opt('#0a84ff', 'Blue'),
        opt('#ff375f', 'Pink'), opt('#ffd60a', 'Gold'), opt('#30d158', 'Green')] },
    { key: 'dock', label: 'App row position', options: [opt('bottom', 'Bottom'), opt('center', 'Center')] },
    { key: 'hint', label: 'Remote hints', options: onOff() }
  ];

  var settings = {
    background: CUSTOM.backgrounds.length ? 0 : 'gradient', interval: 5, dim: 0.4, clock: '12',
    date: true, greeting: true, weather: true, tileSize: 'm', tileStyle: 'color', corners: 22,
    accent: '#ffffff', dock: 'bottom', hint: true
  };

  function loadSettings() {
    try {
      var saved = JSON.parse(localStorage.getItem(SETTINGS_KEY)) || {};
      for (var k in saved) if (settings.hasOwnProperty(k)) settings[k] = saved[k];
    } catch (e) { /* storage unavailable */ }
    // drop a saved background that no longer exists
    var bg = SETTINGS[0].options.map(function (o) { return o.v; });
    if (bg.indexOf(settings.background) < 0) settings.background = bg[0];
  }

  function saveSettings() {
    try { localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings)); } catch (e) { /* ignore */ }
  }

  function applySettings() {
    var root = document.documentElement.style;
    var size = { s: [240, 144], m: [300, 180], l: [380, 228] }[settings.tileSize];
    root.setProperty('--tile-w', size[0] + 'px');
    root.setProperty('--tile-h', size[1] + 'px');
    root.setProperty('--accent', settings.accent);
    root.setProperty('--radius', settings.corners + 'px');
    document.body.classList.toggle('glass', settings.tileStyle === 'glass');
    document.body.classList.toggle('dock-center', settings.dock === 'center');
    $('hint').classList.toggle('hidden', !settings.hint);
    $('greeting').classList.toggle('hidden', !settings.greeting);
    $('date').classList.toggle('hidden', !settings.date);
    $('clock').classList.toggle('hidden', settings.clock === 'off');
    $('weather').classList.toggle('hidden', !settings.weather);
    $('dim').style.opacity = settings.dim;
    applyBackground();
    updateClock();
    if (settings.weather) updateWeather();
    updateDockFocus();
  }

  // ---------- background ----------

  function showImage(file) {
    var back = bgFront === 'bg-a' ? 'bg-b' : 'bg-a';
    $(back).style.backgroundImage = 'url("' + file + '")';
    $(back).classList.add('show');
    $(bgFront).classList.remove('show');
    bgFront = back;
  }

  function hideImages() {
    $('bg-a').classList.remove('show');
    $('bg-b').classList.remove('show');
  }

  function slideshow(files) {
    if (!files.length) return hideImages();
    showImage(files[slideIndex % files.length]);
    if (files.length < 2) return;
    slideTimer = setInterval(function () {
      slideIndex = (slideIndex + 1) % files.length;
      showImage(files[slideIndex]);
    }, settings.interval * 60000);
  }

  function applyBackground() {
    clearInterval(slideTimer);
    var bg = settings.background;
    if (bg === 'gradient') {
      hideImages();
    } else if (bg === 'slideshow') {
      slideshow(CUSTOM.backgrounds.map(function (b) { return b.file; }));
    } else if (bg === 'online') {
      slideshow(onlinePhotos);
    } else {
      showImage(CUSTOM.backgrounds[bg].file);
    }
  }

  // Lists the images in a GitHub folder (public repo) so photos uploaded from a
  // phone show up without reinstalling the app.
  var photosLoadedAt = 0;
  function loadOnlinePhotos(force) {
    var f = CUSTOM.photoFeed;
    if (!f || (!force && Date.now() - photosLoadedAt < 30 * 60000)) return;
    photosLoadedAt = Date.now();
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'https://api.github.com/repos/' + f.owner + '/' + f.repo + '/contents/' +
      f.folder + '?ref=' + encodeURIComponent(f.branch) + '&t=' + Date.now());
    xhr.onload = function () {
      try {
        var urls = JSON.parse(xhr.responseText)
          .filter(function (x) { return x.type === 'file' && /\.(jpe?g|png|webp)$/i.test(x.name); })
          .sort(function (a, b) { return a.name.localeCompare(b.name); })
          .map(function (x) { return x.download_url; });
        var changed = urls.join() !== onlinePhotos.join();
        onlinePhotos = urls;
        if (changed && settings.background === 'online') applyBackground();
      } catch (e) { /* keep previous list */ }
    };
    xhr.send();
  }

  // ---------- data ----------

  function websiteApps() {
    return (CUSTOM.websites || []).map(function (w) {
      return { id: 'web:' + w.url, name: w.name, icon: '', url: w.url };
    });
  }

  function loadApps(done) {
    var finish = done;
    done = function () {
      allApps = websiteApps().concat(allApps);
      finish();
    };
    if (!onTv) {
      allApps = ['YouTube', 'Netflix', 'Prime Video', 'Disney+', 'Apple TV', 'Spotify', 'Plex',
        'Crave', 'Samsung TV Plus', 'Internet', 'Gallery', 'SmartThings']
        .map(function (n) { return { id: 'demo.' + n.replace(/\W/g, ''), name: n, icon: '' }; })
        .sort(function (a, b) { return a.name.localeCompare(b.name); });
      return done();
    }
    try {
      window.tizen.application.getAppsInfo(function (list) {
        var self = window.tizen.application.getCurrentApplication().appInfo.id;
        allApps = list
          .filter(function (a) { return a.show && a.id !== self && a.name; })
          .map(function (a) { return { id: a.id, name: a.name, icon: a.iconPath || '' }; })
          .sort(function (a, b) { return a.name.localeCompare(b.name); });
        done();
      }, function (err) {
        toast('Could not list apps: ' + err.name + ' ' + err.message);
        done();
      });
    } catch (e) {
      toast('Could not list apps: ' + e.message);
      done();
    }
  }

  function loadFavs() {
    try { favs = JSON.parse(localStorage.getItem(FAVS_KEY)) || []; } catch (e) { favs = []; }
    favs = favs.filter(function (id) { return findApp(id); });
    // put each configured website on the dock once, even when favourites already exist
    var seen = [];
    try { seen = JSON.parse(localStorage.getItem('tvhome.websitesAdded')) || []; } catch (e) { /* ignore */ }
    websiteApps().forEach(function (w) {
      if (seen.indexOf(w.id) < 0 && favs.indexOf(w.id) < 0) favs.unshift(w.id);
      if (seen.indexOf(w.id) < 0) seen.push(w.id);
    });
    try { localStorage.setItem('tvhome.websitesAdded', JSON.stringify(seen)); } catch (e) { /* ignore */ }
    if (favs.length <= websiteApps().length) {
      DEFAULT_NAMES.forEach(function (re) {
        var hit = allApps.filter(function (a) { return re.test(a.name); })[0];
        if (hit && favs.indexOf(hit.id) < 0) favs.push(hit.id);
      });
    }
  }

  function saveFavs() {
    try { localStorage.setItem(FAVS_KEY, JSON.stringify(favs)); } catch (e) { /* ignore */ }
  }

  function findApp(id) {
    for (var i = 0; i < allApps.length; i++) if (allApps[i].id === id) return allApps[i];
    return null;
  }

  // ---------- rendering ----------

  function hue(name) {
    var h = 0;
    for (var i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) % 360;
    return h;
  }

  function tileColor(name) {
    var h = hue(name);
    return 'linear-gradient(135deg, hsl(' + h + ',45%,32%), hsl(' + ((h + 40) % 360) + ',50%,18%))';
  }

  function makeTile(app) {
    var t = document.createElement('div');
    t.className = 'tile';
    t.style.background = tileColor(app.name);
    var letter = document.createElement('span');
    letter.className = 'letter';
    letter.textContent = app.name.charAt(0).toUpperCase();
    if (app.icon) {
      var img = document.createElement('img');
      img.src = app.icon.charAt(0) === '/' ? 'file://' + app.icon : app.icon;
      img.onerror = function () { img.parentNode.replaceChild(letter, img); };
      t.appendChild(img);
    } else {
      t.appendChild(letter);
    }
    return t;
  }

  function makeSymbolTile(symbol) {
    var t = document.createElement('div');
    t.className = 'tile add';
    t.innerHTML = '<span class="letter">' + symbol + '</span>';
    return t;
  }

  // Dock layout: favourites, then "+" (add apps), then gear (settings).
  function addIndex() { return favs.length; }
  function gearIndex() { return favs.length + 1; }

  function renderDock() {
    var dock = $('dock');
    dock.innerHTML = '';
    favs.forEach(function (id) { dock.appendChild(makeTile(findApp(id))); });
    dock.appendChild(makeSymbolTile('+'));
    // inline SVG gear: the TV's fonts may not include the U+2699 glyph
    dock.appendChild(makeSymbolTile('<svg viewBox="0 0 24 24" fill="none" ' +
      'stroke="#fff" stroke-width="2"><circle cx="12" cy="12" r="3.2"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3' +
      'M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1L7 17M17 7l2.1-2.1"/><circle cx="12" cy="12" r="7"/></svg>'));
    dockIndex = Math.min(dockIndex, gearIndex());
    updateDockFocus();
  }

  function updateDockFocus() {
    var tiles = $('dock').children;
    for (var i = 0; i < tiles.length; i++) {
      tiles[i].classList.toggle('focused', i === dockIndex && mode !== 'picker' && mode !== 'settings');
      tiles[i].classList.toggle('moving', i === dockIndex && mode === 'move');
    }
    var step = { s: 240, m: 300, l: 380 }[settings.tileSize] + 48;
    var visible = Math.floor(1680 / step);
    var shift = Math.max(0, dockIndex - (visible - 2)) * step;
    $('dock').style.transform = 'translateX(' + -shift + 'px)';

    var app = dockIndex < favs.length ? findApp(favs[dockIndex]) : null;
    $('hero-title').textContent = app ? app.name : dockIndex === addIndex() ? 'Add apps' : 'Customize';
    $('backdrop').style.background = app
      ? 'radial-gradient(ellipse at 30% 20%, hsl(' + hue(app.name) + ',35%,22%) 0%, #0b0b0f 60%, #000 100%)'
      : '';
  }

  function renderMenu() {
    var items = $('menu').querySelectorAll('.menu-item');
    for (var i = 0; i < items.length; i++) items[i].classList.toggle('focused', i === menuIndex);
  }

  function renderPicker() {
    var list = $('picker-list');
    list.innerHTML = '';
    var visible = 11;
    var start = Math.max(0, Math.min(pickIndex - 5, allApps.length - visible));
    allApps.slice(start, start + visible).forEach(function (app, i) {
      var row = document.createElement('div');
      row.className = 'pick';
      if (start + i === pickIndex) row.classList.add('focused');
      if (favs.indexOf(app.id) >= 0) row.classList.add('selected');
      row.innerHTML = '<span></span><span class="check">✓</span>';
      row.firstChild.textContent = app.name;
      list.appendChild(row);
    });
    if (!allApps.length) list.textContent = 'No apps found.';
  }

  function optionIndex(s) {
    for (var i = 0; i < s.options.length; i++) if (s.options[i].v === settings[s.key]) return i;
    return 0;
  }

  function renderSettings() {
    var list = $('settings-list');
    list.innerHTML = '';
    var visible = 10;
    var start = Math.max(0, Math.min(setIndex - 4, SETTINGS.length - visible));
    SETTINGS.slice(start, start + visible).forEach(function (s, i) {
      var row = document.createElement('div');
      row.className = 'setting' + (start + i === setIndex ? ' focused' : '');
      row.innerHTML = '<span></span><span class="value"></span>';
      row.firstChild.textContent = s.label;
      row.lastChild.textContent = s.options[optionIndex(s)].label;
      list.appendChild(row);
    });
  }

  function changeSetting(dir) {
    var s = SETTINGS[setIndex];
    var i = (optionIndex(s) + dir + s.options.length) % s.options.length;
    settings[s.key] = s.options[i].v;
    saveSettings();
    applySettings();
    renderSettings();
  }

  // ---------- widgets ----------

  var DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  var MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
    'September', 'October', 'November', 'December'];

  function updateClock() {
    var d = new Date();
    var m = ('0' + d.getMinutes()).slice(-2);
    $('clock').textContent = settings.clock === '24'
      ? ('0' + d.getHours()).slice(-2) + ':' + m
      : (d.getHours() % 12 || 12) + ':' + m;
    $('date').textContent = DAYS[d.getDay()] + ', ' + MONTHS[d.getMonth()] + ' ' + d.getDate();
    var h = d.getHours();
    var part = h < 5 ? 'Good night' : h < 12 ? 'Good morning' : h < 18 ? 'Good afternoon' : 'Good evening';
    $('greeting').textContent = part + (CUSTOM.name ? ', ' + CUSTOM.name : '');
  }

  // Open-Meteo weather codes, grouped (https://open-meteo.com/en/docs)
  function weatherText(code) {
    if (code === 0) return 'Clear';
    if (code <= 3) return 'Cloudy';
    if (code <= 48) return 'Fog';
    if (code <= 67) return 'Rain';
    if (code <= 77) return 'Snow';
    if (code <= 82) return 'Showers';
    if (code <= 86) return 'Snow showers';
    return 'Thunderstorm';
  }

  var weatherLoadedAt = 0;
  function updateWeather() {
    if (!settings.weather || CUSTOM.latitude === undefined) return;
    if (Date.now() - weatherLoadedAt < 25 * 60000) return;
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'https://api.open-meteo.com/v1/forecast?latitude=' + CUSTOM.latitude +
      '&longitude=' + CUSTOM.longitude + '&current=temperature_2m,weather_code');
    xhr.onload = function () {
      try {
        var c = JSON.parse(xhr.responseText).current;
        $('weather').textContent = Math.round(c.temperature_2m) + '°C  ' + weatherText(c.weather_code) +
          (CUSTOM.city ? ' · ' + CUSTOM.city : '');
        weatherLoadedAt = Date.now();
      } catch (e) { $('weather').textContent = ''; }
    };
    xhr.onerror = function () { $('weather').textContent = ''; };
    xhr.send();
  }

  function toast(msg) {
    var t = document.createElement('div');
    t.textContent = msg;
    t.style.cssText = 'position:absolute;left:50%;top:60px;transform:translateX(-50%);' +
      'background:rgba(60,60,66,.95);padding:20px 36px;border-radius:18px;font-size:30px;z-index:9';
    document.body.appendChild(t);
    setTimeout(function () { t.parentNode.removeChild(t); }, 5000);
  }

  // ---------- actions ----------

  // Opens a website in Samsung's Internet app (org.tizen.browser), falling back to
  // letting the TV pick the handler for the URL.
  function openUrl(app) {
    var control = new window.tizen.ApplicationControl('http://tizen.org/appcontrol/operation/view', app.url);
    var fail = function (err) { toast('Could not open ' + app.name + ': ' + (err.name || err.message)); };
    try {
      window.tizen.application.launchAppControl(control, 'org.tizen.browser', null, function () {
        window.tizen.application.launchAppControl(control, null, null, fail);
      });
    } catch (e) {
      fail(e);
    }
  }

  function launch(app) {
    if (!onTv) return toast('Would open ' + app.name + ' (' + (app.url || app.id) + ')');
    if (app.url) return openUrl(app);
    try {
      window.tizen.application.launch(app.id, null, function (err) {
        toast('Could not open ' + app.name + ': ' + err.name);
      });
    } catch (e) {
      toast('Could not open ' + app.name + ': ' + e.message);
    }
  }

  function setMode(m) {
    mode = m;
    $('menu').classList.toggle('hidden', m !== 'menu');
    $('picker').classList.toggle('hidden', m !== 'picker');
    $('settings').classList.toggle('hidden', m !== 'settings');
    if (m === 'menu') { menuIndex = 0; renderMenu(); }
    if (m === 'picker') { pickIndex = 0; renderPicker(); }
    if (m === 'settings') { setIndex = 0; renderSettings(); }
    updateDockFocus();
  }

  function openOptions() {
    if (dockIndex >= favs.length) return;
    $('menu-title').textContent = findApp(favs[dockIndex]).name;
    setMode('menu');
  }

  function activateDock() {
    if (dockIndex === addIndex()) setMode('picker');
    else if (dockIndex === gearIndex()) setMode('settings');
    else launch(findApp(favs[dockIndex]));
  }

  function exitApp() {
    if (onTv) {
      try { window.tizen.application.getCurrentApplication().exit(); } catch (e) { /* ignore */ }
    }
  }

  // ---------- keys ----------

  function isBack(k) { return k === KEY.BACK || k === KEY.ESC || k === KEY.BACKSPACE; }

  function onKeyDown(e) {
    var k = e.keyCode;
    if (k === KEY.ENTER) {
      e.preventDefault();
      if (enterDownAt) return; // auto-repeat while held
      enterDownAt = Date.now();
      longFired = false;
      if (mode === 'home') {
        longTimer = setTimeout(function () { longFired = true; openOptions(); }, LONG_PRESS_MS);
      }
      return;
    }

    if (mode === 'home') {
      if (k === KEY.LEFT && dockIndex > 0) dockIndex--;
      else if (k === KEY.RIGHT && dockIndex < gearIndex()) dockIndex++;
      else if (k === KEY.DOWN) return openOptions();
      else if (isBack(k)) return exitApp();
      updateDockFocus();
    } else if (mode === 'move') {
      var j = dockIndex + (k === KEY.LEFT ? -1 : k === KEY.RIGHT ? 1 : 0);
      if (j !== dockIndex && j >= 0 && j < favs.length) {
        var tmp = favs[j]; favs[j] = favs[dockIndex]; favs[dockIndex] = tmp;
        dockIndex = j;
        saveFavs();
        renderDock();
      } else if (isBack(k)) {
        setMode('home');
      }
    } else if (mode === 'menu') {
      if (k === KEY.UP && menuIndex > 0) menuIndex--;
      else if (k === KEY.DOWN && menuIndex < 2) menuIndex++;
      else if (isBack(k)) return setMode('home');
      renderMenu();
    } else if (mode === 'picker') {
      if (k === KEY.UP && pickIndex > 0) pickIndex--;
      else if (k === KEY.DOWN && pickIndex < allApps.length - 1) pickIndex++;
      else if (isBack(k)) { setMode('home'); return renderDock(); }
      renderPicker();
    } else if (mode === 'settings') {
      if (k === KEY.UP && setIndex > 0) setIndex--;
      else if (k === KEY.DOWN && setIndex < SETTINGS.length - 1) setIndex++;
      else if (k === KEY.LEFT) return changeSetting(-1);
      else if (k === KEY.RIGHT) return changeSetting(1);
      else if (isBack(k)) return setMode('home');
      renderSettings();
    }
  }

  function onKeyUp(e) {
    if (e.keyCode !== KEY.ENTER) return;
    clearTimeout(longTimer);
    enterDownAt = 0;
    if (longFired) { longFired = false; return; }

    if (mode === 'home') {
      activateDock();
    } else if (mode === 'move') {
      setMode('home');
    } else if (mode === 'menu') {
      if (menuIndex === 0) return setMode('move');
      if (menuIndex === 1) {
        favs.splice(dockIndex, 1);
        saveFavs();
      }
      setMode('home');
      renderDock();
    } else if (mode === 'picker') {
      var app = allApps[pickIndex];
      if (!app) return;
      var at = favs.indexOf(app.id);
      if (at >= 0) favs.splice(at, 1); else favs.push(app.id);
      saveFavs();
      renderPicker();
    } else if (mode === 'settings') {
      changeSetting(1);
    }
  }

  // ---------- start ----------

  window.addEventListener('load', function () {
    loadSettings();
    document.addEventListener('keydown', onKeyDown);
    document.addEventListener('keyup', onKeyUp);
    setInterval(function () { updateClock(); updateWeather(); loadOnlinePhotos(false); }, 10000);
    loadOnlinePhotos(true);
    loadApps(function () {
      loadFavs();
      renderDock();
      applySettings();
    });
  });
})();
