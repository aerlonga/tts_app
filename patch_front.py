import re

with open("possivel front.md", "r") as f:
    content = f.read()

# 1. Fix CSS
# We need to remove display: none; and display: flex; from .next-hint
content = re.sub(r'(\.next-hint\s*\{[^}]*?)\s*display:\s*none;\n', r'\1\n', content)
content = re.sub(r'(\.next-hint\s*\{[^}]*?)\s*display:\s*flex;\n', r'\1\n', content)

# 2. Add Toggle CSS
css_to_add = """
/* ═══════════════════════════════════════════
   TOGGLE SWITCH
═══════════════════════════════════════════ */
.toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 0 14px 0;
  border-top: 1px solid var(--border);
  margin-top: 4px;
}

.toggle-label {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.toggle-label span {
  font-family: var(--mono);
  font-size: 11px;
  color: var(--text);
  letter-spacing: 1px;
  text-transform: uppercase;
}

.toggle-label small {
  font-size: 10px;
  color: var(--text3);
  font-family: var(--mono);
}

.switch {
  position: relative;
  display: inline-block;
  width: 42px;
  height: 24px;
  flex-shrink: 0;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  inset: 0;
  background: var(--bg2);
  border: 1px solid var(--border2);
  border-radius: 24px;
  cursor: pointer;
  transition: background .2s, border-color .2s;
}

.slider::before {
  content: '';
  position: absolute;
  left: 3px;
  top: 50%;
  transform: translateY(-50%);
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--text3);
  transition: left .2s, background .2s;
}

.switch input:checked+.slider {
  background: var(--amber-dim);
  border-color: var(--amber);
}

.switch input:checked+.slider::before {
  left: 21px;
  background: var(--amber);
}
"""

content = content.replace("/* Scrollbar */", css_to_add + "\n/* Scrollbar */")

# 3. Add HTML Toggle
html_to_add = """
      <div class="field">
        <div class="toggle-row">
          <div class="toggle-label">
            <span>Entonacao Inteligente</span>
            <small>Gemini adiciona marcacoes de entonacao antes de gerar o audio</small>
          </div>
          <label class="switch">
            <input type="checkbox" id="enhanceToggle" checked>
            <span class="slider"></span>
          </label>
        </div>
      </div>
"""
content = content.replace(
    '<button class="btn btn-primary" id="ttsBtn" onclick="runTTS()">',
    html_to_add + '\n      <button class="btn btn-primary" id="ttsBtn" onclick="runTTS()">'
)

# 4. Modify runTTS JS
# Let's replace the top of runTTS
old_js_start = """async function runTTS() {
  const apiKey = getApiKey();
  const text   = document.getElementById('ttsText').value.trim();"""

new_js_start = """async function runTTS() {
  const apiKey = getApiKey();
  let text   = document.getElementById('ttsText').value.trim();
  const useEnhance = document.getElementById('enhanceToggle').checked;"""

content = content.replace(old_js_start, new_js_start)

# Now replace the try block start
old_try_start = """  try {
    const res = await fetch('/generate-stream', {"""

new_try_start = """  try {
    if (useEnhance) {
      setProgress(0, 0, 'Analisando entonação...');
      addLog('Iniciando /enhance para marcações de entonação...', 'info');
      
      const enhRes = await fetch('/enhance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: apiKey, text })
      });
      if (!enhRes.ok) {
        const err = await enhRes.json().catch(()=>({}));
        throw new Error('Enhance: ' + (err.error || 'Erro desconhecido'));
      }
      const enhData = await enhRes.json();
      text = enhData.enhanced_text;
      
      // Update the textarea to show the enhanced text
      document.getElementById('ttsText').value = text;
      updateTtsCount();
      
      addLog('✓ Entonação adicionada com sucesso.', 'ok');
      setProgress(0, 0, 'Conectando ao Gemini TTS...');
    }

    const res = await fetch('/generate-stream', {"""

content = content.replace(old_try_start, new_try_start)

with open("index.html", "w") as f:
    f.write(content)

print("index.html successfully updated!")
