# 🕹️ Code2Flow Arcade

Convert source code into deterministic, interactive visual flowcharts and ASCII diagrams inside a premium **80s Synthwave Retro Arcade Cabinet** interface.

**👾 Play Live:** [https://code-to-flow.vercel.app/](https://code-to-flow.vercel.app/)

---

## 🎮 Arcade Features

* **📊 High-Fidelity Visual Flowcharts:** Powered by **Mermaid.js**, offering fully interactive, cleanly linked loop cycles and decisions instead of rigid linear lists.
* **🎹 80s Synthwave Arcade Interface:** Complete visual overhaul featuring a glowing cyber-grid backdrop, physical 3D depressible machine buttons, flashing status loaders, and retro scanline vignette overlays.
* **👾 Pixel Game Typography:** Loaded with authentic 8-bit Google Fonts:
  * `Press Start 2P` for arcade headers, panel titles, button text, and loading metrics.
  * `VT323` for large, highly legible pixelated monospaced outputs, editor input, and steps logs.
* **⚡ Zero-Quota Caching (SHA-256):** Implements an in-memory hashing cache layer. Identical source code submissions bypass the Gemini API completely, returning matches instantly to conserve API quota.
* **🛡️ Bulletproof Mermaid Parser Protection:** Equipped with a multi-phase, prefix-constrained regex sanitizer. Automatically wraps unquoted shape labels in double-quotes without corrupting nested arrays (`adj[i]`) or function calls (`bfs(...)`).
* **🎛️ Tri-View Dashboard:** Seamless tab layouts to view the **Visual Diagram** (Mermaid SVG), **ASCII Flowchart** (deterministic fallback), and **JSON Steps Sequence** (structured extraction details).
* **💾 Developer Utilities:** Instant actions to copy raw Mermaid markup to your clipboard or download flowcharts as high-resolution vectors (`.svg`).

---

## ⚙️ Architecture & Data Flow

```
[ User Code Input ]
       │
       ▼
[ SHA-256 Hashing ] ──( Cache Hit )──► [ Instant Cache Return ]
       │                                         ▲
  ( Cache Miss )                                 │ (Writes to cache)
       │                                         │
       ▼                                         │
[ Gemini 2.5 Logic ] (JSON response) ────────────┘
       │
       ├─────────────────────────┬─────────────────────────┐
       ▼                         ▼                         ▼
[ Parser Sanitizer ]     [ ASCII Engine ]         [ Steps Normalizer ]
(Prefix-guarded regex) (Deterministic Python)  (Strict validation layer)
       │                         │                         │
       ▼                         ▼                         ▼
[ Mermaid SVG Render ]   [ Linear ASCII Box ]      [ JSON Step Logs ]
```

---

## 💎 Tech Stack

* **Backend:** Python 3.9+, Flask
* **AI Engine:** Google Gemini (`gemini-2.5-flash-lite`)
* **Frontend:** HTML5, Vanilla CSS3 (Custom Grid Matrices & Arcade Button Styles), Javascript, Mermaid.js
* **Deployment:** Vercel Serverless (via `vercel.json` routing configuration)

---

## 🚀 Local Development

### Prerequisites

* Python 3.9+
* A Gemini API key (from [Google AI Studio](https://aistudio.google.com/))

### Setup & Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/Saksham-Gupta-GH/code-to-flow.git
   cd code-to-flow
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   ```bash
   export GEMINI_API_KEY="your_api_key_here"
   
   # Optional: defaults to gemini-2.5-flash-lite
   export GEMINI_MODEL_NAME="gemini-2.5-flash-lite" 
   ```

4. **Launch the Local Development Server:**
   ```bash
   python api/index.py
   ```
   Open your browser and navigate to `http://localhost:5000` to start playing!

---

## 🕹️ Game Controls & Inputs

1. Paste any source code snippet (up to 4000 characters) into the **Source Code** terminal window.
2. Click the **Generate Flowchart** push-button to fire up the logical extraction engine.
3. Switch tabs in the right-hand panel to inspect the visual rendering, raw ASCII diagram, or structural steps list.
4. Click **Copy Mermaid Code** to share with markdown documents, or **Download SVG** to save your diagram forever.
