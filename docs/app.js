'use strict';

// --- Language display names (BCP 47 prefix → label) ---

var LANG_NAMES = {
  ja: 'Japanese',
  zh: 'Chinese',
  ko: 'Korean',
  en: 'English',
};

function langGroup(tag) {
  if (!tag) return 'Other';
  return LANG_NAMES[tag.split('-')[0]] || tag;
}

// --- State ---

var manifest = [];
var deck = null;
var cards = [];
var cardIndex = 0;
var flashcardState = 'prompt'; // 'prompt' | 'reveal'
var score = { known: 0, total: 0 };
var ambientTimer = null;
var ambientPhase = 'front';
var wakeLock = null;
var activeFilter = 'all';
var fieldAssignment = {}; // field name → 'front' | 'back' | null
var ambientSpeed = 30; // seconds per phase in ambient mode

var SPEED_PRESETS = [
  { label: 'Fast', value: 5 },
  { label: 'Normal', value: 15 },
  { label: 'Slow', value: 30 },
  { label: 'Very Slow', value: 60 },
];

// --- DOM helpers ---

function $(sel) { return document.querySelector(sel); }
function $$(sel) { return document.querySelectorAll(sel); }

function show(id) {
  $$('.screen').forEach(function(s) { s.classList.remove('active'); });
  $(id).classList.add('active');
}

function escapeHtml(s) {
  if (!s) return '';
  var d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

// --- Deck loading ---

async function loadManifest() {
  var res = await fetch('./deck-manifest.json');
  manifest = await res.json();
  renderFilters();
  renderDeckGrid();
}

async function loadDeck(entry) {
  var res = await fetch('./data/' + entry.filename);
  deck = await res.json();
  cards = (deck.cards || []).filter(function(card) {
    return card.field_values.some(function(fv) {
      return fv.value && fv.value !== 'n/a';
    });
  });
}

// --- Deck picker (filters + tile grid) ---

function renderFilters() {
  var seen = {};
  manifest.forEach(function(entry) {
    var prefix = entry.source_language ? entry.source_language.split('-')[0] : 'other';
    seen[prefix] = (seen[prefix] || 0) + 1;
  });

  var el = $('#deck-filters');
  var html = '<button class="filter-chip active" data-lang="all">All</button>';
  // Sort groups by count descending so the largest language group is first
  Object.keys(seen).sort(function(a, b) { return seen[b] - seen[a]; }).forEach(function(prefix) {
    var label = LANG_NAMES[prefix] || prefix;
    html += '<button class="filter-chip" data-lang="' + escapeHtml(prefix) + '">'
      + escapeHtml(label) + '</button>';
  });
  el.innerHTML = html;

  el.querySelectorAll('.filter-chip').forEach(function(btn) {
    btn.addEventListener('click', function() {
      activeFilter = btn.dataset.lang;
      el.querySelectorAll('.filter-chip').forEach(function(c) { c.classList.remove('active'); });
      btn.classList.add('active');
      renderDeckGrid();
    });
  });
}

function renderDeckGrid() {
  var grid = $('#deck-grid');
  var filtered = manifest;
  if (activeFilter !== 'all') {
    filtered = manifest.filter(function(entry) {
      return entry.source_language && entry.source_language.split('-')[0] === activeFilter;
    });
  }

  var html = '';
  filtered.forEach(function(entry) {
    html += '<button class="deck-tile" data-id="' + escapeHtml(entry.id) + '">'
      + '<span class="deck-tile-name">' + escapeHtml(entry.name) + '</span>'
      + '<span class="deck-tile-count">' + entry.card_count + ' cards</span>'
      + '</button>';
  });
  grid.innerHTML = html;

  grid.querySelectorAll('.deck-tile').forEach(function(btn) {
    btn.addEventListener('click', function() { selectDeck(btn.dataset.id); });
  });
}

async function selectDeck(id) {
  var entry = manifest.find(function(e) { return e.id === id; });
  if (!entry) return;
  await loadDeck(entry);
  initFieldAssignment();
  $('#mode-deck-name').textContent = deck.name;
  $('#mode-deck-info').textContent = cards.length + ' cards';
  renderFieldConfig();
  renderAmbientSpeed();
  show('#screen-mode');
}

function renderAmbientSpeed() {
  var el = $('#ambient-speed');
  var html = '<div class="speed-title">Ambient speed</div><div class="speed-chips">';
  SPEED_PRESETS.forEach(function(p) {
    var cls = p.value === ambientSpeed ? 'speed-chip active' : 'speed-chip';
    html += '<button class="' + cls + '" data-value="' + p.value + '">'
      + escapeHtml(p.label) + '</button>';
  });
  html += '</div>';
  el.innerHTML = html;

  el.querySelectorAll('.speed-chip').forEach(function(btn) {
    btn.addEventListener('click', function() {
      ambientSpeed = parseInt(btn.dataset.value, 10);
      renderAmbientSpeed();
    });
  });
}

// --- Field assignment (front/back/hidden per field) ---

function initFieldAssignment() {
  fieldAssignment = {};
  var display = deck.default_display || {};
  (display.front || []).forEach(function(f) { fieldAssignment[f] = 'front'; });
  (display.back || []).forEach(function(f) { fieldAssignment[f] = 'back'; });
  (deck.field_definitions || []).forEach(function(fd) {
    if (!(fd.name in fieldAssignment)) fieldAssignment[fd.name] = null;
  });
}

function renderFieldConfig() {
  var el = $('#field-config');
  var sampleCard = cards.length > 0 ? cards[0] : null;

  var html = '<div class="field-config-title">Fields</div>';
  (deck.field_definitions || []).forEach(function(fd) {
    var assignment = fieldAssignment[fd.name];
    var sample = sampleCard ? getFieldValue(sampleCard, fd.name) : '';
    if (sample === 'n/a') sample = '';
    var stateLabel = assignment === 'front' ? 'Front'
      : assignment === 'back' ? 'Back' : 'Hidden';
    var stateClass = assignment || 'hidden';

    html += '<div class="field-config-item">'
      + '<div class="field-config-info">'
      + '<span class="field-config-label">' + escapeHtml(fd.label || fd.name) + '</span>'
      + (sample ? '<span class="field-config-sample">' + escapeHtml(sample) + '</span>' : '')
      + '</div>'
      + '<button class="field-config-toggle ' + stateClass
      + '" data-field="' + escapeHtml(fd.name) + '">' + stateLabel + '</button>'
      + '</div>';
  });
  el.innerHTML = html;

  el.querySelectorAll('.field-config-toggle').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var name = btn.dataset.field;
      var cur = fieldAssignment[name];
      fieldAssignment[name] = cur === 'front' ? 'back' : cur === 'back' ? null : 'front';
      renderFieldConfig();
    });
  });
}

// --- Card rendering helpers ---

function getFieldValue(card, name) {
  var fv = card.field_values.find(function(v) { return v.field === name; });
  return fv ? fv.value : null;
}

function getFaceFields(face) {
  if (face === 'both') {
    return getFaceFields('front').concat(getFaceFields('back'));
  }
  return (deck.field_definitions || [])
    .filter(function(fd) { return fieldAssignment[fd.name] === face; })
    .map(function(fd) { return fd.name; });
}

function renderFields(card, fieldNames, cssClass) {
  var values = fieldNames.map(function(name) {
    var val = getFieldValue(card, name);
    if (!val || val === 'n/a') return '';
    var fd = (deck.field_definitions || []).find(function(d) { return d.name === name; });
    var lang = fd ? (fd.language || '') : '';
    return '<div class="field-value" lang="' + escapeHtml(lang) + '">'
      + escapeHtml(val) + '</div>';
  }).filter(Boolean);

  if (values.length === 0) return '';
  return '<div class="field-group ' + cssClass + '">' + values.join('') + '</div>';
}

// --- Shuffle ---

function shuffleCards() {
  for (var i = cards.length - 1; i > 0; i--) {
    var j = Math.floor(Math.random() * (i + 1));
    var tmp = cards[i]; cards[i] = cards[j]; cards[j] = tmp;
  }
}

// --- Wake Lock (keep screen on in ambient mode) ---

async function requestWakeLock() {
  try {
    if ('wakeLock' in navigator) {
      wakeLock = await navigator.wakeLock.request('screen');
    }
  } catch (e) { /* ignore */ }
}

function releaseWakeLock() {
  if (wakeLock) { wakeLock.release(); wakeLock = null; }
}

// --- Ambient mode ---

function startAmbient() {
  cardIndex = 0;
  ambientPhase = 'front';
  shuffleCards();
  show('#screen-ambient');
  renderAmbientCard();
  scheduleAmbientTick();
  requestWakeLock();
}

function stopAmbient() {
  if (ambientTimer) { clearTimeout(ambientTimer); ambientTimer = null; }
  releaseWakeLock();
}

function scheduleAmbientTick() {
  if (ambientTimer) clearTimeout(ambientTimer);
  ambientTimer = setTimeout(ambientTick, ambientSpeed * 1000);
}

function ambientTick() {
  var mode = (deck.default_display || {}).cycle_mode || 'front_back';
  var phases = mode === 'front_back_both'
    ? ['front', 'back', 'both'] : ['front', 'back'];

  var idx = phases.indexOf(ambientPhase);
  if (idx < phases.length - 1) {
    ambientPhase = phases[idx + 1];
  } else {
    ambientPhase = 'front';
    cardIndex = (cardIndex + 1) % cards.length;
  }
  renderAmbientCard();
  scheduleAmbientTick();
}

function renderAmbientCard() {
  var card = cards[cardIndex];
  var el = $('#ambient-card');
  var html = '';
  if (ambientPhase === 'front' || ambientPhase === 'both') {
    html += renderFields(card, getFaceFields('front'), 'front');
  }
  if (ambientPhase === 'back' || ambientPhase === 'both') {
    html += renderFields(card, getFaceFields('back'), 'back');
  }
  // Fade out old content, swap, then fade back in.
  el.style.opacity = '0';
  setTimeout(function() {
    el.innerHTML = html;
    el.style.opacity = '1';
  }, 300);
}

// --- Flashcard mode ---

function startFlashcard() {
  cardIndex = 0;
  score = { known: 0, total: cards.length };
  flashcardState = 'prompt';
  shuffleCards();
  show('#screen-flashcard');
  renderFlashcard();
}

function renderFlashcard() {
  var card = cards[cardIndex];
  var el = $('#flashcard-card');
  var progress = $('#flashcard-progress');

  progress.textContent = (cardIndex + 1) + ' / ' + cards.length;

  if (flashcardState === 'prompt') {
    el.className = 'card-display';
    el.innerHTML = renderFields(card, getFaceFields('front'), 'front');
    $('#flashcard-actions').classList.remove('hidden');
    $('#flashcard-next').classList.add('hidden');
    $('#flashcard-hint').textContent = 'Space = Know \u00b7 Other key = Don\u2019t Know \u00b7 Esc = Exit';
  } else {
    el.className = 'card-display reveal';
    el.innerHTML =
      renderFields(card, getFaceFields('front'), 'front') +
      renderFields(card, getFaceFields('back'), 'back');
    $('#flashcard-actions').classList.add('hidden');
    $('#flashcard-next').classList.remove('hidden');
    $('#flashcard-hint').textContent = 'Any key to continue';
  }
}

function flashcardAnswer(known) {
  if (flashcardState !== 'prompt') return;
  if (known) score.known++;
  flashcardState = 'reveal';
  renderFlashcard();
}

function flashcardNext() {
  if (flashcardState !== 'reveal') return;
  cardIndex++;
  if (cardIndex >= cards.length) {
    showScore();
  } else {
    flashcardState = 'prompt';
    renderFlashcard();
  }
}

// --- Score screen ---

function showScore() {
  var pct = cards.length > 0 ? Math.round((score.known / score.total) * 100) : 0;
  var r = 65;
  var c = 2 * Math.PI * r;
  var offset = c - (pct / 100) * c;
  var color = pct >= 80 ? 'var(--know-color)' : pct >= 50 ? 'var(--back-color)' : '#c55';

  $('#score-ring').innerHTML =
    '<svg viewBox="0 0 160 160">' +
      '<circle cx="80" cy="80" r="' + r + '" fill="none" stroke="#222" stroke-width="8"/>' +
      '<circle cx="80" cy="80" r="' + r + '" fill="none" stroke="' + color + '" stroke-width="8"' +
        ' stroke-linecap="round" stroke-dasharray="' + c + '" stroke-dashoffset="' + offset + '"' +
        ' transform="rotate(-90 80 80)" style="transition:stroke-dashoffset 0.6s ease"/>' +
    '</svg>' +
    '<div class="score-pct" style="color:' + color + '">' + pct + '%</div>';

  $('#score-text').textContent = score.known + ' of ' + score.total + ' correct';
  show('#screen-score');
}

// --- Input ---

function setupInput() {
  document.addEventListener('keydown', function(e) {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    var active = document.querySelector('.screen.active');
    if (!active) return;

    if (active.id === 'screen-ambient') {
      stopAmbient();
      show('#screen-mode');
      e.preventDefault();
      return;
    }

    if (active.id === 'screen-flashcard') {
      if (e.key === 'Escape') { show('#screen-mode'); e.preventDefault(); return; }
      if (e.key === 'Tab') return;
      if (flashcardState === 'prompt') {
        flashcardAnswer(e.code === 'Space');
        e.preventDefault();
      } else if (flashcardState === 'reveal') {
        flashcardNext();
        e.preventDefault();
      }
    }

    if (active.id === 'screen-score' && e.key === 'Escape') {
      show('#screen-decks');
    }
  });

  $('#btn-back-decks').addEventListener('click', function() {
    stopAmbient();
    show('#screen-decks');
  });
  $('#btn-ambient').addEventListener('click', function() { startAmbient(); });
  $('#btn-flashcard').addEventListener('click', function() { startFlashcard(); });
  $('#btn-know').addEventListener('click', function() { flashcardAnswer(true); });
  $('#btn-dont-know').addEventListener('click', function() { flashcardAnswer(false); });
  $('#btn-next').addEventListener('click', function() { flashcardNext(); });
  $('#btn-replay').addEventListener('click', function() { startFlashcard(); });
  $('#btn-home').addEventListener('click', function() { show('#screen-decks'); });

  $('#screen-ambient').addEventListener('click', function() {
    stopAmbient();
    show('#screen-mode');
  });

  // Re-acquire wake lock when tab regains focus
  document.addEventListener('visibilitychange', function() {
    if (document.visibilityState === 'visible' && ambientTimer) {
      requestWakeLock();
    }
  });
}

// --- Service worker ---

function registerSW() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('./sw.js').catch(function() {});
  }
}

// --- Init ---

async function init() {
  registerSW();
  setupInput();
  await loadManifest();
}

init();
