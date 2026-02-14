<div align="center">

# 🎮 Steam Lua Generator

### Generate depot key Lua files instantly from your browser

[![GitHub Stars](https://img.shields.io/github/stars/blizzx4644/Steam-Lua-Generator?style=for-the-badge&color=4f8ff7&logo=github)](https://github.com/blizzx4644/Steam-Lua-Generator/stargazers)
[![GitHub Pages](https://img.shields.io/badge/DEMO-Live-fbbf24?style=for-the-badge&logo=github)](https://blizzx4644.github.io/Steam-Lua-Generator/)

<br>

<img src="https://cdn.akamai.steamstatic.com/store/home/store_home_share.jpg" alt="Banner" width="600" style="border-radius: 12px;">

<br><br>

**A fully client-side web app that generates `.lua` depot key files for Steam apps.**
**No server. No install. Just open and search.**

[🚀 Launch App](#-quick-start) · [✨ Features](#-features) 

</div>


---

## ✨ Features

### 🔍 Smart Search
- Search across **200,000+ Steam apps** by name or AppID
- **Only apps with valid depot keys** appear in results — no dead ends
- Instant results with game thumbnails and depot count badges

### ⬇️ One-Click Generation
- Click **"⬇ Lua"** on any result to instantly download the `.lua` file
- Generated files include `addappid()` calls with all valid depot encryption keys
- No configuration needed

### 📋 Detailed Game View
- Click **"Details"** to open a rich modal with:
  - 🖼️ HD header image from Steam CDN
  - 📝 Game description
  - 👨‍💻 Developer & Publisher
  - 🏷️ Genres & Categories
  - 💰 Price info
  - 🪟🍎🐧 Platform support
  - ⭐ Metacritic score
  - 👥 Review count
  - 🔑 Full depot key list with IDs

### 📅 Three Date Tracking Cards
| Card | Source | What it shows |
|---|---|---|
| 📅 **Release Date** | Steam Store API | When the game was released |
| 🔄 **Last Update** | Steam News API | Most recent game update/patch + title |
| 🔑 **Keys Updated** | GitHub API | When the depot keys database was last updated |

### 🌗 Dark / Light Theme
- Toggle between dark and light themes
- Preference saved in `localStorage`
- Smooth CSS transitions on all elements


### 🔑 Smart Depot Mapping
- Uses **binary search** (`bisect`) to map 178k+ depot keys to their parent apps
- O(log n) per key — entire mapping built in milliseconds
- Only apps with at least one valid key are searchable

---

## 🚀 Quick Start

### Option 1: GitHub Pages (Recommended)
> Just visit the live demo — nothing to install:

**➡️ [https://blizzx4644.github.io/Steam-Lua-Generator/](https://blizzx4644.github.io/Steam-Lua-Generator/)**

### Option 2: Run Locally
```bash
# Clone the repository
git clone https://github.com/blizzx4644/Steam-Lua-Generator.git
cd Steam-Lua-Generator

# Serve with any HTTP server (required for PyScript)
python -m http.server 8000
# or
npx serve .

