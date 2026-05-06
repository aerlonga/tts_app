<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TTS Studio — Dark Channel Pipeline</title>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Mono:ital,wght@0,300;0,400;0,500;1,300&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
/* ═══════════════════════════════════════════
   RESET & ROOT
═══════════════════════════════════════════ */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg:        #080A0C;
  --bg2:       #0E1014;
  --bg3:       #141720;
  --border:    #1E2330;
  --border2:   #2A3040;
  --amber:     #C8840A;
  --amber-dim: #7A4E05;
  --amber-glow:rgba(200,132,10,.12);
  --amber-soft:rgba(200,132,10,.06);
  --green:     #2DB87A;
  --green-dim: rgba(45,184,122,.1);
  --red:       #E0504A;
  --red-dim:   rgba(224,80,74,.1);
  --blue:      #4C8EF5;
  --blue-dim:  rgba(76,142,245,.1);
  --text:      #D4D8E2;
  --text2:     #8B92A8;
  --text3:     #505770;
  --mono:      'DM Mono', monospace;
  --sans:      'DM Sans', sans-serif;
  --display:   'Bebas Neue', sans-serif;
}

html { scroll-behavior: smooth; }

body {
  background: var(--bg);
  color: var(--text);
  font-family: var(--sans);
  min-height: 100vh;
  /* grain texture */
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.035'/%3E%3C/svg%3E");
}

/* ═══════════════════════════════════════════
   MASTHEAD
═══════════════════════════════════════════ */
.masthead {
  border-bottom: 1px solid var(--border);
  padding: 0 40px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 56px;
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(8,10,12,.92);
  backdrop-filter: blur(12px);
}

.masthead-logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-glyph {
  font-family: var(--display);
  font-size: 22px;
  color: var(--amber);
  letter-spacing: 2px;
  line-height: 1;
}

.logo-sub {
  font-family: var(--mono);
  font-size: 10px;
  color: var(--text3);
  letter-spacing: 2px;
  text-transform: uppercase;
  border-left: 1px solid var(--border2);
  padding-left: 12px;
}

/* Pipeline steps indicator */
.pipeline-nav {
  display: flex;
  align-items: center;
  gap: 0;
}

.pipe-step {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 16px;
  height: 56px;
  font-family: var(--mono);
  font-size: 11px;
  color: var(--text3);
  text-transform: uppercase;
  letter-spacing: 1px;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all .2s;
  text-decoration: none;
}

.pipe-step:hover { color: var(--text2); }

.pipe-step.active {
  color: var(--amber);
  border-bottom-color: var(--amber);
}

.pipe-step.done {
  color: var(--green);
  border-bottom-color: transparent;
}

.pipe-num {
  width: 20px; height: 20px;
  border-radius: 50%;
  border: 1px solid currentColor;
  display: grid; place-items: center;
  font-size: 10px;
  flex-shrink: 0;
}

.pipe-step.done .pipe-num {
  background: var(--green);
  border-color: var(--green);
  color: #000;
}

/* ═══════════════════════════════════════════
   API KEY BAR (always visible)
═══════════════════════════════════════════ */
.apibar {
  background: var(--bg2);
  border-bottom: 1px solid var(--border);
  padding: 10px 40px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.apibar label {
  font-family: var(--mono);
  font-size: 10px;
  color: var(--text3);
  letter-spacing: 1.5px;
  text-transform: uppercase;
  white-space: nowrap;
}

.apibar-input {
  flex: 1;
  max-width: 420px;
  background: var(--bg3);
  border: 1px solid var(--border2);
  border-radius: 4px;
  padding: 7px 12px;
  color: var(--text);
  font-family: var(--mono);
  font-size: 12px;
  outline: none;
  transition: border-color .2s;
}

.apibar-input:focus { border-color: var(--amber-dim); }

.eye-btn {
  background: none; border: none;
  color: var(--text3); cursor: pointer;
  font-size: 14px; padding: 0 4px;
  transition: color .2s;
}
.eye-btn:hover { color: var(--text); }

.api-status {
  font-family: var(--mono);
  font-size: 10px;
  color: var(--text3);
  margin-left: auto;
}

/* ═══════════════════════════════════════════
   MAIN LAYOUT
═══════════════════════════════════════════ */
.main {
  max-width: 960px;
  margin: 0 auto;
  padding: 48px 40px 120px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

/* ═══════════════════════════════════════════
   STAGE BLOCK
═══════════════════════════════════════════ */
.stage {
  border: 1px solid var(--border);
  border-radius: 2px;
  overflow: hidden;
  transition: border-color .3s;
}

.stage.active-stage { border-color: var(--border2); }
.stage.done-stage   { border-color: var(--border); }

.stage-header {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 20px 28px;
  background: var(--bg2);
  border-bottom: 1px solid var(--border);
  cursor: pointer;
  user-select: none;
}

.stage-number {
  font-family: var(--display);
  font-size: 52px;
  line-height: 1;
  color: var(--border2);
  flex-shrink: 0;
  transition: color .3s;
  width: 44px;
  text-align: center;
}

.active-stage .stage-number { color: var(--amber-dim); }
.done-stage   .stage-number { color: var(--border);    }

.stage-meta { flex: 1; }

.stage-title {
  font-family: var(--display);
  font-size: 22px;
  letter-spacing: 1.5px;
  color: var(--text2);
  transition: color .3s;
}

.active-stage .stage-title { color: var(--text); }

.stage-desc {
  font-family: var(--mono);
  font-size: 11px;
  color: var(--text3);
  margin-top: 3px;
  letter-spacing: .5px;
}

.stage-badge {
  font-family: var(--mono);
  font-size: 10px;
  padding: 4px 10px;
  border-radius: 2px;
  letter-spacing: 1px;
  text-transform: uppercase;
  border: 1px solid;
}

.badge-pending  { color: var(--text3);  border-color: var(--border2); }
.badge-active   { color: var(--amber);  border-color: var(--amber-dim); background: var(--amber-soft); }
.badge-done     { color: var(--green);  border-color: var(--green-dim); background: var(--green-dim); }
.badge-error    { color: var(--red);    border-color: var(--red-dim);   background: var(--red-dim); }

.stage-body {
  padding: 28px;
  background: var(--bg);
  display: none;
}

.active-stage .stage-body { display: block; }

/* ═══════════════════════════════════════════
   FORM ELEMENTS
═══════════════════════════════════════════ */
.field { margin-bottom: 20px; }

.field-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 7px;
}

.field-label span {
  font-family: var(--mono);
  font-size: 10px;
  color: var(--text3);
  text-transform: uppercase;
  letter-spacing: 1.2px;
}

.field-label small {
  font-family: var(--mono);
  font-size: 10px;
  color: var(--text3);
}

input[type="text"], input[type="url"], select, textarea {
  width: 100%;
  background: var(--bg2);
  border: 1px solid var(--border2);
  border-radius: 3px;
  padding: 11px 14px;
  color: var(--text);
  font-family: var(--mono);
  font-size: 13px;
  outline: none;
  transition: border-color .2s, background .2s;
}

input[type="text"]:focus,
input[type="url"]:focus,
select:focus,
textarea:focus {
  border-color: var(--amber-dim);
  background: var(--bg3);
}

select option { background: var(--bg2); }

textarea {
  font-family: var(--sans);
  font-size: 13.5px;
  line-height: 1.75;
  resize: vertical;
  min-height: 280px;
}

.url-row {
  display: flex;
  gap: 10px;
}
.url-row input { flex: 1; }

/* ═══════════════════════════════════════════
   BUTTONS
═══════════════════════════════════════════ */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 12px 24px;
  border: none;
  border-radius: 3px;
  font-family: var(--mono);
  font-size: 12px;
  letter-spacing: 1px;
  text-transform: uppercase;
  cursor: pointer;
  transition: all .2s;
}

.btn:disabled { opacity: .4; cursor: not-allowed; }

.btn-primary {
  background: var(--amber);
  color: #000;
}
.btn-primary:hover:not(:disabled) { background: #E09A1A; }

.btn-secondary {
  background: transparent;
  color: var(--amber);
  border: 1px solid var(--amber-dim);
}
.btn-secondary:hover:not(:disabled) { background: var(--amber-soft); }

.btn-ghost {
  background: transparent;
  color: var(--text2);
  border: 1px solid var(--border2);
}
.btn-ghost:hover:not(:disabled) { border-color: var(--text3); color: var(--text); }

.btn-green {
  background: var(--green);
  color: #000;
}
.btn-green:hover:not(:disabled) { background: #38D98F; }

.btn-sm {
  padding: 6px 12px;
  font-size: 10px;
}

/* Spinner */
.spin {
  width: 14px; height: 14px;
  border: 2px solid rgba(0,0,0,.2);
  border-top-color: #000;
  border-radius: 50%;
  animation: spin .6s linear infinite;
  display: none;
}
.btn-secondary .spin, .btn-ghost .spin {
  border-color: rgba(200,132,10,.2);
  border-top-color: var(--amber);
}
.btn-green .spin {
  border-color: rgba(0,0,0,.2);
  border-top-color: #000;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ═══════════════════════════════════════════
   STATUS / ALERT
═══════════════════════════════════════════ */
.alert {
  display: none;
  padding: 11px 14px;
  border-radius: 3px;
  font-family: var(--mono);
  font-size: 12px;
  margin-top: 14px;
  border-left: 3px solid;
  line-height: 1.5;
}
.alert.error   { background: var(--red-dim);   border-color: var(--red);   color: var(--red); }
.alert.success { background: var(--green-dim); border-color: var(--green); color: var(--green); }
.alert.loading { background: var(--amber-soft); border-color: var(--amber-dim); color: var(--amber); }
.alert.info    { background: var(--blue-dim);  border-color: var(--blue);  color: var(--blue); }
.alert.show    { display: block; }

/* ═══════════════════════════════════════════
   PROGRESS BAR
═══════════════════════════════════════════ */
.progress-wrap {
  display: none;
  margin-top: 16px;
}
.progress-wrap.show { display: block; }

.progress-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}

.progress-label {
  font-family: var(--mono);
  font-size: 11px;
  color: var(--text2);
}

.progress-pct {
  font-family: var(--mono);
  font-size: 11px;
  color: var(--amber);
}

.progress-track {
  height: 3px;
  background: var(--border2);
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--amber);
  border-radius: 2px;
  width: 0%;
  transition: width .4s ease;
  box-shadow: 0 0 8px var(--amber);
}

.progress-log {
  margin-top: 8px;
  font-family: var(--mono);
  font-size: 10px;
  color: var(--text3);
  font-style: italic;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* SSE Log lines */
.log-stream {
  display: none;
  margin-top: 12px;
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: 3px;
  padding: 12px 14px;
  max-height: 120px;
  overflow-y: auto;
  font-family: var(--mono);
  font-size: 11px;
  color: var(--text3);
  line-height: 1.8;
}
.log-stream.show { display: block; }
.log-line { animation: fadeIn .2s ease; }
.log-line.ok   { color: var(--green); }
.log-line.warn { color: var(--amber); }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

/* ═══════════════════════════════════════════
   IMAGE PROMPTS PANEL
═══════════════════════════════════════════ */
.prompts-panel {
  display: none;
  margin-top: 24px;
  border: 1px solid var(--border);
  border-radius: 3px;
  overflow: hidden;
}
.prompts-panel.show { display: block; }

.prompts-header {
  background: var(--bg2);
  padding: 10px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border);
}

.prompts-title {
  font-family: var(--mono);
  font-size: 10px;
  color: var(--text3);
  text-transform: uppercase;
  letter-spacing: 1.5px;
}

.prompts-list {
  padding: 4px 0;
  max-height: 260px;
  overflow-y: auto;
}

.prompt-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 16px;
  border-bottom: 1px solid var(--border);
  transition: background .15s;
}
.prompt-item:last-child { border-bottom: none; }
.prompt-item:hover { background: var(--bg2); }

.prompt-num {
  font-family: var(--display);
  font-size: 18px;
  color: var(--border2);
  flex-shrink: 0;
  line-height: 1.3;
  width: 24px;
  text-align: right;
}

.prompt-text {
  flex: 1;
  font-family: var(--mono);
  font-size: 11px;
  color: var(--text2);
  line-height: 1.6;
}

.copy-prompt-btn {
  background: none;
  border: 1px solid var(--border2);
  border-radius: 3px;
  padding: 3px 8px;
  font-family: var(--mono);
  font-size: 10px;
  color: var(--text3);
  cursor: pointer;
  white-space: nowrap;
  transition: all .15s;
  flex-shrink: 0;
}
.copy-prompt-btn:hover { border-color: var(--amber-dim); color: var(--amber); }
.copy-prompt-btn.copied { color: var(--green); border-color: var(--green-dim); }

/* ═══════════════════════════════════════════
   AUDIO / VIDEO RESULT
═══════════════════════════════════════════ */
.media-result {
  display: none;
  margin-top: 24px;
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: 3px;
  padding: 20px;
}
.media-result.show { display: block; }

.result-label {
  font-family: var(--mono);
  font-size: 10px;
  color: var(--green);
  text-transform: uppercase;
  letter-spacing: 1.5px;
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.result-label::before {
  content: '';
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--green);
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%,100% { opacity: 1; }
  50%      { opacity: .3; }
}

audio, video {
  width: 100%;
  border-radius: 3px;
  outline: none;
  margin-bottom: 14px;
  filter: saturate(.8);
}

.download-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border: 1px solid var(--green-dim);
  border-radius: 3px;
  color: var(--green);
  font-family: var(--mono);
  font-size: 11px;
  text-decoration: none;
  text-transform: uppercase;
  letter-spacing: 1px;
  transition: all .2s;
  cursor: pointer;
  background: none;
}
.download-link:hover { background: var(--green-dim); }

/* ═══════════════════════════════════════════
   FILE INPUT AREA
═══════════════════════════════════════════ */
.file-drop {
  border: 1px dashed var(--border2);
  border-radius: 3px;
  padding: 24px;
  text-align: center;
  cursor: pointer;
  transition: all .2s;
  position: relative;
}

.file-drop:hover, .file-drop.drag-over {
  border-color: var(--amber-dim);
  background: var(--amber-soft);
}

.file-drop input[type="file"] {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
  width: 100%;
  height: 100%;
  background: none;
  border: none;
  padding: 0;
}

.file-drop-label {
  font-family: var(--mono);
  font-size: 12px;
  color: var(--text3);
  pointer-events: none;
}

.file-drop-label strong {
  color: var(--amber);
  font-weight: 400;
}

/* Image preview strip */
.image-previews {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 12px;
  min-height: 0;
}

.thumb-wrap {
  position: relative;
  width: 64px;
  height: 64px;
  border-radius: 3px;
  overflow: hidden;
  border: 1px solid var(--border2);
  flex-shrink: 0;
}

.thumb-wrap img {
  width: 100%; height: 100%;
  object-fit: cover;
  display: block;
}

.thumb-num {
  position: absolute;
  bottom: 2px; left: 3px;
  font-family: var(--mono);
  font-size: 9px;
  color: rgba(255,255,255,.7);
  text-shadow: 0 1px 2px rgba(0,0,0,.8);
}

/* Row util */
.row { display: flex; gap: 12px; align-items: flex-end; flex-wrap: wrap; }
.row .field { flex: 1; margin-bottom: 0; }

/* Divider */
.divider {
  height: 1px;
  background: var(--border);
  margin: 24px 0;
}

/* Voice selector */
.voice-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 8px;
  margin-bottom: 20px;
}

.voice-option {
  padding: 10px 12px;
  border: 1px solid var(--border2);
  border-radius: 3px;
  cursor: pointer;
  transition: all .15s;
  background: var(--bg2);
}

.voice-option:hover { border-color: var(--amber-dim); }
.voice-option.selected { border-color: var(--amber); background: var(--amber-soft); }

.voice-name {
  font-family: var(--mono);
  font-size: 12px;
  color: var(--text);
  display: block;
}

.voice-desc {
  font-family: var(--mono);
  font-size: 10px;
  color: var(--text3);
  display: block;
  margin-top: 2px;
}

.voice-option.selected .voice-desc { color: var(--amber); }

/* Char counter */
.char-counter {
  text-align: right;
  font-family: var(--mono);
  font-size: 10px;
  color: var(--text3);
  margin-top: 6px;
}

/* Next step hint */
.next-hint {
  display: none;
  margin-top: 20px;
  padding: 12px 16px;
  background: var(--green-dim);
  border: 1px solid rgba(45,184,122,.2);
  border-radius: 3px;
  font-family: var(--mono);
  font-size: 11px;
  color: var(--green);
  cursor: pointer;
  transition: background .2s;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.next-hint:hover { background: rgba(45,184,122,.15); }
.next-hint span { opacity: .6; }

/* Scrollbar */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg2); }
::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--text3); }

/* ═══════════════════════════════════════════
   RESPONSIVE
═══════════════════════════════════════════ */
@media (max-width: 640px) {
  .masthead { padding: 0 16px; }
  .pipe-step span:not(.pipe-num) { display: none; }
  .apibar { padding: 10px 16px; }
  .main { padding: 24px 16px 80px; }
  .stage-body { padding: 20px 16px; }
  .stage-header { padding: 16px 20px; gap: 14px; }
  .stage-number { font-size: 38px; width: 32px; }
}
</style>
</head>
<body>

<!-- ═══ MASTHEAD ═══ -->
<header class="masthead">
  <div class="masthead-logo">
    <div class="logo-glyph">TTS</div>
    <div class="logo-sub">Dark Channel Pipeline</div>
  </div>
  <nav class="pipeline-nav">
    <a class="pipe-step active" id="nav-1" href="#stage1" onclick="scrollToStage(1)">
      <span class="pipe-num">1</span>
      <span>Roteiro</span>
    </a>
    <a class="pipe-step" id="nav-2" href="#stage2" onclick="scrollToStage(2)">
      <span class="pipe-num">2</span>
      <span>Áudio</span>
    </a>
    <a class="pipe-step" id="nav-3" href="#stage3" onclick="scrollToStage(3)">
      <span class="pipe-num">3</span>
      <span>Vídeo</span>
    </a>
  </nav>
</header>

<!-- ═══ API KEY BAR ═══ -->
<div class="apibar">
  <label>API Key</label>
  <input class="apibar-input" type="password" id="apiKey" placeholder="AIza..." autocomplete="off">
  <button class="eye-btn" onclick="toggleKey()">👁</button>
  <div class="api-status" id="apiStatus">Insira sua Gemini API Key</div>
</div>

<!-- ═══ MAIN ═══ -->
<main class="main">

  <!-- ─── STAGE 1: ROTEIRO ─── -->
  <section class="stage active-stage" id="stage1">
    <div class="stage-header" onclick="toggleStage(1)">
      <div class="stage-number">01</div>
      <div class="stage-meta">
        <div class="stage-title">PESQUISA &amp; ROTEIRO</div>
        <div class="stage-desc">Extrai conteúdo de URL · Roteiriza com Gemini · Gera prompts de imagem</div>
      </div>
      <div class="stage-badge badge-active" id="badge-1">ATIVO</div>
    </div>
    <div class="stage-body">

      <!-- URL input -->
      <div class="field">
        <div class="field-label">
          <span>URL do Artigo</span>
          <small>Wikipedia, blog, notícia...</small>
        </div>
        <div class="url-row">
          <input type="url" id="sourceUrl" placeholder="https://en.wikipedia.org/wiki/...">
          <button class="btn btn-primary" id="scriptifyBtn" onclick="runScriptify()">
            <div class="spin" id="scriptifySpin"></div>
            Roteirizar
          </button>
        </div>
      </div>

      <div class="alert" id="scriptifyAlert"></div>

      <!-- Script textarea -->
      <div class="field" id="scriptField" style="display:none;">
        <div class="divider"></div>
        <div class="field-label">
          <span>Roteiro Gerado</span>
          <small id="scriptInfo"></small>
        </div>
        <textarea id="scriptText" rows="16" placeholder="O roteiro aparecerá aqui..."></textarea>
        <div class="char-counter"><span id="charCount">0</span> caracteres</div>
      </div>

      <!-- Image prompts -->
      <div class="prompts-panel" id="promptsPanel">
        <div class="prompts-header">
          <span class="prompts-title">Prompts de Imagem · <span id="promptCount">0</span> gerados</span>
          <button class="btn btn-ghost btn-sm" onclick="copyAllPrompts()">Copiar todos</button>
        </div>
        <div class="prompts-list" id="promptsList"></div>
      </div>

      <!-- Next step hint -->
      <div id="hint1" style="display:none; margin-top:20px;">
        <button class="next-hint" onclick="activateStage(2)">
          ✓ Roteiro pronto — avançar para Geração de Áudio
          <span>→</span>
        </button>
      </div>

    </div>
  </section>

  <!-- ─── STAGE 2: ÁUDIO ─── -->
  <section class="stage" id="stage2">
    <div class="stage-header" onclick="toggleStage(2)">
      <div class="stage-number">02</div>
      <div class="stage-meta">
        <div class="stage-title">GERAÇÃO DE ÁUDIO</div>
        <div class="stage-desc">TTS Gemini Flash · Chunking automático · Stream de progresso</div>
      </div>
      <div class="stage-badge badge-pending" id="badge-2">AGUARDANDO</div>
    </div>
    <div class="stage-body">

      <!-- Voice selector -->
      <div class="field">
        <div class="field-label"><span>Voz</span></div>
        <div class="voice-grid" id="voiceGrid">
          <!-- populated by JS -->
        </div>
      </div>

      <!-- Roteiro para TTS (pode editar) -->
      <div class="field">
        <div class="field-label">
          <span>Roteiro para narrar</span>
          <small id="ttsCharCount">0 caracteres</small>
        </div>
        <textarea id="ttsText" rows="8" placeholder="Cole aqui o roteiro ou use o gerado na Etapa 1..."
                  oninput="updateTtsCount()"></textarea>
      </div>

      <button class="btn btn-primary" id="ttsBtn" onclick="runTTS()">
        <div class="spin" id="ttsSpin" style="border-color:rgba(0,0,0,.2); border-top-color:#000;"></div>
        🎙 Gerar Áudio Longo
      </button>

      <!-- Progress -->
      <div class="progress-wrap" id="ttsProgress">
        <div class="progress-header">
          <span class="progress-label" id="progressLabel">Iniciando...</span>
          <span class="progress-pct" id="progressPct">0%</span>
        </div>
        <div class="progress-track">
          <div class="progress-fill" id="progressFill"></div>
        </div>
        <div class="progress-log" id="progressLog"></div>
      </div>

      <div class="log-stream" id="ttsLog"></div>

      <div class="alert" id="ttsAlert"></div>

      <!-- Audio result -->
      <div class="media-result" id="audioResult">
        <div class="result-label">Áudio Gerado</div>
        <audio id="audioPlayer" controls></audio>
        <a class="download-link" id="audioDownload" download="narration.wav">
          ⬇ &nbsp;Baixar WAV
        </a>
      </div>

      <div id="hint2" style="display:none; margin-top:20px;">
        <button class="next-hint" onclick="activateStage(3)">
          ✓ Áudio pronto — avançar para Montagem de Vídeo
          <span>→</span>
        </button>
      </div>

    </div>
  </section>

  <!-- ─── STAGE 3: VÍDEO ─── -->
  <section class="stage" id="stage3">
    <div class="stage-header" onclick="toggleStage(3)">
      <div class="stage-number">03</div>
      <div class="stage-meta">
        <div class="stage-title">MONTAGEM DE VÍDEO</div>
        <div class="stage-desc">FFmpeg local · Slideshow com crossfade · Export MP4 1080p</div>
      </div>
      <div class="stage-badge badge-pending" id="badge-3">AGUARDANDO</div>
    </div>
    <div class="stage-body">

      <div class="row" style="margin-bottom:20px; align-items:flex-start;">

        <!-- Audio file -->
        <div class="field" style="flex:1; min-width:220px;">
          <div class="field-label"><span>Arquivo de Áudio (.wav)</span></div>
          <div class="file-drop" id="audioDrop">
            <input type="file" id="audioFile" accept=".wav,audio/wav" onchange="onAudioFile(this)">
            <div class="file-drop-label" id="audioDropLabel">
              <strong>Clique</strong> ou arraste o .wav aqui
            </div>
          </div>
        </div>

        <!-- Images -->
        <div class="field" style="flex:2; min-width:280px;">
          <div class="field-label">
            <span>Imagens (.jpg / .png)</span>
            <small id="imgCount">0 / 20 imagens</small>
          </div>
          <div class="file-drop" id="imgDrop">
            <input type="file" id="imageFiles" accept=".jpg,.jpeg,.png,image/jpeg,image/png"
                   multiple onchange="onImageFiles(this)">
            <div class="file-drop-label" id="imgDropLabel">
              <strong>Clique</strong> ou arraste as imagens (máx 20)
            </div>
          </div>
          <div class="image-previews" id="imagePreviews"></div>
        </div>
      </div>

      <button class="btn btn-primary" id="assembleBtn" onclick="runAssemble()">
        <div class="spin" id="assembleSpin" style="border-color:rgba(0,0,0,.2); border-top-color:#000;"></div>
        🎬 Montar Vídeo
      </button>

      <div class="alert" id="assembleAlert"></div>

      <!-- Video result -->
      <div class="media-result" id="videoResult">
        <div class="result-label">Vídeo Montado</div>
        <video id="videoPlayer" controls></video>
        <a class="download-link" id="videoDownload" download="video_final.mp4">
          ⬇ &nbsp;Baixar MP4
        </a>
      </div>

    </div>
  </section>

</main>

<!-- ═══════════════════════════════════════════
     JAVASCRIPT
═══════════════════════════════════════════ -->
<script>
'use strict';

/* ── State ── */
const state = {
  activeStage: 1,
  scriptDone: false,
  audioDone: false,
  audioBlob: null,
  selectedVoice: 'charon',
  imagePrompts: [],
};

/* ── Voices ── */
const VOICES = [
  { id: 'charon',    label: 'Charon',    desc: 'Profissional' },
  { id: 'fenrir',    label: 'Fenrir',    desc: 'Grave / Épico' },
  { id: 'orus',      label: 'Orus',      desc: 'Neutro' },
  { id: 'aoede',     label: 'Aoede',     desc: 'Suave' },
  { id: 'puck',      label: 'Puck',      desc: 'Expressivo' },
  { id: 'kore',      label: 'Kore',      desc: 'Firme' },
  { id: 'alnilam',   label: 'Alnilam',   desc: 'Nova ✦' },
  { id: 'enceladus', label: 'Enceladus', desc: 'Nova ✦' },
];

function buildVoiceGrid() {
  const grid = document.getElementById('voiceGrid');
  grid.innerHTML = VOICES.map(v => `
    <div class="voice-option ${v.id === state.selectedVoice ? 'selected' : ''}"
         onclick="selectVoice('${v.id}', this)">
      <span class="voice-name">${v.label}</span>
      <span class="voice-desc">${v.desc}</span>
    </div>`).join('');
}

function selectVoice(id, el) {
  state.selectedVoice = id;
  document.querySelectorAll('.voice-option').forEach(e => e.classList.remove('selected'));
  el.classList.add('selected');
}

/* ── Stage control ── */
function activateStage(n) {
  state.activeStage = n;

  for (let i = 1; i <= 3; i++) {
    const sec = document.getElementById('stage' + i);
    const nav = document.getElementById('nav-' + i);
    sec.classList.toggle('active-stage', i === n);
    nav.classList.toggle('active', i === n);
  }

  // Sync TTS textarea from script
  if (n === 2) {
    const sc = document.getElementById('scriptText').value.trim();
    if (sc) {
      document.getElementById('ttsText').value = sc;
      updateTtsCount();
    }
  }

  document.getElementById('stage' + n).scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function toggleStage(n) {
  if (state.activeStage === n) return;
  activateStage(n);
}

function scrollToStage(n) {
  activateStage(n);
}

/* ── API Key ── */
function toggleKey() {
  const inp = document.getElementById('apiKey');
  inp.type = inp.type === 'password' ? 'text' : 'password';
}

function getApiKey() {
  return document.getElementById('apiKey').value.trim();
}

document.getElementById('apiKey').addEventListener('input', () => {
  const v = document.getElementById('apiKey').value.trim();
  document.getElementById('apiStatus').textContent = v ? '✓ Key inserida' : 'Insira sua Gemini API Key';
  document.getElementById('apiStatus').style.color = v ? 'var(--green)' : '';
});

/* ── Alert helper ── */
function showAlert(id, msg, type) {
  const el = document.getElementById(id);
  el.textContent = msg;
  el.className = 'alert ' + type + ' show';
}

function hideAlert(id) {
  document.getElementById(id).className = 'alert';
}

/* ── Loading helpers ── */
function setLoading(btnId, spinId, loading) {
  document.getElementById(btnId).disabled = loading;
  document.getElementById(spinId).style.display = loading ? 'block' : 'none';
}

/* ── Char counters ── */
document.getElementById('scriptText').addEventListener('input', () => {
  const v = document.getElementById('scriptText').value.length;
  document.getElementById('charCount').textContent = v.toLocaleString('pt-BR');
});

function updateTtsCount() {
  const v = document.getElementById('ttsText').value.length;
  document.getElementById('ttsCharCount').textContent = v.toLocaleString('pt-BR') + ' caracteres';
}

/* ══════════════════════════════════════════
   STAGE 1 — SCRIPTIFY
══════════════════════════════════════════ */
async function runScriptify() {
  const apiKey = getApiKey();
  const url    = document.getElementById('sourceUrl').value.trim();

  if (!apiKey) { showAlert('scriptifyAlert', '⚠ Insira a Gemini API Key na barra superior.', 'error'); return; }
  if (!url)    { showAlert('scriptifyAlert', '⚠ Cole uma URL válida antes de continuar.', 'error'); return; }
  if (!url.startsWith('http')) { showAlert('scriptifyAlert', '⚠ A URL deve começar com http:// ou https://', 'error'); return; }

  setLoading('scriptifyBtn', 'scriptifySpin', true);
  showAlert('scriptifyAlert', 'Extraindo conteúdo e roteirizando... (30–60s)', 'loading');
  document.getElementById('scriptField').style.display = 'none';
  document.getElementById('promptsPanel').classList.remove('show');
  document.getElementById('hint1').style.display = 'none';

  try {
    const res = await fetch('/scriptify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: apiKey, url }),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Erro desconhecido');

    /* Script */
    document.getElementById('scriptText').value = data.script || '';
    document.getElementById('charCount').textContent = (data.script || '').length.toLocaleString('pt-BR');
    document.getElementById('scriptInfo').textContent =
      `${(data.script || '').length.toLocaleString('pt-BR')} chars · fonte: ${data.source_chars?.toLocaleString('pt-BR') || '?'} chars`;
    document.getElementById('scriptField').style.display = 'block';

    /* Image prompts */
    state.imagePrompts = data.image_prompts || [];
    renderPrompts(state.imagePrompts);

    /* Badge */
    setBadge(1, 'done', 'PRONTO');
    document.getElementById('nav-1').classList.add('done');
    state.scriptDone = true;

    showAlert('scriptifyAlert', `✓ Roteiro gerado com sucesso! ${state.imagePrompts.length} prompts de imagem criados.`, 'success');
    document.getElementById('hint1').style.display = 'block';

  } catch (e) {
    showAlert('scriptifyAlert', '✗ ' + e.message, 'error');
  } finally {
    setLoading('scriptifyBtn', 'scriptifySpin', false);
  }
}

function renderPrompts(prompts) {
  if (!prompts.length) return;
  document.getElementById('promptCount').textContent = prompts.length;
  document.getElementById('promptsList').innerHTML = prompts.map((p, i) => `
    <div class="prompt-item">
      <div class="prompt-num">${String(i + 1).padStart(2, '0')}</div>
      <div class="prompt-text">${escHtml(p)}</div>
      <button class="copy-prompt-btn" onclick="copyPrompt(this, ${i})">Copiar</button>
    </div>`).join('');
  document.getElementById('promptsPanel').classList.add('show');
}

function copyPrompt(btn, idx) {
  navigator.clipboard.writeText(state.imagePrompts[idx]).then(() => {
    btn.textContent = '✓ Copiado';
    btn.classList.add('copied');
    setTimeout(() => { btn.textContent = 'Copiar'; btn.classList.remove('copied'); }, 1800);
  });
}

function copyAllPrompts() {
  if (!state.imagePrompts.length) return;
  navigator.clipboard.writeText(state.imagePrompts.join('\n\n')).then(() => {
    const btn = document.querySelector('.prompts-header .btn');
    const orig = btn.textContent;
    btn.textContent = '✓ Copiados!';
    setTimeout(() => btn.textContent = orig, 2000);
  });
}

/* ══════════════════════════════════════════
   STAGE 2 — TTS STREAM
══════════════════════════════════════════ */
async function runTTS() {
  const apiKey = getApiKey();
  const text   = document.getElementById('ttsText').value.trim();

  if (!apiKey) { showAlert('ttsAlert', '⚠ Insira a Gemini API Key na barra superior.', 'error'); return; }
  if (!text)   { showAlert('ttsAlert', '⚠ Cole o roteiro antes de gerar o áudio.', 'error'); return; }

  setLoading('ttsBtn', 'ttsSpin', true);
  hideAlert('ttsAlert');
  document.getElementById('audioResult').classList.remove('show');
  document.getElementById('hint2').style.display = 'none';

  /* Progress UI */
  const progressWrap = document.getElementById('ttsProgress');
  const logEl        = document.getElementById('ttsLog');
  progressWrap.classList.add('show');
  logEl.classList.add('show');
  logEl.innerHTML = '';
  setProgress(0, 0, 'Conectando ao Gemini TTS...');

  function addLog(msg, cls = '') {
    const line = document.createElement('div');
    line.className = 'log-line ' + cls;
    line.textContent = msg;
    logEl.appendChild(line);
    logEl.scrollTop = logEl.scrollHeight;
  }

  function setProgress(cur, total, label) {
    const pct = total > 0 ? Math.round((cur / total) * 100) : 0;
    document.getElementById('progressFill').style.width = pct + '%';
    document.getElementById('progressPct').textContent  = pct + '%';
    document.getElementById('progressLabel').textContent = label;
  }

  try {
    const res = await fetch('/generate-stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: apiKey, text, voice: state.selectedVoice }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: 'Erro desconhecido' }));
      throw new Error(err.error || 'Erro na API');
    }

    const reader  = res.body.getReader();
    const decoder = new TextDecoder();
    let   buffer  = '';
    let   audiob64 = null;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop(); // keep incomplete line

      for (const raw of lines) {
        const line = raw.startsWith('data: ') ? raw.slice(6) : raw;
        if (!line.trim()) continue;

        let evt;
        try { evt = JSON.parse(line); } catch { continue; }

        if (evt.type === 'progress') {
          setProgress(evt.current, evt.total,
            `Processando chunk ${evt.current} de ${evt.total}...`);
          addLog(`[${String(evt.current).padStart(2,'0')}/${evt.total}] ${evt.preview || ''}...`, 'ok');

        } else if (evt.type === 'error') {
          addLog(`[WARN] chunk ${evt.chunk}: ${evt.message}`, 'warn');

        } else if (evt.type === 'done') {
          audiob64 = evt.audio_b64;
          setProgress(evt.chunks_processed || 1, evt.chunks_processed || 1, 'Finalizado!');
          addLog(`✓ ${evt.chunks_processed || 1} chunks processados`, 'ok');
        }
      }
    }

    if (!audiob64) throw new Error('Nenhum dado de áudio recebido do servidor.');

    /* b64 → Blob → URL */
    const bytes = Uint8Array.from(atob(audiob64), c => c.charCodeAt(0));
    state.audioBlob = new Blob([bytes], { type: 'audio/wav' });
    const audioUrl  = URL.createObjectURL(state.audioBlob);

    document.getElementById('audioPlayer').src = audioUrl;
    document.getElementById('audioDownload').href = audioUrl;
    document.getElementById('audioResult').classList.add('show');
    document.getElementById('audioResult').scrollIntoView({ behavior: 'smooth' });

    setBadge(2, 'done', 'PRONTO');
    document.getElementById('nav-2').classList.add('done');
    state.audioDone = true;
    document.getElementById('hint2').style.display = 'block';

    showAlert('ttsAlert', '✓ Áudio gerado com sucesso!', 'success');

  } catch (e) {
    showAlert('ttsAlert', '✗ ' + e.message, 'error');
    setProgress(0, 0, 'Erro');
  } finally {
    setLoading('ttsBtn', 'ttsSpin', false);
  }
}

/* ══════════════════════════════════════════
   STAGE 3 — ASSEMBLE
══════════════════════════════════════════ */
let selectedAudioFile  = null;
let selectedImageFiles = [];

function onAudioFile(input) {
  selectedAudioFile = input.files[0] || null;
  const label = document.getElementById('audioDropLabel');
  label.innerHTML = selectedAudioFile
    ? `<strong style="color:var(--green)">✓ ${escHtml(selectedAudioFile.name)}</strong>`
    : '<strong>Clique</strong> ou arraste o .wav aqui';
}

function onImageFiles(input) {
  const files = Array.from(input.files).slice(0, 20);
  selectedImageFiles = files;
  document.getElementById('imgCount').textContent = `${files.length} / 20 imagens`;

  const label = document.getElementById('imgDropLabel');
  label.innerHTML = files.length
    ? `<strong style="color:var(--green)">✓ ${files.length} imagens selecionadas</strong>`
    : '<strong>Clique</strong> ou arraste as imagens (máx 20)';

  /* Thumbnails */
  const strip = document.getElementById('imagePreviews');
  strip.innerHTML = '';
  files.forEach((f, i) => {
    const url  = URL.createObjectURL(f);
    const wrap = document.createElement('div');
    wrap.className = 'thumb-wrap';
    wrap.innerHTML = `<img src="${url}" alt="img ${i+1}"><div class="thumb-num">${i+1}</div>`;
    strip.appendChild(wrap);
  });
}

async function runAssemble() {
  /* Use audio blob from stage 2 if available, otherwise fall back to file input */
  const audioSource = state.audioBlob
    ? new File([state.audioBlob], 'audio.wav', { type: 'audio/wav' })
    : selectedAudioFile;

  if (!audioSource) {
    showAlert('assembleAlert', '⚠ Nenhum áudio disponível. Gere na Etapa 2 ou faça upload de um .wav.', 'error');
    return;
  }

  if (!selectedImageFiles.length) {
    showAlert('assembleAlert', '⚠ Selecione pelo menos 1 imagem.', 'error');
    return;
  }

  setLoading('assembleBtn', 'assembleSpin', true);
  showAlert('assembleAlert', 'Montando vídeo com FFmpeg... (pode levar 1–3 min)', 'loading');
  document.getElementById('videoResult').classList.remove('show');

  try {
    const form = new FormData();
    form.append('audio', audioSource, audioSource.name);
    selectedImageFiles.forEach(f => form.append('images', f, f.name));

    const res = await fetch('/assemble', { method: 'POST', body: form });

    if (!res.ok) {
      let msg = 'Erro no servidor.';
      try { const j = await res.json(); msg = j.error || msg; } catch {}
      throw new Error(msg);
    }

    const blob   = await res.blob();
    const vidUrl = URL.createObjectURL(blob);

    document.getElementById('videoPlayer').src = vidUrl;
    document.getElementById('videoDownload').href = vidUrl;
    document.getElementById('videoResult').classList.add('show');
    document.getElementById('videoResult').scrollIntoView({ behavior: 'smooth' });

    setBadge(3, 'done', 'PRONTO');
    document.getElementById('nav-3').classList.add('done');
    showAlert('assembleAlert', '✓ Vídeo montado com sucesso!', 'success');

  } catch (e) {
    showAlert('assembleAlert', '✗ ' + e.message, 'error');
  } finally {
    setLoading('assembleBtn', 'assembleSpin', false);
  }
}

/* ── Badge helper ── */
function setBadge(stage, type, text) {
  const el = document.getElementById('badge-' + stage);
  el.textContent = text;
  el.className = 'stage-badge badge-' + type;
}

/* ── Escape HTML ── */
function escHtml(str) {
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

/* ── Init ── */
buildVoiceGrid();
updateTtsCount();

/* Drag-over effect */
['audioDrop','imgDrop'].forEach(id => {
  const el = document.getElementById(id);
  el.addEventListener('dragover', e => { e.preventDefault(); el.classList.add('drag-over'); });
  el.addEventListener('dragleave', () => el.classList.remove('drag-over'));
  el.addEventListener('drop', () => el.classList.remove('drag-over'));
});
</script>
</body>
</html>