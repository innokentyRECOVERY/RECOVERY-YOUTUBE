# =====================================================================
# RECOVERY YOUTUBE
# Обход блокировки YouTube через VLESS-подписку (сервер: Англия)
# Split-tunnel: ТОЛЬКО youtube.com идут через VPN, остальное напрямую
# =====================================================================
import ctypes
import json
import io
import os
import re
import subprocess
import sys
import threading
import time
import urllib.request
import urllib.parse
import zipfile
import tkinter as tk
from tkinter import messagebox

SUBSCRIPTION_URL = "https://hubcom.xyz/sub/1/45ad8f39-8935-4027-9504-173b75d30893"
ENGLAND_FUSO_FLAG = "\u0410\u043d\u0433\u043b\u0438\u044f"
ENG_FRAG = "\U0001F1EC\U0001F1E7"  # флаг 🇬🇧 (Англия/Великобритания)

if getattr(sys, "frozen", False):
    # скомпилировано в .exe — работаем рядом с exe-файлом
    APP_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_PATH = os.path.join(APP_DIR, "settings.json")
WORK_DIR_KEY = "work_dir"
DEFAULT_WORK_DIR = APP_DIR

PROXY_HOST = "127.0.0.1"
PROXY_HTTP_PORT = 10809
PROXY_SOCKS_PORT = 10808

XRAY_RELEASE_URL = "https://github.com/XTLS/Xray-core/releases/latest/download/Xray-windows-64.zip"

YT_DOMAINS = [
    "youtube.com", "www.youtube.com", "m.youtube.com",
    "googlevideo.com", "ytimg.com", "youtu.be",
    "youtube-nocookie.com", "ggpht.com", "youtubei.googleapis.com",
    "yt3.ggpht.com", "googlevideo.com",
]

INTERNET_SETTINGS_KEY = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"


def hide_console():
    try:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)
    except Exception:
        pass


class RecoveryYouTubeApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("RECOVERY YOUTUBE")
        self.root.configure(bg="#1a1a2e")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.status_text = tk.StringVar(value="Готов к запуску")
        self.server_text = tk.StringVar(value="Сервер: Англия 🇬🇧")
        self.xray_proc = None
        self.working = False
        self.last_up = 0
        self.last_down = 0
        self.timer_job = None
        self.connected = False
        self.expire_ts = None
        self.active_url = SUBSCRIPTION_URL
        self.keepalive = threading.Event()
        self.keepalive.clear()
        self.session_seconds = 2 * 60 * 60  # лимит одной сессии: 2 часа
        self.folder_text = tk.StringVar(value="")

        self.work_dir = self.load_work_dir()
        self.apply_work_dir()

        self.build_ui()
        self.center_window()

    def center_window(self):
        self.root.update_idletasks()
        w, h = 520, 520
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    # ---------------- работа с папкой xray ----------------

    def load_work_dir(self):
        try:
            if os.path.exists(SETTINGS_PATH):
                with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                d = data.get(WORK_DIR_KEY, "")
                if d and os.path.isdir(d):
                    return d
        except Exception:
            pass
        return DEFAULT_WORK_DIR

    def save_work_dir(self):
        try:
            with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump({WORK_DIR_KEY: self.work_dir}, f, ensure_ascii=False)
        except Exception:
            pass

    def apply_work_dir(self):
        self.XRAY_DIR = self.work_dir
        self.XRAY_EXE = os.path.join(self.work_dir, "xray.exe")
        self.CONFIG_PATH = os.path.join(self.work_dir, "xray_config.json")
        self.folder_text.set(self.work_dir)

    def pick_work_dir(self):
        from tkinter import filedialog
        import winreg
        init = self.work_dir if os.path.isdir(self.work_dir) else APP_DIR
        old_hidden = None
        try:
            adv = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
                0, winreg.KEY_READ | winreg.KEY_SET_VALUE)
            try:
                old_hidden, _ = winreg.QueryValueEx(adv, "Hidden")
            except OSError:
                old_hidden = None
            winreg.SetValueEx(adv, "Hidden", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(adv)
        except Exception:
            pass
        try:
            chosen = filedialog.askdirectory(
                title="Выберите папку для xray-core и настроек", initialdir=init)
        finally:
            if old_hidden is not None:
                try:
                    adv = winreg.OpenKey(
                        winreg.HKEY_CURRENT_USER,
                        r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
                        0, winreg.KEY_SET_VALUE)
                    winreg.SetValueEx(adv, "Hidden", 0, winreg.REG_DWORD, old_hidden)
                    winreg.CloseKey(adv)
                except Exception:
                    pass
        if chosen:
            self.work_dir = os.path.normpath(chosen)
            self.save_work_dir()
            self.apply_work_dir()
            self.set_status(f"Папка загрузок: {self.work_dir}")

    def build_ui(self):
        title = tk.Label(
            self.root, text="RECOVERY YOUTUBE",
            font=("Arial", 26, "bold"), fg="#e94560", bg="#1a1a2e"
        )
        title.pack(pady=(25, 5))

        subtitle = tk.Label(
            self.root, text="Обход блокировки YouTube",
            font=("Arial", 13), fg="#a0a0b8", bg="#1a1a2e"
        )
        subtitle.pack()

        server_lbl = tk.Label(
            self.root, textvariable=self.server_text,
            font=("Arial", 14, "bold"), fg="#4fc3f7", bg="#1a1a2e"
        )
        server_lbl.pack(pady=10)

        self.run_btn = tk.Button(
            self.root, text="ЗАПУСТИТЬ ОБХОД",
            font=("Arial", 16, "bold"),
            command=self.start_bypass,
            bg="#00a84d", fg="white",
            activebackground="#00c75a", activeforeground="white",
            width=22, pady=10, cursor="hand2"
        )
        self.run_btn.pack(pady=15)

        self.stop_btn = tk.Button(
            self.root, text="ОСТАНОВИТЬ",
            font=("Arial", 14, "bold"),
            command=self.stop_bypass,
            bg="#b33939", fg="white",
            activebackground="#cc0000", activeforeground="white",
            width=18, pady=6, cursor="hand2",
            state="disabled"
        )
        self.stop_btn.pack(pady=5)

        status_lbl = tk.Label(
            self.root, textvariable=self.status_text,
            font=("Arial", 12), fg="#ffd166", bg="#1a1a2e", wraplength=460
        )
        status_lbl.pack(pady=10)

        self.updown_text = tk.StringVar(value="⬆ 0 B | ⬇ 0 B")
        updown_lbl = tk.Label(
            self.root, textvariable=self.updown_text,
            font=("Consolas", 13, "bold"), fg="#7bed9f", bg="#1a1a2e"
        )
        updown_lbl.pack()

        self.timer_text = tk.StringVar(value="Осталось: 02:00:00")
        timer_lbl = tk.Label(
            self.root, textvariable=self.timer_text,
            font=("Consolas", 13, "bold"), fg="#ff7f50", bg="#1a1a2e"
        )
        timer_lbl.pack(pady=(4, 4))

        self.folder_frame = tk.Frame(self.root, bg="#1a1a2e")
        self.folder_frame.pack(pady=(6, 2))
        folder_lbl = tk.Label(
            self.root, textvariable=self.folder_text,
            font=("Arial", 8), fg="#8a8aa0", bg="#1a1a2e", wraplength=470
        )
        folder_lbl.pack()
        folder_btn = tk.Button(
            self.root, text="📁 Выбрать папку для xray",
            command=self.pick_work_dir,
            font=("Arial", 10, "bold"), bg="#533483", fg="white",
            activebackground="#6f42c1", activeforeground="white",
            width=20, pady=2, cursor="hand2"
        )
        folder_btn.pack(pady=(3, 4))

        self.code_frame = tk.Frame(self.root, bg="#1a1a2e")
        self.code_frame.pack(pady=2)
        code_hint = tk.Label(
            self.code_frame, text="Новый код подписки:", font=("Arial", 10),
            fg="#a0a0b8", bg="#1a1a2e"
        )
        code_hint.pack()
        self.code_entry = tk.Entry(
            self.code_frame, width=54, font=("Arial", 10), state="normal",
            bg="#16213e", fg="white", insertbackground="white", disabledbackground="#16213e",
            disabledforeground="#8a8aa0"
        )
        self.code_entry.pack(pady=(3, 3))
        self.apply_btn = tk.Button(
            self.code_frame, text="ПРИМЕНИТЬ КОД", state="normal",
            command=self.apply_new_code,
            font=("Arial", 11, "bold"), bg="#f39c12", fg="white",
            activebackground="#ffb347", activeforeground="white",
            width=16, pady=3, cursor="hand2"
        )
        self.apply_btn.pack()

        note = tk.Label(
            self.root,
            text="Через VPN идут только сайты YouTube.\nОстальной интернет не затрагивается.\nЛимит сессии: 2 часа — потом автоотключение и повторный запуск вручную.",
            font=("Arial", 10), fg="#8a8aa0", bg="#1a1a2e", justify="center"
        )
        note.pack(side="bottom", pady=8)

    # ---------------- subscription / config ----------------

    def fetch_subscription(self, url=None):
        url = url or self.active_url or SUBSCRIPTION_URL
        # не ходим через локальный прокси/системный прокси — напрямую,
        # иначе при включённом прокси подписка зависает бесконечно
        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({})
        )
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
        })
        with opener.open(req, timeout=15) as resp:
            raw = resp.read()
        text = raw.decode("utf-8", errors="replace").strip()
        # возможна base64/raw кодировка подписки
        if not text.startswith("{") and not text.startswith("[") \
                and not text.startswith("vless://") and "://" not in text:
            import base64
            try:
                decoded = base64.b64decode(text + "=" * (-len(text) % 4)).decode("utf-8", errors="replace")
                if decoded.strip().startswith(("{", "[")) or "://" in decoded:
                    text = decoded
            except Exception:
                pass
        data = {}
        text = text.strip()
        if text.startswith("{") or text.startswith("["):
            try:
                data = json.loads(text)
            except Exception:
                data = {}
            links = data.get("links", [])
            # извлечь срок истечения, если приходит в подписке
            for k in ("expire", "expires", "expiry", "daysLeft", "expireTime", "expire_date"):
                v = data.get(k)
                if v is not None:
                    ts = self._to_ts(v)
                    if ts:
                        self.expire_ts = ts
                    break
        else:
            # подписка пришла как простой список ссылок (формат поменялся)
            links = [ln.strip() for ln in text.splitlines() if ln.strip()]
        data["links"] = links
        return data

    def find_england_link(self, links):
        england = None
        for link in links:
            low = link.lower()
            if "vless://" in low:
                # имя сервера в подписке — в фрагменте # после ссылки (URL-encoded)
                frag = link.split("#", 1)[1] if "#" in link else ""
                decoded = urllib.parse.unquote(frag)
                if ("англия" in decoded.lower() or "england" in decoded.lower()
                        or ENG_FRAG in decoded):
                    england = link
                    break
        if not england:
            for link in links:
                if "vless://" in link:
                    england = link
                    break
        return england

    def _to_ts(self, v):
        try:
            if isinstance(v, (int, float)):
                return float(v)
            v = str(v).strip()
            if v.isdigit():
                return float(v)
            v = v.replace("Z", "+00:00")
            fmts = [
                "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f",
                "%Y/%m/%d %H:%M:%S", "%d/%m/%Y %H:%M:%S",
                "%m/%d/%Y %H:%M:%S", "%Y-%m-%d",
            ]
            import datetime as _dt
            for f in fmts:
                try:
                    d = _dt.datetime.strptime(v[:26], f)
                    return d.timestamp()
                except ValueError:
                    continue
        except Exception:
            pass
        return None

    def build_outbound(self, vless_uri):
        parsed = urllib.parse.urlparse(vless_uri)
        host = parsed.hostname
        port = parsed.port
        params = dict(urllib.parse.parse_qsl(parsed.query))
        user_id = parsed.username

        stream = {}
        network = params.get("type", "tcp")
        stream["network"] = network
        security = params.get("security", "none")
        stream["security"] = security

        if security == "reality":
            reality = {
                "serverName": params.get("sni", ""),
                "fingerprint": params.get("fp", "chrome"),
                "publicKey": params.get("pbk", ""),
                "shortId": params.get("sid", ""),
            }
            if params.get("spx"):
                reality["spiderX"] = params.get("spx").replace("%2F", "/")
            stream["realitySettings"] = reality
        elif security == "tls":
            stream["tlsSettings"] = {
                "serverName": params.get("sni", ""),
                "fingerprint": params.get("fp", "chrome"),
                "alpn": [params.get("alpn", "")] if params.get("alpn") else None,
            }

        if network == "grpc":
            stream["grpcSettings"] = {
                "serviceName": params.get("serviceName", params.get("path", "")),
                "mode": "gun",
            }
        elif network == "ws":
            stream["wsSettings"] = {
                "path": params.get("path", ""),
                "headers": {"Host": params.get("host", "")} if params.get("host") else None,
            }
        elif network == "xhttp":
            stream["xhttpSettings"] = {
                "path": params.get("path", ""),
                "mode": params.get("mode", "auto"),
            }

        outbound = {
            "tag": "proxy",
            "protocol": "vless",
            "settings": {
                "vnext": [{
                    "address": host,
                    "port": port,
                    "users": [{"id": user_id, "encryption": params.get("encryption", "none")}],
                }]
            },
            "streamSettings": stream,
        }
        return outbound

    def generate_config(self, outbound):
        config = {
            "log": {"loglevel": "warning"},
            "api": {"tag": "api", "services": ["HandlerService", "StatsService"]},
            "stats": {},
            "policy": {
                "levels": {
                    "0": {
                        "statsUserUplink": True,
                        "statsUserDownlink": True,
                    }
                },
                "system": {
                    "statsInboundUplink": True,
                    "statsInboundDownlink": True,
                    "statsOutboundUplink": True,
                    "statsOutboundDownlink": True,
                },
            },
            "inbounds": [
                {
                    "tag": "http-in",
                    "listen": PROXY_HOST,
                    "port": PROXY_HTTP_PORT,
                    "protocol": "http",
                    "settings": {"allowTransparent": False},
                },
                {
                    "tag": "socks-in",
                    "listen": PROXY_HOST,
                    "port": PROXY_SOCKS_PORT,
                    "protocol": "socks",
                    "settings": {"udp": True},
                },
                {
                    "tag": "api",
                    "listen": PROXY_HOST,
                    "port": 10086,
                    "protocol": "dokodemo-door",
                    "settings": {"address": "127.0.0.1"},
                },
            ],
            "outbounds": [
                outbound,
                {"tag": "direct", "protocol": "freedom", "settings": {}},
                {"tag": "block", "protocol": "blackhole", "settings": {}},
                {"tag": "api", "protocol": "blackhole", "settings": {}},
            ],
            "routing": {
                "domainStrategy": "AsIs",
                "rules": [
                    {
                        "type": "field",
                        "inboundTag": ["api"],
                        "outboundTag": "api",
                    },
                    {
                        "type": "field",
                        "outboundTag": "proxy",
                        "domain": YT_DOMAINS,
                    },
                    {"type": "field", "outboundTag": "direct", "network": "tcp,udp"},
                ],
            },
        }
        return config

    # ---------------- xray management ----------------

    def download_xray(self):
        os.makedirs(self.XRAY_DIR, exist_ok=True)
        self.set_status("Скачивание xray-core...")
        zip_path = os.path.join(self.XRAY_DIR, "xray.zip")
        urllib.request.urlretrieve(XRAY_RELEASE_URL, zip_path)
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(self.XRAY_DIR)
        os.remove(zip_path)
        if not os.path.exists(self.XRAY_EXE):
            raise RuntimeError("xray.exe не найден после распаковки")

    def run_xray(self):
        self.xray_proc = subprocess.Popen(
            [self.XRAY_EXE, "run", "-c", self.CONFIG_PATH],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

    def xray_alive(self):
        return self.xray_proc is not None and self.xray_proc.poll() is None

    # ---------------- system proxy ----------------

    def set_system_proxy(self, on):
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, INTERNET_SETTINGS_KEY, 0, winreg.KEY_SET_VALUE
        )
        if on:
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ,
                              f"{PROXY_HOST}:{PROXY_HTTP_PORT}")
            winreg.SetValueEx(key, "ProxyOverride", 0, winreg.REG_SZ,
                              "<local>;baidu.com;qq.com;weixin.qq.com;taobao.com;tmall.com;jd.com")
        else:
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
        winreg.CloseKey(key)
        ctypes.windll.wininet.InternetSetOptionW(0, 39, 0, 0)
        ctypes.windll.wininet.InternetSetOptionW(0, 37, 0, 0)

    # ---------------- main flow ----------------

    def set_status(self, text):
        self.status_text.set(text)

    def start_bypass(self):
        if self.working or self.connected:
            return
        self.working = True
        self.run_btn.config(state="disabled")
        threading.Thread(target=self._start_worker, daemon=True).start()

    def _start_worker(self):
        try:
            if not os.path.exists(self.XRAY_EXE):
                self.download_xray()

            self.set_status("Получение подписки...")
            data = self.fetch_subscription()
            links = data.get("links", [])
            england = self.find_england_link(links)
            if not england:
                raise RuntimeError("VLESS-ссылка не найдена в подписке")

            outbound = self.build_outbound(england)
            config = self.generate_config(outbound)
            with open(self.CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            if self.xray_alive():
                self.kill_xray()
            self.set_status("Запуск соединения (Англия)...")
            self.run_xray()
            time.sleep(2.5)

            if not self.xray_alive():
                raise RuntimeError("xray-core завершился с ошибкой")

            self.set_system_proxy(True)
            self.connected = True
            self.keepalive.set()
            self.root.after(0, self._started_ui)

        except Exception as e:
            msg = str(e)
            self.root.after(0, lambda: self._fail(msg))

    def _started_ui(self):
        self.working = False
        self.stop_btn.config(state="normal")
        self.session_seconds = 2 * 60 * 60
        self.timer_text.set(self.session_label())
        self.set_status("Подключено (Англия). Проверяю связь с сервером...")
        self.update_stats()
        threading.Thread(target=self.verify_proxy, daemon=True).start()
        threading.Thread(target=self._keepalive_loop, daemon=True).start()

    def session_label(self):
        if self.expire_ts and time.time() > self.expire_ts:
            return "Подписка истекла — жду новый код"
        s = max(int(self.session_seconds), 0)
        h, rem = divmod(s, 3600)
        m, sec = divmod(rem, 60)
        return f"Осталось: {h:02}:{m:02}:{sec:02}"

    def _keepalive_loop(self):
        failed = 0
        while self.keepalive.is_set() and self.connected:
            time.sleep(15)
            if not self.connected:
                break
            if self.expire_ts and time.time() > self.expire_ts:
                self.root.after(0, self._subscription_expired)
                break
            # сессия 2 часа — не переподключать после истечения лимита
            if self.session_seconds <= 0:
                continue
            if not self.xray_alive():
                failed += 1
                if failed >= 3:
                    self.root.after(0, self._reconnect_give_up)
                    break
                self.root.after(0, self._reconnect)
            else:
                failed = 0

    def _reconnect(self):
        if not self.connected:
            return
        self.set_status("Соединение разорвано. Переподключение...")
        try:
            if self.xray_alive():
                self.kill_xray()
            time.sleep(2)
            if not self.xray_alive():
                self.run_xray()
            time.sleep(2.5)
            if self.xray_alive():
                self.set_status("Переподключено к Англии ✔")
            else:
                self.set_status("Не удалось переподключиться. Пробую снова...")
        except Exception:
            self.set_status("Ошибка переподключения. Пробую снова...")

    def _reconnect_give_up(self):
        self.connected = False
        self.keepalive.clear()
        if self.timer_job:
            self.root.after_cancel(self.timer_job)
            self.timer_job = None
        if self.xray_alive():
            self.kill_xray()
        self.set_system_proxy(False)
        self.stop_btn.config(state="disabled")
        self.run_btn.config(state="normal")
        self.timer_text.set("Осталось: 02:00:00")
        self.set_status("Не удалось восстановить соединение. Нажмите «ЗАПУСТИТЬ ОБХОД» заново")

    def _subscription_expired(self):
        self.connected = False
        self.keepalive.clear()
        if self.xray_alive():
            self.kill_xray()
        self.set_system_proxy(False)
        self.stop_btn.config(state="disabled")
        self.run_btn.config(state="normal")
        self.code_entry.config(state="normal")
        self.apply_btn.config(state="normal")
        self.timer_text.set("Подписка истекла — жду новый код")
        self.set_status("Подписка завершена. Вставьте новый код ниже и нажмите «ПРИМЕНИТЬ КОД»")

    def apply_new_code(self):
        code = self.code_entry.get().strip()
        if not code:
            messagebox.showwarning("RECOVERY YOUTUBE", "Вставьте URL нового кода подписки")
            return
        self.set_status("Проверка нового кода...")
        self.apply_btn.config(state="disabled")
        threading.Thread(target=self._apply_code_worker, args=(code,), daemon=True).start()

    def _apply_code_worker(self, code):
        try:
            self.set_status("Проверяю новый код...")
            data = self.fetch_subscription(code)
            links = data.get("links", [])
            england = self.find_england_link(links)
            if not england:
                self.root.after(0, lambda: self._apply_failed(
                    "По коду не найдена ссылка на Англию (проверьте код)"))
                return
            self.active_url = code
            self.connected = False
            self.keepalive.clear()
            self.expire_ts = None
            self.root.after(0, lambda: self.timer_text.set("Новый код применён. Перезапуск соединения..."))
            self.root.after(0, self.start_bypass)
        except Exception as e:
            self.root.after(0, lambda: self._apply_failed(f"Ошибка: {e}"))

    def _apply_failed(self, msg):
        self.set_status(f"Не удалось применить код: {msg}")
        self.apply_btn.config(state="normal")
        messagebox.showerror("RECOVERY YOUTUBE", f"Не удалось применить код:\n{msg}")

    def format_bytes(self, n):
        n = max(int(n), 0)
        if n < 1024:
            return f"{n} B"
        for unit in ("KB", "MB", "GB", "TB"):
            n /= 1024.0
            if n < 1024:
                return f"{n:.1f} {unit}"
        return f"{n:.1f} PB"

    def query_xray_stats(self):
        # Xray API общается по gRPC — используем встроенную CLI-команду xray api
        try:
            out = subprocess.run(
                [self.XRAY_EXE, "api", "statsquery", "--server=127.0.0.1:10086"],
                capture_output=True, text=True, timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            text = (out.stdout or "").strip()
            data = json.loads(text) if text else {}
        except Exception:
            return self.last_up, self.last_down
        up = 0
        down = 0
        items = data.get("stat") or data.get("stats") or (
            data if isinstance(data, list) else []
        )
        for item in items:
            name = item.get("name", "")
            value = item.get("value", 0)
            if name.endswith(">>>traffic>>>uplink"):
                up += value
            elif name.endswith(">>>traffic>>>downlink"):
                down += value
        return up, down

    def update_stats(self):
        if not self.connected:
            if self.expire_ts and time.time() > self.expire_ts:
                self.timer_text.set("Подписка истекла — жду новый код")
            return
        if not self.xray_alive():
            self.timer_text.set("Соединение разорвано — переподключаюсь")
            return
        # сетевой запрос статистики — строго в фоновом потоке,
        # чтобы не блокировать UI («Не отвечает»)
        threading.Thread(target=self._stats_worker, daemon=True).start()
        self._schedule_stats()

    def _schedule_stats(self):
        self.timer_job = self.root.after(2000, self.update_stats)

    def _stats_worker(self):
        try:
            up, down = self.query_xray_stats()
        except Exception:
            up, down = self.last_up, self.last_down
        # обновить счётчики и таймер сессии в главном потоке
        self.root.after(0, lambda: self._apply_stats(up, down))

    def _apply_stats(self, up, down):
        self.updown_text.set(f"⬆ отдаёт {self.format_bytes(up)} | ⬇ получает {self.format_bytes(down)}")
        self.last_up = up
        self.last_down = down
        self.session_seconds -= 2  # интервал обновления — 2 секунды
        if self.session_seconds <= 0:
            self.timer_text.set("Лимит 2 часа истёк")
            self.stop_bypass()
            self.set_status("Сессия завершена (лимит 2 часа). Нажмите «ЗАПУСТИТЬ ОБХОД», чтобы снова подключиться")
            return
        self.timer_text.set(self.session_label())

    def verify_proxy(self):
        try:
            proxy_handler = urllib.request.ProxyHandler({
                "http": f"http://{PROXY_HOST}:{PROXY_HTTP_PORT}",
                "https": f"http://{PROXY_HOST}:{PROXY_HTTP_PORT}",
            })
            opener = urllib.request.build_opener(proxy_handler)
            opener.open("https://www.youtube.com/", timeout=15)
            self.root.after(0, lambda: self.set_status("Сервер Англия работает: YouTube доступен ✔"))
        except Exception:
            self.root.after(0, lambda: self.set_status("Туннель активен, но проверка без подтверждения"))

    def kill_xray(self):
        if self.xray_proc:
            try:
                self.xray_proc.kill()
            except Exception:
                pass
            self.xray_proc = None

    def stop_bypass(self):
        self.connected = False
        self.keepalive.clear()
        if self.timer_job:
            self.root.after_cancel(self.timer_job)
            self.timer_job = None
        if self.xray_alive():
            self.kill_xray()
        self.set_system_proxy(False)
        self.stop_btn.config(state="disabled")
        self.run_btn.config(state="normal")
        self.timer_text.set("Осталось: 02:00:00")
        self.set_status("Соединение остановлено")

    def _fail(self, msg):
        self.working = False
        self.run_btn.config(state="normal")
        self.set_status("Ошибка: " + msg)
        messagebox.showerror("RECOVERY YOUTUBE", f"Ошибка:\n{msg}")

    def on_close(self):
        try:
            if self.timer_job:
                self.root.after_cancel(self.timer_job)
            self.kill_xray()
            self.set_system_proxy(False)
        except Exception:
            pass
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    if sys.platform == "win32":
        hide_console()
    app = RecoveryYouTubeApp()
    app.run()