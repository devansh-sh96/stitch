"""
getting_data.py - Windows System, Process, App Discovery Engine & App Screen Time Tracker
Extracts running processes, open windows, installed applications, native system icons,
and tracks foreground app usage duration.
"""

import os
import glob
import time
import json
import psutil
import subprocess
import webbrowser
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import win32gui
    import win32process
    import win32con
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

from PySide6 import QtCore, QtGui, QtWidgets

USAGE_FILE = Path(__file__).parent / "app_usage.json"


class AppUsageTracker:
    """Tracks and persists how much time the user spends inside each application."""
    _instance = None

    def __init__(self):
        self.usage_seconds: Dict[str, float] = {}
        self.last_foreground_app: Optional[str] = None
        self.last_timestamp: float = time.time()
        self._load_usage()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_usage(self):
        if USAGE_FILE.exists():
            try:
                with open(USAGE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.usage_seconds = data.get("usage_seconds", {})
            except Exception:
                self.usage_seconds = {}

    def save_usage(self):
        try:
            with open(USAGE_FILE, "w", encoding="utf-8") as f:
                json.dump({"usage_seconds": self.usage_seconds, "last_updated": time.time()}, f, indent=2)
        except Exception:
            pass

    def tick_foreground(self):
        """Called periodically (e.g. every 1-2s) to update active foreground app time."""
        now = time.time()
        delta = now - self.last_timestamp
        self.last_timestamp = now

        if not HAS_WIN32:
            return

        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd and win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd).strip()
                if title and title not in ("Program Manager", "Default IME"):
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    proc = psutil.Process(pid)
                    app_name = proc.name().replace(".exe", "").capitalize()
                    if app_name:
                        # Add elapsed delta to this app
                        self.usage_seconds[app_name] = self.usage_seconds.get(app_name, 0.0) + min(delta, 10.0)
                        self.last_foreground_app = app_name
        except Exception:
            pass

    def get_top_used_apps(self, limit: int = 6) -> List[Dict[str, Any]]:
        """Returns sorted list of most used apps with formatted duration and percentage."""
        # Ensure at least some default demo time exists if empty
        if not self.usage_seconds:
            self.usage_seconds = {
                "Code": 1820.0,
                "Chrome": 2640.0,
                "Notion": 1120.0,
                "Spotify": 940.0
            }

        sorted_items = sorted(self.usage_seconds.items(), key=lambda x: x[1], reverse=True)[:limit]
        total_time = sum(v for _, v in sorted_items) or 1.0

        results = []
        for name, secs in sorted_items:
            mins = int(secs // 60)
            hours = mins // 60
            remaining_mins = mins % 60
            if hours > 0:
                duration_str = f"{hours}h {remaining_mins}m"
            else:
                duration_str = f"{max(1, remaining_mins)}m"

            percent = min(100, int((secs / total_time) * 100))
            results.append({
                "name": name,
                "duration_str": duration_str,
                "raw_seconds": secs,
                "percent": percent
            })
        return results


class AppIconCache:
    """Extracts and caches native Windows QIcon objects."""
    _instance = None
    _provider = None
    _cache = {}

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
            cls._provider = QtWidgets.QFileIconProvider()
        return cls._instance

    def get_icon_for_path(self, file_path: str) -> QtGui.QIcon:
        if not file_path:
            return self._get_fallback_icon("default")

        clean_path = str(file_path).strip()
        if clean_path in self._cache:
            return self._cache[clean_path]

        try:
            if os.path.exists(clean_path):
                file_info = QtCore.QFileInfo(clean_path)
                icon = self._provider.icon(file_info)
                if not icon.isNull():
                    self._cache[clean_path] = icon
                    return icon
        except Exception:
            pass

        return self._get_fallback_icon(clean_path)

    def _get_fallback_icon(self, name: str) -> QtGui.QIcon:
        pixmap = QtGui.QPixmap(48, 48)
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        hue = abs(hash(name)) % 360
        bg_color = QtGui.QColor.fromHsv(hue, 160, 220)

        painter.setBrush(QtGui.QBrush(bg_color))
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawRoundedRect(2, 2, 44, 44, 12, 12)

        painter.setPen(QtGui.QColor("#ffffff"))
        font = QtGui.QFont("Segoe UI", 16, QtGui.QFont.Bold)
        painter.setFont(font)
        initial = name.strip()[:1].upper() if name.strip() else "A"
        painter.drawText(QtCore.QRect(0, 0, 48, 48), QtCore.Qt.AlignCenter, initial)
        painter.end()

        return QtGui.QIcon(pixmap)


def get_running_statuses() -> Dict[str, bool]:
    running_names = set()
    for proc in psutil.process_iter(['name']):
        try:
            name = proc.info['name']
            if name:
                running_names.add(name.lower())
        except Exception:
            pass

    key_apps = ["code.exe", "notion.exe", "spotify.exe", "discord.exe", "chrome.exe", "msedge.exe"]
    return {app: (app in running_names) for app in key_apps}


def get_running_applications() -> List[Dict[str, Any]]:
    running_apps = []
    seen_hwnds = set()
    seen_pids = set()

    if HAS_WIN32:
        def enum_windows_callback(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd):
                return
            if win32gui.GetWindowTextLength(hwnd) == 0:
                return

            ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            if ex_style & win32con.WS_EX_TOOLWINDOW:
                return

            title = win32gui.GetWindowText(hwnd).strip()
            if not title or title in ("Program Manager", "Default IME", "MSCTFIME UI"):
                return

            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                proc = psutil.Process(pid)
                exe_path = proc.exe()
                name = proc.name()
                mem_mb = round(proc.memory_info().rss / (1024 * 1024), 1)

                if "svchost.exe" in name.lower() or "dwm.exe" in name.lower() or "explorer.exe" == name.lower() and not title:
                    return

                if hwnd not in seen_hwnds:
                    seen_hwnds.add(hwnd)
                    seen_pids.add(pid)
                    running_apps.append({
                        "name": Path(exe_path).stem if exe_path else name.replace(".exe", ""),
                        "title": title,
                        "process_name": name,
                        "pid": pid,
                        "hwnd": hwnd,
                        "exe": exe_path,
                        "mem_mb": mem_mb,
                        "is_running": True
                    })
            except Exception:
                pass

        try:
            win32gui.EnumWindows(enum_windows_callback, None)
        except Exception:
            pass

    if len(running_apps) < 4:
        for proc in psutil.process_iter(['pid', 'name', 'exe', 'memory_info']):
            try:
                pid = proc.info['pid']
                if pid in seen_pids or pid <= 4:
                    continue
                name = proc.info['name'] or ""
                exe = proc.info['exe'] or ""
                if not exe or exe.lower().startswith("c:\\windows\\system32"):
                    continue

                mem_mb = round(proc.info['memory_info'].rss / (1024 * 1024), 1)
                seen_pids.add(pid)
                running_apps.append({
                    "name": Path(exe).stem if exe else name.replace(".exe", ""),
                    "title": name,
                    "process_name": name,
                    "pid": pid,
                    "hwnd": None,
                    "exe": exe,
                    "mem_mb": mem_mb,
                    "is_running": True
                })
            except Exception:
                pass

    return running_apps


def get_installed_applications() -> List[Dict[str, Any]]:
    apps = []
    seen_names = set()

    presets = [
        {"name": "VS Code", "target": "vscode://", "category": "Development", "tags": "code editor programming python"},
        {"name": "Google Chrome", "target": "chrome.exe", "category": "Productivity", "tags": "browser internet web"},
        {"name": "Notion", "target": "notion://", "category": "Productivity", "tags": "notes docs wiki tasks"},
        {"name": "Spotify", "target": "spotify:", "category": "Media & Audio", "tags": "music audio podcast lofi"},
        {"name": "Discord", "target": "discord://", "category": "Communication", "tags": "chat community voice gaming"},
        {"name": "Google AI Studio", "target": "https://aistudio.google.com", "category": "AI & Tools", "tags": "ai llm gemini prompts"},
        {"name": "GitHub", "target": "https://github.com", "category": "Development", "tags": "git repo code development"},
        {"name": "ChatGPT", "target": "https://chatgpt.com", "category": "AI & Tools", "tags": "ai llm openai gpt"},
        {"name": "YouTube", "target": "https://youtube.com", "category": "Media & Audio", "tags": "video media streaming music"},
        {"name": "Terminal", "target": "wt.exe", "category": "Development", "tags": "terminal powershell bash cmd cli"},
        {"name": "Notepad", "target": "notepad.exe", "category": "Productivity", "tags": "text editor scratch notes"},
        {"name": "Calculator", "target": "calc.exe", "category": "Tools", "tags": "calculator math numbers"},
    ]

    for p in presets:
        seen_names.add(p["name"].lower())
        apps.append({
            "name": p["name"],
            "target": p["target"],
            "category": p["category"],
            "tags": p["tags"],
            "icon_path": p["target"] if not p["target"].startswith("http") else None,
            "is_preset": True
        })

    search_dirs = [
        os.path.expandvars(r'%ProgramData%\Microsoft\Windows\Start Menu\Programs'),
        os.path.expandvars(r'%AppData%\Microsoft\Windows\Start Menu\Programs'),
        os.path.expandvars(r'%UserProfile%\Desktop'),
        r'C:\Users\Public\Desktop'
    ]

    for sdir in search_dirs:
        if not os.path.exists(sdir):
            continue

        for ext in ("*.lnk", "*.url"):
            for shortcut_path in glob.glob(f"{sdir}/**/{ext}", recursive=True):
                stem = Path(shortcut_path).stem
                clean_name = stem.replace(" Shortcut", "").replace(" - Shortcut", "")

                lower_stem = clean_name.lower()
                if any(skip in lower_stem for skip in ("uninstall", "help", "readme", "documentation", "configure", "setup")):
                    continue

                if lower_stem in seen_names:
                    continue

                seen_names.add(lower_stem)

                category = "Productivity"
                if any(k in lower_stem for k in ("code", "studio", "git", "python", "terminal", "powershell", "dev", "cmd")):
                    category = "Development"
                elif any(k in lower_stem for k in ("spotify", "music", "vlc", "player", "audacity", "media", "audio", "video", "obs")):
                    category = "Media & Audio"
                elif any(k in lower_stem for k in ("discord", "slack", "zoom", "teams", "telegram", "whatsapp", "mail")):
                    category = "Communication"
                elif any(k in lower_stem for k in ("paint", "photoshop", "figma", "illustrator", "blender", "gimp", "canva")):
                    category = "Design"
                elif any(k in lower_stem for k in ("cleaner", "antivirus", "update", "control", "calc", "settings", "task")):
                    category = "Tools"

                apps.append({
                    "name": clean_name,
                    "target": shortcut_path,
                    "category": category,
                    "tags": f"{clean_name.lower()} app program shortcut",
                    "icon_path": shortcut_path,
                    "is_preset": False
                })

    apps.sort(key=lambda x: (not x.get("is_preset", False), x["name"].lower()))
    return apps


def launch_application(target: str, hwnd: Optional[int] = None) -> bool:
    try:
        if hwnd and HAS_WIN32 and win32gui.IsWindow(hwnd):
            try:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)
                return True
            except Exception:
                pass

        clean_target = str(target).strip()
        if clean_target.startswith(("http://", "https://")):
            webbrowser.open(clean_target)
            return True
        elif clean_target.endswith((".lnk", ".url")) or ":" in clean_target:
            os.startfile(clean_target)
            return True
        else:
            try:
                os.startfile(clean_target)
                return True
            except Exception:
                subprocess.Popen(clean_target, shell=True)
                return True
    except Exception as e:
        print(f"Failed to launch {target}: {e}")
        try:
            webbrowser.open(f"https://www.google.com/search?q={target}")
            return True
        except Exception:
            return False


def get_live_desktop_summary() -> str:
    apps = get_running_applications()
    if not apps:
        return "No foreground desktop applications detected."

    summary_lines = []
    for app in apps[:10]:
        title = app.get("title") or app.get("name")
        mem = app.get("mem_mb", 0)
        summary_lines.append(f"- {title} (Process: {app.get('process_name')}, RAM: {mem} MB)")

    return "\n".join(summary_lines)
