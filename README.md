# Code2Flow

Convert source code into deterministic, text-based ASCII flowcharts.

**Live app:** https://code2flow-x46y.onrender.com

---

## Overview

Code2Flow takes a code snippet, sends it to Gemini only to extract **control-flow steps**, then renders a clean ASCII flowchart **deterministically in Python**.

- Gemini is **never** used to draw ASCII.
- ASCII rendering is pure code, stable across runs.
- Supports loops, decisions, yes/no branches, and linear processes.
- Simple web UI built with Flask, HTML, CSS and vanilla JS.

---

## How it works

1. **AI stage (logic only)**  
   The backend calls Gemini with a fixed prompt that asks it to output control-flow steps using only these keywords:

   - `START`
   - `PROCESS:`
   - `LOOP:`
   - `DECISION:`
   - `YES ->`
   - `NO ->`
   - `END`

   The model must not include ASCII art or flowcharts—just labeled steps.

2. **Normalization**  
   The raw Gemini output is post-processed with a regex-based parser:

   - Splits on the control-flow keywords.
   - Normalizes into an ordered list of steps:  
     `{"type": "PROCESS" | "LOOP" | "DECISION" | "YES" | "NO" | "START" | "END", "text": "..."}`

3. **Rendering (no AI)**  
   A pure Python renderer turns the normalized steps into a vertical ASCII flowchart, using:

   - `( START )` / `( END )`
   - `[ process ]`
   - `< condition ? >`
   - `|-- Yes -->`
   - `|-- No  -->`
   - `|-- loop back to < condition ? >` (for loops where applicable)

   Rendering has **no randomness** and does not call Gemini.

---

## Tech stack

- **Backend:** Python, Flask, Gunicorn
- **AI client:** `google-generativeai` (Gemini)
- **Frontend:** Jinja2 templates, HTML, CSS, vanilla JavaScript
- **Deployment:** Render (`render.yaml` based)

---

## Local development

### Prerequisites

- Python 3.10+ (recommended)
- `pip` / `pip3`
- A Gemini API key

### Setup

```bash
git clone https://github.com/<your-username>/code2flow.git
cd code2flow

pip3 install -r requirements.txt

export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
# optional, default is gemini-1.5-pro
export GEMINI_MODEL_NAME="gemini-1.5-pro"

python3 app.py
