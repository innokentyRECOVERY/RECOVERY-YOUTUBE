# =====================================================================
# RECOVERY YOUTUBE
# Обход блокировки YouTube через VLESS-подписку (сервер: Англия)
# Split-tunnel: ТОЛЬКО youtube.com идут через VPN, остальное напрямую
# =====================================================================
import ctypes
import base64
import json
import io
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
import urllib.parse
import zipfile
import tkinter as tk
from tkinter import messagebox

try:
    import pystray
    import PIL.Image as PILImage
    from PIL import ImageTk as PILImageTk
    TRAY_AVAILABLE = True
except Exception:
    TRAY_AVAILABLE = False

SUBSCRIPTION_URL = "https://hubcom.xyz/sub/1/45ad8f39-8935-4027-9504-173b75d30893"
ENGLAND_FUSO_FLAG = "\u0410\u043d\u0433\u043b\u0438\u044f"
ENG_FRAG = "\U0001F1EC\U0001F1E7"  # флаг 🇬🇧 (Англия/Великобритания)

if getattr(sys, "frozen", False):
    # скомпилировано в .exe — работаем рядом с exe-файлом
    APP_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DATA_DIR = os.path.join(os.environ.get("APPDATA", APP_DIR), "RECOVERY_YOUTUBE")
SETTINGS_PATH = os.path.join(APP_DATA_DIR, "settings.json")
WORK_DIR_KEY = "work_dir"
DEFAULT_WORK_DIR = APP_DATA_DIR

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

TG_DOMAINS = [
    "telegram.org", "www.telegram.org", "web.telegram.org",
    "core.telegram.org", "cdn.telegram.org",
    "t.me", "telegram.me", "telegram.dog",
    "telesco.pe", "telegra.ph",
]

SERVICES = {
    "youtube": {
        "tab": "ОБХОД YOUTUBE",
        "title": "Обход блокировки YouTube",
        "domains": YT_DOMAINS,
        "check_url": "https://www.youtube.com/",
        "success": "Сервер Англия работает: YouTube доступен ✔",
        "note": "Через VPN идут только сайты YouTube.\nОстальной интернет не затрагивается.\nЛимит сессии: 2 часа — потом автоотключение и повторный запуск.",
    },
    "telegram": {
        "tab": "ОБХОД TELEGRAM",
        "title": "Обход блокировки Telegram",
        "domains": TG_DOMAINS,
        "check_url": "https://web.telegram.org/",
        "success": "Сервер Англия работает: Telegram доступен ✔",
        "note": "Через VPN идут только сайты Telegram и Telegram Desktop.\nОстальной интернет не затрагивается.\nЛимит сессии: 2 часа — потом автоотключение и повторный запуск.",
    },
}

INTERNET_SETTINGS_KEY = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"

SINGLE_INSTANCE_MUTEX = "Global\\RECOVERY_YOUTUBE_SINGLE_INSTANCE"

# Встроенная иконка приложения (PNG 64x64, base64) — для окна и системного трея
ICON_B64 = (
    "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"
)

APP_TRAY_ICON_BYTES = base64.b64decode(ICON_B64)

DOLLAR_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAYAAADDPmHLAAAJX0lEQVR4nO2de4xcVR3Hv/fOzM7szu7sbrd1oIAW0SU0C4rUFhpaIE2rBLUFmyhKAXlEIWApgUQemlraxv4D1epaRW0hSo2grTyCbbHCpq0pq2iL2KVpS+WhbNnn7M7O+15zLplmKbPbc2fu4/zOPZ9k0t3tmXvP/H7f+zuv3zkDKBQKhUKhCCIaAkDvwhvNat+b3LlZahtJ9eFqcXRQhUH6Q3jpcFkFQa7SIjldBjGQqSgFx1MUgtAVpOh0amIQslIyOV50IQhVGZkdL6oQdAhCkJwv0uf1XYWiGCKo0cDXCKCc778dfFGecrw40cDzCKCcL5Z9PBWAcr54dvIk3CjHi9skuB4BlPPFtp+rAlDOF9+OrglAOZ+GPV0RgHK+O7hhV8cFoJzvLk7b11EBKOd7g5N2dkwAyvne4pS9hVkNVPiDIwJQT78/OGF3LYjOn7a1E1q8/kN/P77oGwjabKEeNOfLSG8NflB9gIBTtQDU0y8W1fpDk935WrQOdbMvQOS8cxA++0zrpU9pqVjWGBhG8cib1iv/z4PWC4YBmfsD0gogMvMTqL/qckQvvQhafayqaxiDKeRe2oexp7ajdLwfFHBdAKI7X5/aisZbv4LYFXMcu6aZLyDzhx1Ib3kWZiYLmUSgyeT86PzPInHvLVbYd4PSW//D0HfXo/Tf45BFBNKMAhqWfh7ND9zmmvMZobNOR+uG7yHS8UnIgibD0x9ftgTxZYs9u585msbAt1ej9Pa7oB4FyEeA6GWzPXU+Q2uMo2XV8oqzidTQKT/9elsLEstv8OXeoTNPQ/z6qyEyPH4jHQEab1oKrbHBt/s3fGkBwh+dDsqQFUAoORWxBZfYek9u7z8weNcamOlMxf8fXrkBRt+gjUroaPC4+fFcAKKG/9iV8wGdT79msYjUup9jeOWPUPj34QnL5fa+gv5bH0Dx8H+46xGd+xnoTXGIyqn8RzYCxObN4i478vAmZP/8V66yZjqDofsfRqm3j6u8FgkjajMSiYRO8enXWxLWmJwH9lRnX9hr6/rGUArpXzzJXT46+1MQmcn8SDIChD9+FnfZsS3PVXWPbFc3ikff4iobmXkOoPl+1EJVkBRA6LSpXOWM4VEUDr1R3U1ME7k9f+cqqjXUW6uMFAlTC/8MLc439DOO91mOrJZ896vWFLPRPwRjcBilgeETPxsf+HkIRioNkWH+rDQzOKEAhEbnDLehUE23KfQcxXuLb4PMkGwCzBG+py10RhJamKbGvYKkAIzUKH820NwLXa+PdAIQuf1n2Jmta7zxGmusrkBFv5KMAMXDb1pZOryLNk333sI9axg0SFqFTe0We45yl49dPgctq1dMmAwaZEgKgJHbt99W+bpZHWj75VrEr1+iooEMAsj+qQtmLm/rPSyBI37dYmj1UdfqRQ2yAjBG0sju2OPoNcMfOwNBQ6M2AhiPPqUZUx5d4+hybKm3H/mX9yPX1Y38gddrmkkUlfEzgqQFUO7gJe7/livXNvqHkNmxG9nnu1B69z3IKACyTUCZ7Iv7kN2+27Wcw/i1X0DbY+vQ/ODttlYhqUBeAIzU+k3Wur9raJq16WTKT7+PxD03Q29uhCxIIQCUDAyv+gkyz/zF3ftoGmKLLrX6HWzDqQzIIQCGYWBkw+NIrd3IvVZQS0ZSy0N3oX7JQlBHHgGM6xMM3Hzf+9GgWHLvRpqGptu/htjn5oEy0gmgnAnEokE/E8K2F2Bmcq7dq+mO66z1BqqQHwbyoMWiiM6bhdhlsxG5cKbjq4PFQ8cwcOcqMnMGUg0DeTCzOWR37sHQg4+gb+kdju/xD7fPQPQSmnkHgRDAeKzmwJjgSTWrf4IbvrwIFAmcACaj79q7MdL5G5Te6bX93sj55yI0/SOghhLAOFh2L+s09t90H0Z++JjtpoKJgBpKAJUwTWSeexGDK9ZaIwpe6jraQQ0lgElgO4NS634GXkIzptMXgChfaiwK+b/9C/nuA1xl9Sbx1whO9q+KABzw7izWE+JuE58IcvnSbB8eSwTRW5tP/Bs68XvixN/Zrh524IMTFA4d4ysYpZdqRkoAbKPHtN//2DqZ41TUffo8a1cQyyD2aicSbOYoigCpJoAlgRaPvc0dKeoudmbfvsZ5Ghg7V4AapATAYKGdl4ZrnJmdC3NmAvGeKiK8AEQeCRR6jnCXjXS0Izqn9igQ5ZznZ6eMi0wlv5KLAPl9B6wMIF6alt8APVH98Cx0+jTErriYq2zhtYkPoBIVcgJg7Wz+lddsnR7evPLOqs4Q1sJhJL7zTSAc4uqf2KmXKJATgJ1x+fimoGXN3bb2D2jxejQ/tNz6ogke2D4CuzuVhBaAyP0AdnYPW7ixQ+SCc9G6cRWik5wXoMWi1u6ghq9ehbZNP0DdRR3c1x/buhMiM5E/J3WyyNlB9VfOR9MKMb7mLdfVjeHVnaAoAJJNACOzfTeKx97xuxpgB0uObNwCqkwqAJGbASsN/JFNMAu1z/TVQmr9ZnvnC/vAZH4kGwEYhYNHrMQNv0g/vg25l14GZU4pAKGjABsR7NiNsd9WdxpoLYw++jukf/1HiM6p/Ec6ApQZ/dVTGOl8wpvv+CuWrMOnx558HjJAajVwMjLbdlrJnNbmzdaEe03O+s0ovsG3IEUBKb406uRVwPjXv4j6qxc6dkikMTCE9BPPIvPMLjKbP3ibb2kiQBlzLGO1z5mnd1lfKhFbMBehZFtV1yq8+jrGnt71/qHRbu4z9BGpvjiyIppmTQXXnd+OcPvZiLTPsNYHJjoepnCgB/n9PSjsP2j9ThXezrt0EeBDmKb1JLNXmWlbOysmefQvuwdBw9YoQPQhocK+n2wPA5UIxMauf6SYB1BUT1UCUFFATKrxS9URQIlALKr1h2oCAk7NvXqScwOSkaxhdFZzBFBNgb/Uan9HmgAlAn9wwu6qDxBwHBOAigLe4pS9HY0ASgTe4KSdHW8ClAjcxWn7utIHUCJwBzfs6lonUImAhj1dHQUoEYhvR9eHgUoEYtvP0wQPNW0s3oPj6USQigbi2cnzmUAlArHs42uOn2oS/H8wfF0LUNHAfzsIk+UbxGiQFCDLWpjVQBGMEcTPK0QlghQNkoI4voxQlZFZCEnBHF9GyErJIoakoE4fj/AVpCiEJAHHlyFTUdHFkCTk9PGQrLQIgkgSdfjJSPEh3BRGUhJHKxQKhUKBD/J/MQCAuOvpETUAAAAASUVORK5CYII="
)

DOLLAR_IMAGE_BYTES = base64.b64decode(DOLLAR_B64)

# Встроенное фоновое изображение (spokoynich.jpg) — фон работает даже без файла рядом с exe
try:
    from bg_embedded_data import BG_IMAGE_BASE64
    EMBEDDED_BACKGROUND_BYTES = base64.b64decode("".join(BG_IMAGE_BASE64))
except Exception:
    EMBEDDED_BACKGROUND_BYTES = b""

# возможные имена файлов фона рядом с exe (первый найденный используется)
BACKGROUND_CANDIDATES = (
    "spokoynich.jpg", "спокойнич.jpg",
    "фон.jpg", "фон.png", "background.jpg", "background.png",
    "bg.jpg", "bg.png",
)


def _find_existing_hwnd():
    # ищем главное окно ЛЮБОЙ версии по заголовку "RECOVERY YOUTUBE ..."
    # (в т.ч. окно скрытое в трей). Это ловит и старые сборки без mutex.
    found = []
    user32 = ctypes.windll.user32
    EnumWindowsProc = ctypes.WINFUNCTYPE(
        ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    def callback(hwnd, lparam):
        try:
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                if buf.value.startswith("RECOVERY YOUTUBE"):
                    found.append(hwnd)
                    return False
        except Exception:
            pass
        return True

    try:
        proc = EnumWindowsProc(callback)
        user32.EnumWindows(proc, 0)
    except Exception:
        pass
    return found[0] if found else 0


def acquire_single_instance():
    # именованный mutex: гарантирует, что работает только один экземпляр.
    # Возвращает handle, если mutex создан, иначе None (уже запущен).
    try:
        handle = ctypes.windll.kernel32.CreateMutexW(None, False, SINGLE_INSTANCE_MUTEX)
        if not handle:
            return None
        if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            ctypes.windll.kernel32.CloseHandle(handle)
            return None
        # старые сборки не создают mutex — проверяем окно по заголовку
        if _find_existing_hwnd():
            ctypes.windll.kernel32.CloseHandle(handle)
            return None
        return handle
    except Exception:
        return None


def raise_existing_window():
    # вместо нового окна поднимаем уже запущенный экземпляр (в т.ч. из трея,
    # с другого рабочего стола или старую версию без mutex)
    try:
        hwnd = _find_existing_hwnd()
        if not hwnd:
            hwnd = ctypes.windll.user32.FindWindowW(
                None, "RECOVERY YOUTUBE v" + RecoveryYouTubeApp.VERSION)
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            ctypes.windll.user32.SetForegroundWindow(hwnd)
    except Exception:
        pass


def hide_console():
    try:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)
    except Exception:
        pass


def _sanitize_tcl_tk_env():
    # битые TCL_LIBRARY/TK_LIBRARY (часто хвост от старого .exe в _MEI*)
    # ломают tkinter: окно остаётся пустой рамкой без интерфейса
    for key, marker in (("TCL_LIBRARY", "init.tcl"), ("TK_LIBRARY", "tk.tcl")):
        val = os.environ.get(key)
        if not val:
            continue
        if os.path.isfile(os.path.join(val, marker)):
            continue
        os.environ.pop(key, None)
    if getattr(sys, "frozen", False):
        return
    prefix = getattr(sys, "base_prefix", sys.prefix)
    tcl = os.path.join(prefix, "tcl", "tcl8.6")
    tk = os.path.join(prefix, "tcl", "tk8.6")
    if "TCL_LIBRARY" not in os.environ and os.path.isfile(os.path.join(tcl, "init.tcl")):
        os.environ["TCL_LIBRARY"] = tcl
    if "TK_LIBRARY" not in os.environ and os.path.isfile(os.path.join(tk, "tk.tcl")):
        os.environ["TK_LIBRARY"] = tk


_sanitize_tcl_tk_env()


class RecoveryYouTubeApp:
    VERSION = "1.0.2.3"

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"RECOVERY YOUTUBE v{self.VERSION}")
        self.root.configure(bg="#1a1a2e")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.status_text = tk.StringVar(value="Готов к запуску")
        self.server_text = tk.StringVar(value="Сервер: Англия 🇬🇧")
        self.mode = "youtube"
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
        self.proxy_fail_count = 0
        self.proxy_ok = True
        self.folder_text = tk.StringVar(value="")

        self.work_dir = self.load_work_dir()
        self.ensure_work_dir()
        self.apply_work_dir()

        self._btns = []
        self.tray_icon = None
        self._exiting = False
        self._exit_when_disconnected = False
        self.root.geometry("560x680")
        self.build_ui()
        self.center_window()
        self.root.resizable(False, False)
        self.set_window_icon()
        self.setup_tray()

    def center_window(self):
        w, h = 560, 680
        self.root.minsize(w, h)
        self.canvas.config(width=w, height=h)
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - w) // 2
        y = max(0, (self.root.winfo_screenheight() - h) // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.update_idletasks()

    # ---------------- системный трей ----------------

    def tray_image(self):
        # встроенная иконка всегда доступна (ничего не читается с диска)
        try:
            return PILImage.open(io.BytesIO(APP_TRAY_ICON_BYTES)).convert("RGBA").resize((64, 64))
        except Exception:
            return PILImage.new("RGBA", (64, 64), (26, 26, 46, 255))

    def set_window_icon(self):
        # убирает стандартную иконку Python/tk в панели задач
        try:
            img = PILImage.open(io.BytesIO(APP_TRAY_ICON_BYTES)).convert("RGBA").resize((64, 64))
            photo = PILImageTk.PhotoImage(img)
            self.root.iconphoto(True, photo)
            self._window_icon = photo  # не даём GC удалить фото
        except Exception:
            pass

    def setup_tray(self):
        if not TRAY_AVAILABLE:
            return
        try:
            menu = pystray.Menu(
                pystray.MenuItem("Показать окно", self.show_window, default=True),
                pystray.MenuItem("Выход", self.full_exit),
            )
            self.tray_icon = pystray.Icon(
                "RECOVERY_YOUTUBE", self.tray_image(), "RECOVERY YOUTUBE", menu)
        except Exception:
            self.tray_icon = None

    def ensure_tray_running(self):
        if self.tray_icon is not None and not self._exiting:
            try:
                if not self.tray_icon.visible:
                    self.tray_icon.run_detached()
            except Exception:
                pass

    def show_window(self, icon=None, item=None):
        self.root.after(0, self.root.deiconify)
        self.root.after(0, self.root.lift)
        self.root.after(0, self.root.focus_force)

    def hide_to_tray(self):
        self.root.withdraw()
        self.ensure_tray_running()

    def full_exit(self, icon=None, item=None):
        self._exiting = True
        try:
            if self.working:
                self.stop_bypass(user_stopped=True)
        except Exception:
            pass
        try:
            if self.tray_icon is not None:
                self.tray_icon.stop()
        except Exception:
            pass
        self.root.after(0, self._really_close)

    def _really_close(self):
        try:
            if self.timer_job:
                self.root.after_cancel(self.timer_job)
            self.kill_xray()
            self.set_system_proxy(False)
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass
        # принудительно завершаем процесс: поток трея pystray не позволяет
        # интерпретатору выйти самому
        os._exit(0)

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

    def ensure_work_dir(self):
        try:
            os.makedirs(self.work_dir, exist_ok=True)
        except Exception:
            self.work_dir = DEFAULT_WORK_DIR
            try:
                os.makedirs(self.work_dir, exist_ok=True)
            except Exception:
                pass

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
        self.migrate_existing_xray()
        self.folder_text.set(self.work_dir)

    def migrate_existing_xray(self):
        # если xray лежит рядом с exe (старая схема), переносим в новую папку —
        # чтобы не качать заново
        try:
            if os.path.exists(self.XRAY_EXE):
                return
            legacy = os.path.join(APP_DIR, "xray", "xray.exe")
            if not os.path.exists(legacy):
                legacy = os.path.join(APP_DIR, "xray.exe")
            if os.path.exists(legacy):
                os.makedirs(self.work_dir, exist_ok=True)
                shutil.copy2(legacy, self.XRAY_EXE)
        except Exception:
            pass

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

    # ---------------- canvas UI helpers ----------------

    def _load_background(self):
        # фон интерфейса — картинка из файла рядом с exe (или в папке xray);
        # если файла нет, остаётся тёмный фон окна
        for name in BACKGROUND_CANDIDATES:
            for base in (self.work_dir, APP_DIR):
                p = os.path.join(base, name)
                try:
                    if os.path.exists(p):
                        img = PILImage.open(p).convert("RGB").resize(
                            (560, 680), PILImage.LANCZOS)
                        dim = PILImage.new("RGB", img.size, (10, 10, 20))
                        img = PILImage.blend(img, dim, 0.55)
                        photo = PILImageTk.PhotoImage(img)
                        self._bg_photo = photo  # не даём GC удалить фото
                        return photo
                except Exception:
                    continue
        # если файла рядом нет — используем встроенный фон (base64 в exe)
        if EMBEDDED_BACKGROUND_BYTES:
            try:
                img = PILImage.open(io.BytesIO(EMBEDDED_BACKGROUND_BYTES)).convert(
                    "RGB").resize((560, 680), PILImage.LANCZOS)
                dim = PILImage.new("RGB", img.size, (10, 10, 20))
                img = PILImage.blend(img, dim, 0.55)
                photo = PILImageTk.PhotoImage(img)
                self._bg_photo = photo  # не даём GC удалить фото
                return photo
            except Exception:
                pass
        return None

    def _dollar_photo(self, size=26):
        try:
            img = PILImage.open(io.BytesIO(DOLLAR_IMAGE_BYTES)).convert("RGBA").resize((size, size))
            photo = PILImageTk.PhotoImage(img)
            self._dollar_photo_ref = photo
            return photo
        except Exception:
            return None

    def _attach_var(self, item, var):
        # StringVar -> обновление canvas-текста
        try:
            var.trace_add("write", lambda *a, it=item, v=var: self.canvas.itemconfig(it, text=v.get()))
        except Exception:
            pass

    def _add_btn(self, x1, y1, x2, y2, text, command, font, enabled=True, color="#4fc3f7"):
        # прозрачная кнопка: пустой фон (виден фон окна), контур + текст.
        # Клики обрабатываются хит-тестом по всей области прямоугольника,
        # а не только по тексту/контуру (см. _on_canvas_click).
        rect = self.canvas.create_rectangle(
            x1, y1, x2, y2, outline=color, width=2, fill="")
        txt = self.canvas.create_text(
            (x1 + x2) / 2, (y1 + y2) / 2, text=text, fill="#ffffff", font=font, justify="center")
        state = {"enabled": enabled}
        self._btns.append({"x1": x1, "y1": y1, "x2": x2, "y2": y2,
                           "state": state, "command": command})
        d = {"rect": rect, "text": txt, "state": state, "color": color}
        if not enabled:
            self._set_btn(d, False)
        return d

    def _add_round_btn(self, cx, cy, r, command, enabled=True, color="#4fc3f7"):
        # круглая кнопка: окружность + иконка питания (⏻) вместо текста.
        # Клики обрабатываются круговым хит-тестом (см. _on_canvas_click).
        outline_items = []
        fill_items = []
        oval = self.canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r, outline=color, width=2, fill="")
        outline_items.append(oval)
        # иконка питания: дуга окружности (разрыв сверху) + вертикальная линия
        ir = r * 0.42
        w = max(2, int(r * 0.09))
        arc = self.canvas.create_arc(
            cx - ir, cy - ir, cx + ir, cy + ir,
            start=30, extent=300, style="arc", outline=color, width=w)
        outline_items.append(arc)
        stem = self.canvas.create_line(
            cx, cy - ir * 1.2, cx, cy + ir * 0.62,
            fill=color, width=w)
        fill_items.append(stem)
        state = {"enabled": enabled}
        self._btns.append({"circle": (cx, cy, r),
                           "state": state, "command": command})
        d = {"oval": oval, "circle": (cx, cy, r), "state": state,
             "color": color, "outline_items": outline_items,
             "fill_items": fill_items}
        if not enabled:
            self._set_btn(d, False)
        return d

    def _on_canvas_click(self, e):
        # хит-тест: клик срабатывает по всей площади кнопки, даже если в
        # прозрачной области внутри контура (там нет текста/заливки)
        x, y = e.x, e.y
        for b in self._btns:
            if not b["state"]["enabled"] or not b["command"]:
                continue
            if "circle" in b:
                cx, cy, r = b["circle"]
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    b["command"]()
                    break
            elif b["x1"] <= x <= b["x2"] and b["y1"] <= y <= b["y2"]:
                b["command"]()
                break

    def _set_btn(self, d, enabled):
        d["state"]["enabled"] = enabled
        col = d.get("color", "#4fc3f7") if enabled else "#666666"
        for it in d.get("outline_items", []):
            try:
                self.canvas.itemconfig(it, outline=col)
            except Exception:
                pass
        for it in d.get("fill_items", []):
            try:
                self.canvas.itemconfig(it, fill=col)
            except Exception:
                pass
        if "rect" in d and d.get("rect"):
            self.canvas.itemconfig(d["rect"], outline=col)
        if d.get("text"):
            self.canvas.itemconfig(d["text"], fill="#ffffff")

    def _set_tab_active(self, mode, active):
        d = self.tab_items.get(mode)
        if not d:
            return
        col = "#e94560" if active else "#4fc3f7"
        d["color"] = col
        self.canvas.itemconfig(d["rect"], outline=col)
        self.canvas.itemconfig(d["text"], fill="#ffffff")

    BLUE = "#4fc3f7"
    RED = "#e94560"

    def build_ui(self):
        # единый canvas: фон-картинка + все элементы (прозрачные кнопки)
        self.canvas = tk.Canvas(self.root, width=560, height=680,
                                bg="#1a1a2e", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        photo = self._load_background()
        if photo is not None:
            self.canvas.create_image(0, 0, anchor="nw", image=photo)

        btn_font = ("Arial", 11, "bold")

        # вкладки ОБХОД YOUTUBE / ОБХОД TELEGRAM
        self.tab_items = {}
        tab_pos = {"youtube": (30, 14, 180, 56),
                   "telegram": (190, 14, 355, 56)}
        for key, (x1, y1, x2, y2) in tab_pos.items():
            svc = SERVICES[key]
            d = self._add_btn(x1, y1, x2, y2, svc["tab"],
                              lambda k=key: self.switch_mode(k),
                              ("Arial", 12, "bold"))
            self.tab_items[key] = d
        self._set_tab_active(self.mode, True)

        # вкладка «Путь милионера» — с долларом, открывает донаты
        dx1, dy1, dx2, dy2 = 365, 14, 540, 56
        drect = self.canvas.create_rectangle(
            dx1, dy1, dx2, dy2, outline=self.RED, width=2, fill="")
        dphoto = self._dollar_photo(24)
        dimg = None
        if dphoto is not None:
            dimg = self.canvas.create_image(
                (dx1 + dx2) / 2, dy1 + 14, image=dphoto)
        dtext = self.canvas.create_text(
            (dx1 + dx2) / 2, dy1 + 34, text="Путь милионера",
            font=("Arial", 9, "bold"), fill="#ffffff")
        self._btns.append({"x1": dx1, "y1": dy1, "x2": dx2, "y2": dy2,
                           "state": {"enabled": True}, "command": self.open_donation})
        self.dollar_tab = {"rect": drect, "img": dimg, "text": dtext}

        # глобальный хит-тест: клики срабатывают по всей площади кнопок
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        # заголовок RECOVERY YOUTUBE
        self.canvas.create_text(280, 96, text="RECOVERY YOUTUBE",
                                font=("Arial", 26, "bold"), fill="#ffffff")

        # подзаголовок выбранного сервиса (textvariable)
        self.subtitle_text = tk.StringVar(value=SERVICES[self.mode]["title"])
        sub_it = self.canvas.create_text(280, 130, text=self.subtitle_text.get(),
                                         font=("Arial", 13), fill="#ffffff")
        self._attach_var(sub_it, self.subtitle_text)

        # сервер
        sv_it = self.canvas.create_text(280, 160, text=self.server_text.get(),
                                        font=("Arial", 14, "bold"), fill="#ffffff")
        self._attach_var(sv_it, self.server_text)

        # кнопка ЗАПУСТИТЬ — круглая с иконкой питания; ОСТАНОВИТЬ — обычная
        self.run_btn = self._add_round_btn(
            280, 202, 46, self.start_bypass,
            enabled=True, color="#4fc3f7")
        self.stop_btn = self._add_btn(
            170, 262, 390, 304, "ОСТАНОВИТЬ",
            lambda: self.stop_bypass(user_stopped=True),
            ("Arial", 14, "bold"), enabled=False, color="#b33939")

        # статус
        st_it = self.canvas.create_text(280, 322, text=self.status_text.get(),
                                        font=("Arial", 12), fill="#ffffff", width=500)
        self._attach_var(st_it, self.status_text)

        # скорость / таймер
        self.updown_text = tk.StringVar(value="⬆ 0 B | ⬇ 0 B")
        self.timer_text = tk.StringVar(value="Осталось: 02:00:00")
        ud_it = self.canvas.create_text(280, 352, text=self.updown_text.get(),
                                        font=("Consolas", 13, "bold"), fill="#ffffff")
        self._attach_var(ud_it, self.updown_text)
        tm_it = self.canvas.create_text(280, 378, text=self.timer_text.get(),
                                        font=("Consolas", 13, "bold"), fill="#ffffff")
        self._attach_var(tm_it, self.timer_text)

        # папка xray + кнопка выбора
        f_it = self.canvas.create_text(280, 404, text=self.folder_text.get(),
                                       font=("Arial", 8), fill="#ffffff", width=470)
        self._attach_var(f_it, self.folder_text)
        self.folder_btn = self._add_btn(
            150, 418, 410, 448, "📁 Выбрать папку для xray", self.pick_work_dir,
            ("Arial", 10, "bold"), color="#a0a0b8")

        # поле нового кода подписки
        self.canvas.create_text(280, 474, text="Новый код подписки:",
                                font=("Arial", 10), fill="#ffffff")
        self.code_entry = tk.Entry(
            self.root, width=56, font=("Arial", 10), state="normal",
            bg="#16213e", fg="white", insertbackground="white", disabledbackground="#16213e",
            disabledforeground="#8a8aa0")
        self.code_entry.bind("<Return>", lambda e: self.apply_new_code())
        self.canvas.create_window(280, 496, window=self.code_entry, width=400, height=26)
        self.apply_btn = self._add_btn(
            180, 520, 380, 552, "ПРИМЕНИТЬ КОД", self.apply_new_code,
            ("Arial", 11, "bold"), enabled=True, color="#a0a0b8")

        # заметка снизу (сервисе-зависимая)
        self.note_text = tk.StringVar(value=SERVICES[self.mode]["note"])
        n_it = self.canvas.create_text(280, 640, text=self.note_text.get(),
                                       font=("Arial", 10), fill="#ffffff", justify="center", width=500)
        self._attach_var(n_it, self.note_text)

    def open_donation(self):
        # вкладка «Путь милионера» — открыть страницу донейшенов в основном браузере
        try:
            subprocess.Popen(
                ["rundll32", "url.dll,FileProtocolHandler",
                 "https://www.donationalerts.com/r/scallyspaxe"],
                creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception:
            pass

    def switch_mode(self, mode):
        if mode == self.mode:
            return
        if self.working or self.connected:
            messagebox.showinfo(
                "RECOVERY",
                "Сначала остановите текущее соединение, затем переключите вкладку.",
            )
            return
        self.mode = mode
        svc = SERVICES[mode]
        self.subtitle_text.set(svc["title"])
        self.note_text.set(svc["note"])
        for key in self.tab_items:
            self._set_tab_active(key, key == mode)
        self.server_text.set("Сервер: Англия 🇬🇧")
        self.set_status("Готов к запуску")

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
                        "domain": SERVICES[self.mode]["domains"],
                    },
                    {"type": "field", "outboundTag": "direct", "network": "tcp,udp"},
                ],
            },
        }
        return config

    # ---------------- xray management ----------------

    def download_xray(self):
        if os.path.exists(self.XRAY_EXE):
            self.set_status("xray-core уже установлен")
            return
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
        self._set_btn(self.run_btn, False)
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
        self._set_btn(self.stop_btn, True)
        self.session_seconds = 2 * 60 * 60
        self.timer_text.set(self.session_label())
        self.set_status("Подключено (Англия). Проверяю связь с сервером...")
        self.update_stats()

        def _initial_check():
            ok = self.verify_proxy()
            if ok and self.connected:
                self.root.after(
                    0, lambda: self.set_status(SERVICES[self.mode]["success"]))

        threading.Thread(target=_initial_check, daemon=True).start()
        threading.Thread(target=self._keepalive_loop, daemon=True).start()
        threading.Thread(target=self._proxy_monitor, daemon=True).start()

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
        self._set_btn(self.stop_btn, False)
        self._set_btn(self.run_btn, True)
        self.timer_text.set("Осталось: 02:00:00")
        self.set_status("Не удалось восстановить соединение. Нажмите «ЗАПУСТИТЬ ОБХОД» заново")
        self.maybe_exit_after_disconnect()

    def _server_unreachable(self):
        # xray-процесс жив, но YouTube через прокси не открывается —
        # значит проблема на стороне сервера/подписки, а не локальная
        self.connected = False
        self.keepalive.clear()
        if self.timer_job:
            self.root.after_cancel(self.timer_job)
            self.timer_job = None
        if self.xray_alive():
            self.kill_xray()
        self.set_system_proxy(False)
        self.working = False
        self._set_btn(self.stop_btn, False)
        self._set_btn(self.run_btn, True)
        self.timer_text.set("Осталось: 02:00:00")
        self.set_status("Сервер не отвечает — отключён, подписка закончилась " 
                        "(оплата/истекла) или возможен DDoS")
        messagebox.showwarning(
            "RECOVERY YOUTUBE",
            "Сервер Англия не отвечает.\n\n"
            "Возможные причины:\n"
            "• подписка закончилась / не оплачена — введите новый код подписки;\n"
            "• сервер временно отключён или перегружен (возможно DDoS-атака);\n"
            "• изменились параметры доступа к серверу.\n\n"
            "Попробуйте позже или введите новый код подписки.")
        self.maybe_exit_after_disconnect()

    def _subscription_expired(self):
        self.connected = False
        self.keepalive.clear()
        if self.xray_alive():
            self.kill_xray()
        self.set_system_proxy(False)
        self._set_btn(self.stop_btn, False)
        self._set_btn(self.run_btn, True)
        self.code_entry.config(state="normal")
        self._set_btn(self.apply_btn, True)
        self.timer_text.set("Подписка истекла — жду новый код")
        self.set_status("Подписка завершена. Вставьте новый код ниже и нажмите «ПРИМЕНИТЬ КОД»")
        self.maybe_exit_after_disconnect()

    def apply_new_code(self):
        code = self.code_entry.get().strip()
        if not code:
            messagebox.showwarning("RECOVERY YOUTUBE", "Вставьте URL нового кода подписки")
            return
        self.set_status("Проверка нового кода...")
        self._set_btn(self.apply_btn, False)
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
        self._set_btn(self.apply_btn, True)
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
            opener.open(SERVICES[self.mode]["check_url"], timeout=12)
            return True
        except Exception:
            return False

    def _proxy_monitor(self):
        # фоновый контроль реальной доступности YouTube через прокси.
        # Если xray жив, но YouTube через прокси не открывается — это сервер
        # молчит (подписка/оплата/DDoS), а не локальная ошибка.
        failed = 0
        while self.keepalive.is_set() and self.connected:
            time.sleep(25)
            if not self.connected:
                break
            if not self.xray_alive():
                continue
            ok = self.verify_proxy()
            if ok:
                failed = 0
                self.proxy_ok = True
            else:
                failed += 1
                self.proxy_ok = False
                if failed >= 3:
                    self.root.after(0, self._server_unreachable)
                    break
        self.proxy_ok = True
        self.proxy_fail_count = 0

    def kill_xray(self):
        if self.xray_proc:
            try:
                self.xray_proc.kill()
            except Exception:
                pass
            self.xray_proc = None

    def stop_bypass(self, user_stopped=False):
        self.connected = False
        self.keepalive.clear()
        if self.timer_job:
            self.root.after_cancel(self.timer_job)
            self.timer_job = None
        if self.xray_alive():
            self.kill_xray()
        self.set_system_proxy(False)
        self._set_btn(self.stop_btn, False)
        self._set_btn(self.run_btn, True)
        self.timer_text.set("Осталось: 02:00:00")
        self.set_status("Соединение остановлено")
        # автоматическое отключение (лимит времени, обрыв связи) при закрытом
        # в трей окне завершает приложение; ручная кнопка «ОСТАНОВИТЬ» — никогда
        if not user_stopped:
            self.maybe_exit_after_disconnect()

    def _fail(self, msg):
        self.working = False
        self._set_btn(self.run_btn, True)
        self.set_status("Ошибка: " + msg)
        self.maybe_exit_after_disconnect()
        if not self._exiting:
            messagebox.showerror("RECOVERY YOUTUBE", f"Ошибка:\n{msg}")

    def on_close(self):
        # кнопка «закрыть» (X):
        #  - если соединение активно — сворачиваем в трей и отслеживаем:
        #    как только соединение отключится, приложение закроется само;
        #  - если соединения нет — полностью закрываем приложение.
        if self.connected or self.working:
            self._exit_when_disconnected = True
            self.hide_to_tray()
        else:
            self._exit_when_disconnected = False
            self.full_exit()

    def maybe_exit_after_disconnect(self):
        # вызывается после остановки соединения: если пользователь закрыл
        # окно (X) и ждёт отключения в трее — теперь выходим полностью
        if self._exiting:
            return
        if self._exit_when_disconnected:
            self._exit_when_disconnected = False
            self.full_exit()

    def run(self):
        self.ensure_tray_running()
        self.center_window()
        self.root.deiconify()
        self.root.lift()
        self.root.mainloop()


if __name__ == "__main__":
    if sys.platform == "win32":
        hide_console()
    mutex = acquire_single_instance()
    if mutex is None:
        raise_existing_window()
        sys.exit(0)
    app = RecoveryYouTubeApp()
    app.run()