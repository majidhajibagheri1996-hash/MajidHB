"""
Bubu & Dudu - a tiny desktop pet for Windows.

* Bubu (left) types on a little keyboard whenever YOU type.
* Dudu (right) moves a little mouse whenever YOU move/click the mouse.
* After a while with no input they fall asleep; now and then they share a heart.

Controls
  - Left-drag  : move them anywhere on the screen
  - Right-click: menu (size, snap to a corner, always-on-top, start with Windows, exit)

Privacy: the app only checks *whether* some key is pressed (it never stores,
logs or sends which key). Nothing leaves your computer.

Only the Python standard library is used (tkinter + ctypes), so it runs with a
plain Python install and also builds into a single .exe with PyInstaller.
"""

import ctypes
import json
import math
import os
import random
import sys
import time
import tkinter as tk

IS_WIN = sys.platform.startswith("win")
APP_NAME = "BubuDudu"

# ----------------------------------------------------------------------------
# Look & feel (edit these if you want different colours)
# ----------------------------------------------------------------------------
KEY_COLOR = "#ff00fe"   # used as the "transparent" colour of the window
W, H = 320, 185         # base canvas size (multiplied by the size factor)
OUTLINE = "#3b2a22"

BUBU = dict(  # brown bear - the typist
    body="#c98d5e", belly="#ecc9a3", ear="#c98d5e", inner="#e9a98b",
    patch=None, blush="#f39a9a", paw="#b77a4c", arm="#c98d5e",
)
DUDU = dict(  # white bear with dark ears / eye patches - the mouse user
    body="#fbf7f2", belly="#ffffff", ear="#3a3a3a", inner="#5a5a5a",
    patch="#3a3a3a", blush="#f7a8b8", paw="#3a3a3a", arm="#3a3a3a",
)
SIZES = {"Small": 0.7, "Medium": 1.0, "Large": 1.4}
SLEEP_AFTER = 45.0      # seconds without any input -> sleep
FPS = 30


# ----------------------------------------------------------------------------
# Windows helpers (all optional: on other OSes we fall back gracefully)
# ----------------------------------------------------------------------------
if IS_WIN:
    user32 = ctypes.windll.user32

    class _POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

    class _RECT(ctypes.Structure):
        _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                    ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

# Virtual-key codes we watch for "typing". Mouse buttons (1,2,4,5,6) excluded.
_KEY_CODES = [vk for vk in range(0x08, 0xFF) if vk not in (0x01, 0x02, 0x04, 0x05, 0x06)]


def config_path():
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    folder = os.path.join(base, APP_NAME)
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "config.json")


def load_config():
    try:
        with open(config_path(), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(cfg):
    try:
        with open(config_path(), "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass


def work_area(root):
    """Usable screen area (excludes the taskbar)."""
    if IS_WIN:
        r = _RECT()
        if user32.SystemParametersInfoW(48, 0, ctypes.byref(r), 0):  # SPI_GETWORKAREA
            return r.left, r.top, r.right, r.bottom
    return 0, 0, root.winfo_screenwidth(), root.winfo_screenheight()


def virtual_screen(root):
    """Bounding box of all monitors."""
    if IS_WIN:
        x = user32.GetSystemMetrics(76)
        y = user32.GetSystemMetrics(77)
        w = user32.GetSystemMetrics(78)
        h = user32.GetSystemMetrics(79)
        if w and h:
            return x, y, x + w, y + h
    return 0, 0, root.winfo_screenwidth(), root.winfo_screenheight()


# --- "Start with Windows" (per-user Run key, no admin rights needed) ---------
_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _launch_command():
    if getattr(sys, "frozen", False):            # running as the .exe
        return f'"{sys.executable}"'
    exe = sys.executable
    pyw = os.path.join(os.path.dirname(exe), "pythonw.exe")
    if os.path.exists(pyw):
        exe = pyw
    return f'"{exe}" "{os.path.abspath(__file__)}"'


def autostart_enabled():
    if not IS_WIN:
        return False
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY) as k:
            winreg.QueryValueEx(k, APP_NAME)
            return True
    except OSError:
        return False


def set_autostart(enable):
    if not IS_WIN:
        return
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
        if enable:
            winreg.SetValueEx(k, APP_NAME, 0, winreg.REG_SZ, _launch_command())
        else:
            try:
                winreg.DeleteValue(k, APP_NAME)
            except OSError:
                pass


# ----------------------------------------------------------------------------
# Input watcher
# ----------------------------------------------------------------------------
class InputWatcher:
    """Reports new key presses, mouse movement and mouse clicks.

    Only counts presses; never records which key was pressed."""

    def __init__(self, root):
        self.root = root
        self.down = set()
        self.last_pos = self.cursor()
        self.mouse_was_down = False

    def cursor(self):
        if IS_WIN:
            p = _POINT()
            user32.GetCursorPos(ctypes.byref(p))
            return p.x, p.y
        return self.root.winfo_pointerxy()

    def poll(self):
        new_presses = 0
        if IS_WIN:
            gaks = user32.GetAsyncKeyState
            now_down = set()
            for vk in _KEY_CODES:
                st = gaks(vk)
                if st & 0x8000:
                    now_down.add(vk)
                    if vk not in self.down:
                        new_presses += 1
                elif st & 0x0001 and vk not in self.down:
                    new_presses += 1          # very quick tap between polls
            self.down = now_down
            mouse_down = bool(gaks(0x01) & 0x8000 or gaks(0x02) & 0x8000)
        else:
            mouse_down = False

        x, y = self.cursor()
        dx, dy = x - self.last_pos[0], y - self.last_pos[1]
        self.last_pos = (x, y)
        click = mouse_down and not self.mouse_was_down
        self.mouse_was_down = mouse_down
        return new_presses, dx, dy, click, (x, y)


# ----------------------------------------------------------------------------
# Small particle effects (drawn with shapes only - text would leave pink
# fringes around the transparent colour)
# ----------------------------------------------------------------------------
_HEART = []
for i in range(24):
    t = 2 * math.pi * i / 24
    _HEART.append((16 * math.sin(t) ** 3 / 16,
                   -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) / 16))


class Particle:
    def __init__(self, kind, x, y, vx, vy, life, color, size=1.0):
        self.kind, self.x, self.y, self.vx, self.vy = kind, x, y, vx, vy
        self.life = self.max_life = life
        self.color, self.size = color, size

    def step(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
        return self.life > 0


# ----------------------------------------------------------------------------
# The pet window
# ----------------------------------------------------------------------------
class Pet:
    def __init__(self):
        self.cfg = load_config()
        self.scale = float(self.cfg.get("scale", 1.0))
        self.topmost = bool(self.cfg.get("topmost", True))

        self.root = tk.Tk()
        self.root.title("Bubu & Dudu")
        self.root.overrideredirect(True)            # no title bar / no taskbar button
        self.root.attributes("-topmost", self.topmost)
        self.root.config(bg=KEY_COLOR)
        if IS_WIN:
            self.root.attributes("-transparentcolor", KEY_COLOR)

        self.canvas = tk.Canvas(self.root, bg=KEY_COLOR, highlightthickness=0, bd=0)
        self.canvas.pack()
        self.apply_scale(self.scale, keep_corner=False)
        self.place_initial()

        self.watch = InputWatcher(self.root)
        self.particles = []
        self.t0 = time.time()
        self.last_frame = time.time()
        self.last_key = -99.0
        self.last_mouse = -99.0
        self.last_any = time.time()
        self.paw_phase = 0            # which of Bubu's paws hits next
        self.paw_hit = [0.0, 0.0]     # remaining "press" time for each paw
        self.lit_key = None
        self.mouse_off = [0.0, 0.0]   # little mouse offset on the pad
        self.click_t = 0.0
        self.look = (0.0, 0.0)
        self.next_blink = time.time() + random.uniform(2, 5)
        self.blink_until = 0.0
        self.next_love = time.time() + random.uniform(15, 30)
        self.love_until = 0.0
        self.demo = "--demo" in sys.argv

        # dragging + menu
        self.drag = None
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Button-3>", self.show_menu)
        self.build_menu()

        self.root.after(0, self.tick)
        self.root.after(2000, self.keep_on_top)

    # ------------------------------------------------------------- geometry --
    def apply_scale(self, s, keep_corner=True):
        old_w = int(W * self.scale)
        old_h = int(H * self.scale)
        self.scale = s
        w, h = int(W * s), int(H * s)
        self.canvas.config(width=w, height=h)
        if keep_corner:
            # keep the bottom-right corner where it was
            x = self.root.winfo_x() + old_w - w
            y = self.root.winfo_y() + old_h - h
            self.root.geometry(f"{w}x{h}+{x}+{y}")
        else:
            self.root.geometry(f"{w}x{h}")

    def size(self):
        return int(W * self.scale), int(H * self.scale)

    def place_initial(self):
        w, h = self.size()
        vx1, vy1, vx2, vy2 = virtual_screen(self.root)
        x, y = self.cfg.get("x"), self.cfg.get("y")
        if x is None or y is None or not (vx1 - w // 2 <= x <= vx2 - w // 2 and vy1 <= y <= vy2 - h // 2):
            self.snap("bottom-right", save=False)
        else:
            self.root.geometry(f"{w}x{h}+{int(x)}+{int(y)}")

    def snap(self, corner, save=True):
        w, h = self.size()
        l, t, r, b = work_area(self.root)
        m = 4
        x = l + m if "left" in corner else r - w - m
        y = t + m if "top" in corner else b - h - m
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        if save:
            self.root.update_idletasks()
            self.save()

    def save(self):
        self.cfg.update(x=self.root.winfo_x(), y=self.root.winfo_y(),
                        scale=self.scale, topmost=self.topmost)
        save_config(self.cfg)

    # ------------------------------------------------------- mouse handling --
    def on_press(self, e):
        self.drag = (e.x_root - self.root.winfo_x(), e.y_root - self.root.winfo_y())

    def on_drag(self, e):
        if self.drag:
            self.root.geometry(f"+{e.x_root - self.drag[0]}+{e.y_root - self.drag[1]}")

    def on_release(self, _e):
        self.drag = None
        self.save()

    def build_menu(self):
        m = tk.Menu(self.root, tearoff=0)
        size_menu = tk.Menu(m, tearoff=0)
        self.size_var = tk.StringVar(value=next((k for k, v in SIZES.items() if abs(v - self.scale) < 1e-6), "Medium"))
        for name, val in SIZES.items():
            size_menu.add_radiobutton(label=name, variable=self.size_var, value=name,
                                      command=lambda v=val: (self.apply_scale(v), self.save()))
        m.add_cascade(label="Size  (اندازه)", menu=size_menu)

        corner_menu = tk.Menu(m, tearoff=0)
        for c in ("bottom-right", "bottom-left", "top-right", "top-left"):
            corner_menu.add_command(label=c.replace("-", " ").title(), command=lambda c=c: self.snap(c))
        m.add_cascade(label="Move to corner  (گوشه)", menu=corner_menu)

        self.top_var = tk.BooleanVar(value=self.topmost)
        m.add_checkbutton(label="Always on top  (همیشه رو)", variable=self.top_var, command=self.toggle_top)
        if IS_WIN:
            self.auto_var = tk.BooleanVar(value=autostart_enabled())
            m.add_checkbutton(label="Start with Windows  (اجرا با ویندوز)",
                              variable=self.auto_var, command=self.toggle_autostart)
        m.add_separator()
        m.add_command(label="Exit  (خروج)", command=self.quit)
        self.menu = m

    def show_menu(self, e):
        try:
            self.menu.tk_popup(e.x_root, e.y_root)
        finally:
            self.menu.grab_release()

    def toggle_top(self):
        self.topmost = self.top_var.get()
        self.root.attributes("-topmost", self.topmost)
        self.save()

    def toggle_autostart(self):
        try:
            set_autostart(self.auto_var.get())
        except Exception:
            self.auto_var.set(autostart_enabled())

    def keep_on_top(self):
        # Some apps steal the top-most slot; quietly take it back.
        if self.topmost and self.drag is None:
            try:
                self.root.attributes("-topmost", True)
            except tk.TclError:
                return
        self.root.after(2000, self.keep_on_top)

    def quit(self):
        self.save()
        self.root.destroy()

    # ----------------------------------------------------------- main loop --
    def tick(self):
        now = time.time()
        dt = min(0.1, now - self.last_frame)
        self.last_frame = now

        presses, dx, dy, click, (cx, cy) = self.watch.poll()
        if self.demo:
            presses, dx, dy, click = self.fake_input(now)

        if presses:
            self.last_key = now
            for _ in range(min(presses, 2)):
                self.key_hit()
        if abs(dx) + abs(dy) > 1 or click:
            self.last_mouse = now
            self.mouse_off[0] = max(-12, min(12, self.mouse_off[0] + dx * 0.12))
            self.mouse_off[1] = max(-4, min(4, self.mouse_off[1] + dy * 0.06))
            if abs(dx) + abs(dy) > 25 and random.random() < 0.3:
                self.spawn("dash", 272 * 1 + self.mouse_off[0] - math.copysign(14, dx or 1), 160,
                           -math.copysign(30, dx or 1), 0, 0.3, "#9a8f88")
        if click:
            self.click_t = 0.18
            self.spawn("star", 272 + self.mouse_off[0], 145, random.uniform(-15, 15), -45, 0.6, "#ffcc33")
        if presses or abs(dx) + abs(dy) > 1 or click:
            self.last_any = now

        # mouse slowly glides back to centre of the pad
        decay = math.exp(-dt * 3)
        self.mouse_off = [self.mouse_off[0] * decay, self.mouse_off[1] * decay]
        self.paw_hit = [max(0.0, p - dt) for p in self.paw_hit]
        self.click_t = max(0.0, self.click_t - dt)

        # Dudu's eyes follow the real cursor
        wx, wy = self.root.winfo_x(), self.root.winfo_y()
        ex = wx + 235 * self.scale
        ey = wy + 62 * self.scale
        vx, vy = cx - ex, cy - ey
        d = math.hypot(vx, vy) or 1
        target = (vx / d * min(3.2, d / 40), vy / d * min(2.6, d / 40))
        self.look = (self.look[0] + (target[0] - self.look[0]) * 0.3,
                     self.look[1] + (target[1] - self.look[1]) * 0.3)

        sleeping = (now - self.last_any) > SLEEP_AFTER
        if now > self.next_blink:
            self.blink_until = now + 0.14
            self.next_blink = now + random.uniform(2.5, 6)
        if not sleeping and now > self.next_love and now - self.last_any > 3:
            self.love_until = now + 2.2
            self.next_love = now + random.uniform(25, 50)
            self.spawn("heart", 160, 70, 0, -18, 2.0, "#ff5c8a", 1.3)
        if sleeping and random.random() < dt * 0.9:
            self.spawn("z", random.choice((105, 255)), 30, random.uniform(4, 10), -14, 2.5, "#7d8fb3",
                       random.uniform(0.8, 1.2))

        self.particles = [p for p in self.particles if p.step(dt)]
        self.draw(now, sleeping)
        self.root.after(int(1000 / FPS), self.tick)

    def key_hit(self):
        i = self.paw_phase
        self.paw_phase ^= 1
        self.paw_hit[i] = 0.12
        self.lit_key = (random.randrange(3), random.randrange(8))
        if random.random() < 0.35:
            kind = random.choice(("note", "heart", "star"))
            color = {"note": "#6b8cff", "heart": "#ff6b9a", "star": "#ffbf33"}[kind]
            self.spawn(kind, 86 + random.uniform(-40, 40), 132, random.uniform(-12, 12), -55, 0.8, color, 0.8)

    def spawn(self, *a):
        if len(self.particles) < 40:
            self.particles.append(Particle(*a))

    def fake_input(self, now):
        """--demo mode: pretend there is typing and mouse movement."""
        presses = 1 if random.random() < 0.35 else 0
        dx = int(40 * math.sin(now * 2.0))
        dy = int(10 * math.cos(now * 1.3))
        return presses, dx, dy, random.random() < 0.03

    # -------------------------------------------------------------- drawing --
    def draw(self, now, sleeping):
        c = self.canvas
        s = self.scale
        c.delete("all")
        t = now - self.t0
        typing = (now - self.last_key) < 0.6
        mousing = (now - self.last_mouse) < 0.6
        blink = now < self.blink_until
        love = now < self.love_until

        def S(*pts):
            return [v * s for v in pts]

        def oval(x1, y1, x2, y2, fill, outline=OUTLINE, w=2):
            c.create_oval(*S(x1, y1, x2, y2), fill=fill, outline=outline or fill, width=max(1, w * s))

        def line(pts, fill=OUTLINE, w=2, **kw):
            c.create_line(*S(*pts), fill=fill, width=max(1, w * s), capstyle=tk.ROUND,
                          joinstyle=tk.ROUND, **kw)

        def rrect(x1, y1, x2, y2, r, fill, outline=OUTLINE, w=2):
            pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
                   x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
            c.create_polygon(*S(*pts), smooth=True, fill=fill, outline=outline, width=max(1, w * s))

        def arm(x1, y1, x2, y2, color):
            line((x1, y1, x2, y2), fill=OUTLINE, w=17)
            line((x1, y1, x2, y2), fill=color, w=13)

        def bear(cx, bob, pal, look, eyes_closed, happy):
            y = bob
            # ears
            for ex in (cx - 30, cx + 30):
                oval(ex - 13, 30 + y, ex + 13, 56 + y, pal["ear"])
                oval(ex - 6, 37 + y, ex + 6, 49 + y, pal["inner"], outline=None)
            # body
            oval(cx - 38, 96 + y * 0.5, cx + 38, 172, pal["body"])
            oval(cx - 24, 114 + y * 0.5, cx + 24, 168, pal["belly"], outline=None)
            # head
            oval(cx - 43, 30 + y, cx + 43, 102 + y, pal["body"])
            # eye patches (panda-ish)
            if pal["patch"]:
                for ex, tilt in ((cx - 16, -1), (cx + 16, 1)):
                    c.create_polygon(*S(ex - 10 + tilt * 2, 56 + y, ex + 10 + tilt * 2, 54 + y,
                                        ex + 9 - tilt * 2, 74 + y, ex - 9 - tilt * 2, 74 + y),
                                     smooth=True, fill=pal["patch"], outline=pal["patch"])
            pupil = "#1d1714"
            lx, ly = look
            for ex in (cx - 16, cx + 16):
                ey = 64 + y
                if eyes_closed:
                    col = "#ffffff" if pal["patch"] else OUTLINE
                    c.create_arc(*S(ex - 6, ey - 4, ex + 6, ey + 5), start=200, extent=140,
                                 style=tk.ARC, outline=col, width=max(1, 2 * s))
                elif happy:
                    col = "#ffffff" if pal["patch"] else OUTLINE
                    c.create_arc(*S(ex - 6, ey - 2, ex + 6, ey + 8), start=20, extent=140,
                                 style=tk.ARC, outline=col, width=max(1, 2.2 * s))
                else:
                    oval(ex - 5 + lx, ey - 5 + ly, ex + 5 + lx, ey + 5 + ly,
                         pupil if not pal["patch"] else "#ffffff", outline=None)
                    if pal["patch"]:
                        oval(ex - 3.4 + lx * 1.3, ey - 3.4 + ly * 1.3, ex + 3.4 + lx * 1.3, ey + 3.4 + ly * 1.3,
                             pupil, outline=None)
                    oval(ex - 2.5 + lx, ey - 3.5 + ly, ex - 0.3 + lx, ey - 1.3 + ly, "#ffffff", outline=None)
            # blush
            for bx in (cx - 29, cx + 29):
                oval(bx - 7, 76 + y, bx + 7, 83 + y, pal["blush"], outline=None)
            # nose + mouth
            oval(cx - 4, 74 + y, cx + 4, 79 + y, OUTLINE, outline=None)
            c.create_arc(*S(cx - 7, 76 + y, cx, 84 + y), start=200, extent=150, style=tk.ARC,
                         outline=OUTLINE, width=max(1, 1.8 * s))
            c.create_arc(*S(cx, 76 + y, cx + 7, 84 + y), start=190, extent=150, style=tk.ARC,
                         outline=OUTLINE, width=max(1, 1.8 * s))

        # ---------------- Bubu (typing) ----------------
        bx = 86
        if sleeping:
            bob_b = 3 + 2 * math.sin(t * 1.5)
        elif typing:
            bob_b = 2 * math.sin(t * 14)
        else:
            bob_b = 1.2 * math.sin(t * 2)
        bubu_look = (2.5, 0.5) if love else ((0, 2.5) if typing else (0, 1))
        bear(bx, bob_b, BUBU, bubu_look, sleeping or blink, love)

        # keyboard
        rrect(40, 146, 134, 176, 6, "#e9e6f2")
        for r in range(3):
            for k in range(8):
                kx, ky = 46 + k * 11, 150 + r * 8
                lit = self.lit_key == (r, k) and typing
                c.create_rectangle(*S(kx, ky, kx + 8, ky + 5),
                                   fill="#ffd36e" if lit else "#ffffff", outline="#b9b4c9",
                                   width=max(1, s))
        # Bubu's paws
        for i, (sx, px) in enumerate(((bx - 26, bx - 22), (bx + 26, bx + 22))):
            if sleeping:
                py = 156
            elif typing:
                py = 154 if self.paw_hit[i] > 0 else 145 + 2 * math.sin(t * 20 + i * 3)
            else:
                py = 154
            arm(sx, 118 + bob_b * 0.5, px, py, BUBU["arm"])
            oval(px - 10, py - 8, px + 10, py + 8, BUBU["paw"])

        # ---------------- Dudu (mouse) ----------------
        dx = 236
        if sleeping:
            bob_d = 3 + 2 * math.sin(t * 1.5 + 1)
        elif mousing:
            bob_d = 1.5 * math.sin(t * 9)
        else:
            bob_d = 1.2 * math.sin(t * 2 + 1)
        dudu_look = (-2.8, 0.5) if love else self.look
        bear(dx, bob_d, DUDU, dudu_look, sleeping or blink, love)

        # mouse pad + mouse
        rrect(250, 152, 312, 178, 7, "#bfe3d6")
        mx = 281 + self.mouse_off[0]
        my = 164 + self.mouse_off[1]
        squash = 1.5 if self.click_t > 0 else 0
        oval(mx - 11, my - 13 + squash, mx + 11, my + 13, "#f5f5f5")
        line((mx, my - 13 + squash, mx, my - 4), fill="#9a9a9a", w=1.5)
        if self.click_t > 0:
            oval(mx - 9, my - 11 + squash, mx - 1, my - 4, "#ffd36e", outline=None)
        # Dudu's paws: left resting, right on the back of the mouse
        arm(dx - 26, 120 + bob_d * 0.5, dx - 20, 156, DUDU["arm"])
        oval(dx - 30, 148, dx - 10, 164, DUDU["paw"])
        arm(dx + 28, 120 + bob_d * 0.5, mx - 1, my + 3, DUDU["arm"])
        oval(mx - 8, my - 2 + squash, mx + 7, my + 10 + squash, DUDU["paw"])

        # ---------------- particles ----------------
        for p in self.particles:
            k = p.life / p.max_life
            sz = p.size * (0.6 + 0.4 * k)
            if p.kind == "heart":
                pts = []
                for hx, hy in _HEART:
                    pts += [p.x + hx * 9 * sz, p.y + hy * 9 * sz]
                c.create_polygon(*S(*pts), fill=p.color, outline=p.color, smooth=True)
            elif p.kind == "note":
                oval(p.x - 4 * sz, p.y + 3 * sz, p.x + 3 * sz, p.y + 8 * sz, p.color, outline=None)
                line((p.x + 2.5 * sz, p.y + 5 * sz, p.x + 2.5 * sz, p.y - 7 * sz, p.x + 7 * sz, p.y - 4 * sz),
                     fill=p.color, w=1.8)
            elif p.kind == "star":
                pts = []
                for j in range(10):
                    a = -math.pi / 2 + j * math.pi / 5
                    rr = (6 if j % 2 == 0 else 2.6) * sz
                    pts += [p.x + rr * math.cos(a), p.y + rr * math.sin(a)]
                c.create_polygon(*S(*pts), fill=p.color, outline=p.color)
            elif p.kind == "z":
                z = 5 * sz
                line((p.x - z, p.y - z, p.x + z, p.y - z, p.x - z, p.y + z, p.x + z, p.y + z),
                     fill=p.color, w=2)
            elif p.kind == "dash":
                line((p.x - 4, p.y - 4, p.x + 4, p.y - 4), fill=p.color, w=1.5)
                line((p.x - 6, p.y + 2, p.x + 2, p.y + 2), fill=p.color, w=1.5)

    def run(self):
        self.root.mainloop()


def main():
    if IS_WIN:
        # Make sure only one copy runs.
        mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "Local\\BubuDuduDesktopPet")
        if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            return
        globals()["_mutex"] = mutex
    Pet().run()


if __name__ == "__main__":
    main()
