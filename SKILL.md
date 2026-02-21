---
name: maracaibo-realestate
description: Scrape Maracaibo, Venezuela real estate listings from websites, Instagram and Facebook. Filters by criteria and sends results via Telegram.
---

# Maracaibo Real Estate Scraper

Scrapes property listings from websites, Instagram profiles/hashtags, and Facebook groups for Maracaibo, Venezuela.

## Sources

### Websites (Direct Scraping)
Scraped daily at 8am:
- **regaladogroup.net/inmuebles/** - Regalado Group
- **angelpinton.com/inmobiliaria/maracaibo-v/inmuebles/** - Ángel Pinton
- **nexthouseinmobiliaria.com/inmobiliaria/inmuebles** - Next House
- **zuhausebienesraices.com/propiedades/** - Zuhause Bienes Raices
- **eliterealestateca.com** - Elite Real Estate

### Instagram Profiles (Inmobiliarias)
Scraped 3x daily (8am, 2pm, 8pm):
- @necya.eliterealestate
- @regaladogroup
- @angelpintoninmobiliaria
- @nexthouseinmobiliaria (también @inmobiliarianexthouse)
- @zuhausebienesraices

### Instagram Hashtags
- #inmueblesmaracaibo
- #casasenmaracaibo
- #apartamentosmaracaibo
- #ventacasamaracaibo
- #bienesraicesmaracaibo
- #ventamaracaibo

### Facebook (optional)
- TBD - Provide group URLs to add

## Telegram Delivery
- **English group:** -1003777728309 (topic 398)
- **Spanish group:** -1003729911432 (mensajes pineados)

## Usage

```bash
# Full scrape (Instagram + websites at 8am)
./scripts/run-scrape.sh

# Scrape only websites
python3 ./scripts/scrape-websites.py --site all

# Scrape specific website
python3 ./scripts/scrape-websites.py --site regaladogroup

# Scrape Instagram profile
./scripts/scrape-ig-profile.sh "profile_name" 10

# Scrape Instagram hashtag
./scripts/scrape-ig.sh "#hashtag" 10

# Process results to database
python3 ./scripts/process-to-db.py
```

## Database
SQLite at `data/listings.db`:
- `listings` - All scraped properties with extracted metadata
- `sent_to_groups` - Track which listings sent to which groups

## Adding New Sources
1. **Instagram profiles:** Add to PROFILES array in `run-scrape.sh`
2. **Websites:** Add config to WEBSITES dict in `scrape-websites.py`
3. **Hashtags:** Add to HASHTAGS array in `run-scrape.sh`

## Cron Schedule
Configured via Clawdbot cron jobs (see cron list for active jobs).
