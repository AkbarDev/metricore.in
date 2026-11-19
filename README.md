# Metricore.in

> **Open-Source, Non-Commercial AI Tools Reference Directory**  
> Built with **FastAPI**, **Jinja2**, and **Tailwind CSS**.

Metricore is an open-source, non-commercial reference directory that catalogs and compares **Paid AI Tools** alongside **Free Alternatives**, documenting publicly accessible free-tier limits so developers, researchers, and creators can explore software options.

---

## ⚖️ Non-Commercial & Trademark Notice

- **Reference Only:** Metricore is an independent, non-commercial community project for general informational and reference purposes only.
- **No Affiliation or Endorsement:** Metricore is not affiliated with, sponsored by, authorized by, or endorsed by any tool, vendor, or company listed.
- **Trademarks:** All product names, logos, service marks, and registered trademarks belong to their respective owners. Their display here is for factual identification and reference only.
- **Pricing & Limits Volatility:** Software pricing, subscription tiers, free limits, and terms change frequently. Information on this site may be incomplete or outdated; always verify current details on each vendor's official website.
- **No Professional Advice:** Listings and editorial descriptions do not constitute legal, cybersecurity, financial, compliance, or architecture advice.

---

## 📋 Representative Reference Categories

Initial reference matchups between paid tools and free alternatives:

| # | Category | Paid Reference Tool | Price | Free Alternative | Documented Free-Tier Limit |
| :-: | :--- | :--- | :--- | :--- | :--- |
| **01** | **Image Creation** | Midjourney | $60/mo | Nano Banana | Promotional web trials vs. free web generation |
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

## ✏️ Corrections & Removals

We are committed to factual accuracy and prompt updates:
- **Report an Inaccuracy:** If you notice outdated pricing, incorrect free tier limits, or broken links, please open an issue on our [GitHub Issues Tracker](https://github.com/AkbarDev/metricore.in/issues).
- **Request a Removal:** If you are a tool owner or authorized representative and wish for an entry to be removed, submit an issue or contact us; requests are processed promptly.

---

## 🤝 How to Contribute

Contributions from developers and creators are welcome:
1. Fork the repository.
2. Submit additions, documentation corrections, or UI refinements.
3. Ensure all descriptions remain neutral, factual, and free of marketing superlatives.
4. Submit a Pull Request.

---

## ⚡ Tech Stack & Architecture

- **Backend:** FastAPI (Python 3.10+)
- **Templating:** Jinja2 (Dynamic Server-Side Rendering)
- **Frontend Interactivity:** HTMX (Instant, zero-reload search & category filtering)
- **Styling:** Tailwind CSS (Self-hosted static build)
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
Interactive API docs are available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
