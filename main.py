import os
import threading
import time
import webbrowser
from dataclasses import asdict, dataclass
from typing import Any

import keyboard
import psutil
import pyautogui
from flask import Flask, jsonify, render_template_string, request

pyautogui.FAILSAFE = False

HTML_PAGE = """
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Minecraft 1.8.9 Smart Local Panel</title>
  <style>
    :root {
      --bg1: #0b1020;
      --bg2: #121a30;
      --card: rgba(255,255,255,0.06);
      --border: rgba(255,255,255,0.15);
      --text: #e8ecff;
      --muted: #9aa6d8;
      --green: #34d399;
      --red: #fb7185;
      --blue: #60a5fa;
      --gold: #facc15;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      font-family: Inter, Segoe UI, Arial, sans-serif;
      background: radial-gradient(1200px 600px at 0% -20%, #1d4ed8 0%, transparent 60%),
                  radial-gradient(1000px 600px at 100% 120%, #7c3aed 0%, transparent 60%),
                  linear-gradient(135deg, var(--bg1), var(--bg2));
      color: var(--text);
      display: flex;
      justify-content: center;
      padding: 30px 16px;
    }
    .wrap {
      width: min(960px, 100%);
      display: grid;
      grid-template-columns: 1.2fr 1fr;
      gap: 16px;
    }
    .card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 20px;
      backdrop-filter: blur(12px);
      padding: 20px;
      box-shadow: 0 14px 32px rgba(0,0,0,0.35);
    }
    h1 { margin: 0 0 6px; font-size: 30px; }
    .sub { color: var(--muted); margin-bottom: 20px; }
    .status {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      font-weight: 700;
      border-radius: 999px;
      padding: 8px 12px;
      letter-spacing: .4px;
      text-transform: uppercase;
    }
    .dot { width: 10px; height: 10px; border-radius: 50%; }
    .ok { color: var(--green); background: rgba(52,211,153,0.12); }
    .ok .dot { background: var(--green); box-shadow: 0 0 10px var(--green); }
    .bad { color: var(--red); background: rgba(251,113,133,0.12); }
    .bad .dot { background: var(--red); box-shadow: 0 0 10px var(--red); }
    .kv { display: flex; justify-content: space-between; margin-top: 12px; color: var(--muted); }
    .value { color: var(--text); font-weight: 600; }
    .switches { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 18px; }
    .pill {
      background: rgba(255,255,255,0.05);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 12px;
    }
    .on { color: var(--green); }
    .off { color: var(--red); }
    label { display: block; margin: 10px 0 6px; color: var(--muted); }
    input {
      width: 100%;
      background: rgba(255,255,255,0.04);
      color: var(--text);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 10px 12px;
      outline: none;
    }
    input:focus { border-color: var(--blue); box-shadow: 0 0 0 2px rgba(96,165,250,.2); }
    button {
      margin-top: 14px;
      width: 100%;
      border: 0;
      border-radius: 12px;
      padding: 12px;
      font-weight: 700;
      color: #0b1020;
      background: linear-gradient(90deg, #60a5fa, #34d399);
      cursor: pointer;
    }
    .hint { color: var(--gold); margin-top: 12px; font-size: 13px; }
    .message { margin-top: 10px; min-height: 18px; color: var(--green); }
    @media (max-width: 860px) {
      .wrap { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <section class="card">
      <h1>MC 1.8.9 Control</h1>
      <div class="sub">Авто-кликер + авто-строительство с локального сайта</div>
      <div id="mc-status" class="status bad"><span class="dot"></span><span>DISCONNECTED</span></div>
      <div class="kv"><span>Minecraft process:</span><span id="proc-name" class="value">—</span></div>
      <div class="kv"><span>Версия:</span><span id="mc-version" class="value">—</span></div>
      <div class="switches">
        <div class="pill">
          <div>Auto Build</div>
          <div class="value"><span id="build-state" class="off">OFF</span> · key <code id="build-key-show">f6</code></div>
        </div>
        <div class="pill">
          <div>Auto Click</div>
          <div class="value"><span id="click-state" class="off">OFF</span> · key <code id="click-key-show">f7</code></div>
        </div>
      </div>
      <div class="hint">После запуска Minecraft 1.8.9 статус станет <b style="color:#34d399">CONNECTED</b> автоматически.</div>
    </section>

    <section class="card">
      <h2 style="margin-top:0">Настройки</h2>
      <label for="cps">CPS (1-30)</label>
      <input id="cps" type="number" min="1" max="30" value="10" />

      <label for="build_key">Бинд Auto Build</label>
      <input id="build_key" type="text" value="f6" />

      <label for="click_key">Бинд Auto Click</label>
      <input id="click_key" type="text" value="f7" />

      <button onclick="saveSettings()">Сохранить настройки</button>
      <div class="message" id="msg"></div>
    </section>
  </div>

<script>
async function refresh() {
  const r = await fetch('/api/status');
  const data = await r.json();

  const status = document.getElementById('mc-status');
  status.className = 'status ' + (data.minecraft_connected ? 'ok' : 'bad');
  status.innerHTML = `<span class="dot"></span><span>${data.minecraft_connected ? 'CONNECTED' : 'DISCONNECTED'}</span>`;

  document.getElementById('proc-name').textContent = data.detected_process || '—';
  document.getElementById('mc-version').textContent = data.detected_version || '—';

  document.getElementById('build-state').textContent = data.auto_build_enabled ? 'ON' : 'OFF';
  document.getElementById('build-state').className = data.auto_build_enabled ? 'on' : 'off';
  document.getElementById('click-state').textContent = data.auto_click_enabled ? 'ON' : 'OFF';
  document.getElementById('click-state').className = data.auto_click_enabled ? 'on' : 'off';

  document.getElementById('build-key-show').textContent = data.build_key;
  document.getElementById('click-key-show').textContent = data.click_key;

  document.getElementById('cps').value = data.cps;
  document.getElementById('build_key').value = data.build_key;
  document.getElementById('click_key').value = data.click_key;
}

async function saveSettings() {
  const payload = {
    cps: Number(document.getElementById('cps').value),
    build_key: document.getElementById('build_key').value.trim().toLowerCase(),
    click_key: document.getElementById('click_key').value.trim().toLowerCase()
  };

  const r = await fetch('/api/settings', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload)
  });

  const data = await r.json();
  const msg = document.getElementById('msg');
  msg.style.color = r.ok ? '#34d399' : '#fb7185';
  msg.textContent = data.message || (r.ok ? 'Сохранено' : 'Ошибка');
  await refresh();
}

setInterval(refresh, 1000);
refresh();
</script>
</body>
</html>
"""


@dataclass
class RuntimeState:
    cps: int = 10
    build_key: str = "f6"
    click_key: str = "f7"
    auto_build_enabled: bool = False
    auto_click_enabled: bool = False
    minecraft_connected: bool = False
    detected_process: str = ""
    detected_version: str = ""


state = RuntimeState()
state_lock = threading.Lock()
app = Flask(__name__)
hotkey_refs: dict[str, tuple[str, int]] = {}
website_opened_once = False


def detect_minecraft_process() -> tuple[bool, str, str]:
    version_markers = ["1.8.9", "forge", "lunar", "badlion"]
    for proc in psutil.process_iter(attrs=["name", "cmdline"]):
        try:
            name = (proc.info.get("name") or "").lower()
            cmdline_list = proc.info.get("cmdline") or []
            cmdline = " ".join(cmdline_list).lower()

            looks_java = any(x in name for x in ("java", "javaw"))
            looks_mc = "minecraft" in cmdline or "net.minecraft.launchwrapper" in cmdline
            if not (looks_java and looks_mc):
                continue

            detected_version = "unknown"
            for marker in version_markers:
                if marker in cmdline:
                    detected_version = marker
                    break

            if "1.8.9" in cmdline or "launchwrapper" in cmdline:
                return True, name, detected_version
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False, "", ""


def can_run_actions() -> bool:
    with state_lock:
        return state.minecraft_connected


def click_interval() -> float:
    with state_lock:
        cps = max(1, min(30, state.cps))
    return 1.0 / cps


def build_worker() -> None:
    while True:
        with state_lock:
            enabled = state.auto_build_enabled
        if enabled and can_run_actions():
            pyautogui.click(button="right")
            time.sleep(click_interval())
        else:
            time.sleep(0.03)


def click_worker() -> None:
    while True:
        with state_lock:
            enabled = state.auto_click_enabled
        if enabled and can_run_actions():
            pyautogui.click(button="left")
            time.sleep(click_interval())
        else:
            time.sleep(0.03)


def try_open_panel() -> None:
    global website_opened_once
    if not website_opened_once:
        website_opened_once = True
        webbrowser.open("http://127.0.0.1:5000")


def minecraft_monitor() -> None:
    while True:
        connected, process_name, version = detect_minecraft_process()

        with state_lock:
            old = state.minecraft_connected
            state.minecraft_connected = connected
            state.detected_process = process_name
            state.detected_version = version
            if not connected:
                state.auto_build_enabled = False
                state.auto_click_enabled = False

        if connected and not old:
            print("\033[92m[MC] CONNECTED\033[0m")
            try_open_panel()
        elif not connected and old:
            print("\033[91m[MC] DISCONNECTED\033[0m")

        time.sleep(1)


def toggle_build() -> None:
    with state_lock:
        if state.minecraft_connected:
            state.auto_build_enabled = not state.auto_build_enabled


def toggle_click() -> None:
    with state_lock:
        if state.minecraft_connected:
            state.auto_click_enabled = not state.auto_click_enabled


def bind_hotkeys() -> None:
    with state_lock:
        target_build = state.build_key
        target_click = state.click_key

    expected = {"build": target_build, "click": target_click}

    for action, (saved_key, hotkey_id) in list(hotkey_refs.items()):
        if expected.get(action) != saved_key:
            keyboard.remove_hotkey(hotkey_id)
            del hotkey_refs[action]

    for action, key in expected.items():
        if action in hotkey_refs and hotkey_refs[action][0] == key:
            continue
        callback = toggle_build if action == "build" else toggle_click
        hotkey_id = keyboard.add_hotkey(key, callback)
        hotkey_refs[action] = (key, hotkey_id)


def hotkey_watcher() -> None:
    while True:
        bind_hotkeys()
        time.sleep(1)


@app.get("/")
def index() -> str:
    return render_template_string(HTML_PAGE)


@app.get("/api/status")
def api_status():
    with state_lock:
        return jsonify(asdict(state))


@app.post("/api/settings")
def api_settings():
    payload: dict[str, Any] = request.get_json(force=True, silent=True) or {}

    try:
        cps = int(payload.get("cps", state.cps))
    except (TypeError, ValueError):
        return jsonify({"message": "CPS должен быть числом"}), 400

    cps = max(1, min(30, cps))
    build_key = str(payload.get("build_key", state.build_key)).strip().lower()
    click_key = str(payload.get("click_key", state.click_key)).strip().lower()

    if not build_key or not click_key:
        return jsonify({"message": "Бинды не должны быть пустыми"}), 400

    with state_lock:
        state.cps = cps
        state.build_key = build_key
        state.click_key = click_key

    return jsonify({"message": "Настройки обновлены"})


def startup() -> None:
    threading.Thread(target=minecraft_monitor, daemon=True).start()
    threading.Thread(target=build_worker, daemon=True).start()
    threading.Thread(target=click_worker, daemon=True).start()
    threading.Thread(target=hotkey_watcher, daemon=True).start()


if __name__ == "__main__":
    print("[INFO] Starting local panel at http://127.0.0.1:5000")
    startup()
    app.run(host="127.0.0.1", port=5000, debug=False)
