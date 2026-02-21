# Maracaibo Real Estate Scraper & Dashboard

Automated property listing aggregator for Maracaibo, Venezuela with interactive dashboard.

## Quick Start

### Run Dashboard
```bash
cd ~/clawd/skills/maracaibo-realestate
streamlit run dashboard.py
```
Access at: http://localhost:8501

### Remote Access (ngrok)
```bash
~/bin/ngrok http 8501
```

## Features

### Dashboard (`dashboard.py`)
- **Filters:** Property type, sector, price range, bedrooms
- **Preferred zones** highlighted with ⭐
- **Interactive scatter plot** — click points to see details
- **Opportunity Score** (0-100) — identifies best deals
- **Days on market** tracking
- **Search bar** — filter by sector, description, realtor

### Opportunity Score Formula
| Factor | Max Points | Details |
|--------|-----------|---------|
| Price vs trend | 40 | 30% below trend = 40 pts |
| Preferred sector | 20 | Bonus for target zones |
| Days on market | 20 | 10+ days = max (more negotiable) |
| $/m² vs median | 20 | 25% below = 20 pts |

### Data Sources
- **Instagram:** via Apify (hashtags + profiles)
- **Websites:** angelpinton.com, regaladogroup.net, eliterealestateca.com

### Preferred Zones
Tierra Negra, Av. El Milagro, Bancomara, 5 de Julio, Santa Rita, La Lago, Bella Vista, Canta Claro, Av. 72, Zona Norte

## Scripts

| Script | Purpose |
|--------|---------|
| `run-scrape.sh` | Run all scrapers |
| `process-to-db.py` | Process JSON → SQLite |
| `check-listings.py` | Detect sold/price drops |
| `analyze_v2.py` | Generate static charts |
| `db.py` | Database utilities |

## Cron Jobs
- **Morning:** 8:00 AM (EN + ES)
- **Afternoon:** 2:00 PM (EN + ES)
- **Evening:** 8:00 PM (EN + ES)
- **Weekly:** Sunday 9:00 AM — check sold/price drops

## Database

SQLite at `data/maracaibo.db`

Key fields:
- `listing_date` — when first seen
- `original_price` — for price change tracking
- `price_usd` — current price
- `status` — active/sold/new

## Notes

### Venezuelan Number Format
Prices use dots as thousands separators:
- `$$45.000` = $45,000
- `$$1.500.000` = $1,500,000

This is handled in `process-to-db.py` and `check-listings.py`.

## Telegram Groups
- **A&Alfred (EN):** -1003777728309 topic:398
- **Automated Real State (ES):** -1003729911432
