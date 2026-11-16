# Metricore.in

> **All-in-One AI Platform & Tools Directory**  
> Built with **FastAPI**, **Jinja2**, and **Tailwind CSS**.

Metricore is a high-performance, dynamic directory comparing industry-standard **Paid AI Tools** against their best **Free Alternatives**, complete with **Free Tier Testing Limits** so developers and creators can evaluate tools before purchasing.

---

## 📸 Source Data & Categories

Extracted from `July_19_2026.png`:

| # | Topic / Category | Paid Benchmark | Price | Free Alternative | Free Tier Testing Limit |
| :-: | :--- | :--- | :--- | :--- | :--- |
| **01** | **Image Creation** | Midjourney | $60/mo | Nano Banana | Promotional web trials vs. 100% free web gen |
| **02** | **AI Research** | Perplexity | $20/mo | Consensus | 5 Pro queries / 4 hrs vs. 20 AI credits/mo |
| **03** | **Avatar Creation** | HeyGen | $39/mo | Hedra | 1 free credit (1 min video) vs. daily credits |
| **04** | **Code Generation** | GitHub Copilot | $10/mo | Cursor | 30-day trial vs. 2,000 completions/mo free |
| **05** | **Cinematic Creation** | Runway ML | $76/mo | Stable Diffusion | 125 one-time credits vs. free open-weights |
| **06** | **Thumbnail / Image Editing**| Adobe Firefly | $9.99/mo | Photoroom | 25 monthly credits vs. free background removal |
| **07** | **Video Generation** | Higgsfield | $49/mo | Hailuo | Free mobile trial vs. daily HD credits |
| **08** | **Social Media Scheduling** | Buffer | $15/mo | Publer | 3 channels / 10 posts vs. 3 accounts free |
| **09** | **AI Writing Assistant** | Jasper | $39/mo | QuillBot | 7-day trial vs. 125 words + free grammar check |
| **10** | **Presentation Maker** | Gamma | $10/mo | Canva | 400 signup credits vs. free design templates |
| **11** | **Voice Generation** | ElevenLabs | $22/mo | PlayHT | 10,000 chars/mo vs. 12,500 chars free |
| **12** | **Music Generation** | Suno | $8/mo | Udio | 50 daily credits (10 songs/day) vs. 10 daily + 100 monthly |

---

## ⚡ Tech Stack & Architecture

- **Backend:** FastAPI (Python 3.10+)
- **Templating:** Jinja2 (Dynamic Server-Side Rendering)
- **Frontend Interactivity:** HTMX (Instant, zero-reload search & category filtering)
- **Styling:** Tailwind CSS (Modern dark mode UI)
- **Data Store:** `app/data/tools.json` validated by Pydantic models in `app/models.py`
- **Interactive API Docs:** Automatic Swagger UI at `/docs`

---

## 🚀 Quickstart Guide

### 1. Clone the Repository
```bash
git clone https://github.com/AkbarDev/metricore.in.git
cd metricore.in
```

### 2. Install Dependencies
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Run the Development Server
```bash
python run.py
```
Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.  
Interactive API docs are live at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
