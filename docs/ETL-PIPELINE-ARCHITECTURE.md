# 🏗️ ETL Pipeline Architecture

**Mi Casa Venezuela - Real Estate Data Pipeline**

**Versión:** 2.0  
**Última actualización:** 2026-02-27  
**Maintainers:** @augustov58, @rockoloco

---

## 📋 Resumen Ejecutivo

Pipeline ETL (Extract, Transform, Load) que agrega listados inmobiliarios de múltiples fuentes en Maracaibo, Venezuela. El sistema normaliza datos heterogéneos en un esquema unificado para alimentar la plataforma [micasavenezuela.com](https://micasavenezuela.com).

**Métricas actuales:**
- 🏠 ~130 listings activos
- 📡 5 fuentes web + Instagram
- ⏰ 3 ejecuciones/día
- 🔄 Auto-limpieza de listings >60 días

---

## 🏛️ Arquitectura General

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ETL PIPELINE - MI CASA VENEZUELA                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        1. EXTRACT (Fuentes)                         │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │  INSTAGRAM   │  │   WEBSITES   │  │   FACEBOOK   │              │   │
│  │  │              │  │              │  │   (futuro)   │              │   │
│  │  │ Apify Actor  │  │ BeautifulSoup│  │              │              │   │
│  │  │ Profile      │  │ + Requests   │  │              │              │   │
│  │  │ Scraper      │  │              │  │              │              │   │
│  │  │              │  │              │  │              │              │   │
│  │  │ • Profiles   │  │ • Regalado   │  │ • Groups     │              │   │
│  │  │ • Carousels  │  │ • AngelPinton│  │ • Marketplace│              │   │
│  │  │ • Comments   │  │ • NextHouse  │  │              │              │   │
│  │  │              │  │ • Zuhause    │  │              │              │   │
│  │  │              │  │ • Elite RE   │  │              │              │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │   │
│  │         │                 │                 │                       │   │
│  └─────────┼─────────────────┼─────────────────┼───────────────────────┘   │
│            │                 │                 │                           │
│            ▼                 ▼                 ▼                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      RAW DATA (JSON Files)                          │   │
│  │  ./data/ig-*.json    ./data/websites-*.json    ./data/fb-*.json    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│            │                 │                 │                           │
│            └─────────────────┼─────────────────┘                           │
│                              ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      2. TRANSFORM (Procesamiento)                   │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                     │   │
│  │  process-to-db.py / sync-listings.py                               │   │
│  │  ─────────────────────────────────────────                         │   │
│  │                                                                     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │   │
│  │  │ Normalize   │  │  Parse      │  │ Deduplicate │  │ Validate  │ │   │
│  │  │ Schema      │  │  Fields     │  │ by URL/ID   │  │ Data      │ │   │
│  │  │             │  │             │  │             │  │           │ │   │
│  │  │ • source    │  │ • price     │  │ • source_id │  │ • price   │ │   │
│  │  │ • source_id │  │ • bedrooms  │  │ • url hash  │  │   > $1000 │ │   │
│  │  │ • url       │  │ • sqm       │  │ • content   │  │ • sqm     │ │   │
│  │  │ • images[]  │  │ • location  │  │   hash      │  │   < 5000  │ │   │
│  │  │ • text      │  │ • type      │  │             │  │           │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘ │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                             │
│                              ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        3. LOAD (Destinos)                           │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                     │   │
│  │  ┌──────────────────────┐         ┌──────────────────────┐         │   │
│  │  │     SUPABASE         │         │      SQLite          │         │   │
│  │  │   (Producción)       │         │   (Local/Backup)     │         │   │
│  │  │                      │         │                      │         │   │
│  │  │  mcv_listings        │         │  listings.db         │         │   │
│  │  │  mcv_events          │         │                      │         │   │
│  │  │  mcv_leads           │         │  • sent_to_groups    │         │   │
│  │  │                      │         │  • price_history     │         │   │
│  │  └──────────┬───────────┘         └──────────────────────┘         │   │
│  │             │                                                       │   │
│  └─────────────┼───────────────────────────────────────────────────────┘   │
│                │                                                           │
│                ▼                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      4. SERVE (Consumidores)                        │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │   WEB APP    │  │  TELEGRAM    │  │   FUTURE     │              │   │
│  │  │              │  │   ALERTS     │  │              │              │   │
│  │  │ micasavene-  │  │              │  │ • API        │              │   │
│  │  │ zuela.com    │  │ • EN Group   │  │ • Mobile App │              │   │
│  │  │              │  │ • ES Group   │  │ • Webhooks   │              │   │
│  │  │ Next.js      │  │              │  │              │              │   │
│  │  │ Vercel       │  │ Clawdbot     │  │              │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Componentes del Sistema

### 1. Extractors (Scrapers)

| Componente | Archivo | Tecnología | Frecuencia |
|------------|---------|------------|------------|
| Instagram Scraper | `scrape-ig-profile.sh` | Apify API | 3x/día |
| Website Scraper | `scrape-websites.py` | BeautifulSoup | 3x/día |
| Facebook Scraper | `scrape-fb.sh` | Apify API | Deshabilitado |

#### Instagram Scraper
```bash
# Usa Apify Instagram Profile Scraper
# Devuelve: posts con carruseles completos (campo 'images')
./scripts/scrape-ig-profile.sh "username" [maxPosts]

# Output: ./data/ig-{username}-{timestamp}.json
```

**Campos extraídos:**
- `displayUrl` - Imagen principal
- `images[]` - Todas las imágenes del carrusel ✅ (fix 2026-02-27)
- `caption` - Texto del post
- `ownerUsername` - Autor
- `likesCount` - Engagement
- `timestamp` - Fecha publicación

#### Website Scraper
```bash
# Scraping directo con requests + BeautifulSoup
python scripts/scrape-websites.py --site all --fetch-details

# Output: ./data/websites-{timestamp}.json
```

**Sitios soportados:**

| Sitio | Parser | Detail Fetch | Estado |
|-------|--------|--------------|--------|
| regaladogroup.net | `parse_regaladogroup` | ✅ | Activo |
| angelpinton.com | `parse_angelpinton` | ✅ | Activo |
| nexthouseinmobiliaria.com | `parse_nexthouse` | ✅ | Activo |
| zuhausebienesraices.com | `parse_zuhause` | ✅ | Activo |
| eliterealestateca.com | `parse_eliterealestate` | ✅ | Activo |

### 2. Transformers

| Componente | Archivo | Función |
|------------|---------|---------|
| Local Processor | `process-to-db.py` | JSON → SQLite (alertas Telegram) |
| Supabase Sync | `sync-listings.py` | JSON → PostgreSQL (web app) |

#### Normalización de Schema

```python
# Schema unificado para todos los listings
{
    'source': str,        # 'instagram', 'regaladogroup', etc.
    'source_id': str,     # ID único en la fuente
    'url': str,           # URL original del listing
    'text': str,          # Descripción (max 2000 chars)
    'author': str,        # Vendedor/Realtor
    'images': list[str],  # URLs de imágenes
    'price_usd': float,   # Precio en USD
    'bedrooms': int,      # Habitaciones
    'bathrooms': int,     # Baños
    'sqm': float,         # Metros cuadrados
    'property_type': str, # 'casa', 'apartamento', 'terreno', etc.
    'location': str,      # Sector/Zona
    'listing_date': str,  # Fecha de publicación
    'status': str,        # 'new', 'sent', 'sold'
}
```

#### Parsing de Campos

```python
# Precio (múltiples formatos)
"$130,000" → 130000
"130.000 $" → 130000
"$$45.000" → 45000

# Metros cuadrados (formato latino)
"811,91 mts2" → 811.91  # ✅ Fix 2026-02-27
"350 m²" → 350

# Habitaciones
"Habitaciones: 3" → 3
"3 Hab" → 3
```

### 3. Loaders

#### Supabase (Producción)
```python
# sync-listings.py
- Deduplicación por (source, source_id)
- Deduplicación por URL
- Auto-delete listings >60 días
- Upsert para re-listings
```

#### SQLite (Local)
```python
# process-to-db.py → listings.db
- Tracking de envíos a grupos Telegram
- Historial de precios
- Backup local
```

---

## ⏰ Scheduling

### GitHub Actions (micasavenezuela)

```yaml
# .github/workflows/sync-listings.yml
schedule:
  - cron: '0 13 * * *'  # 8am EST
  - cron: '0 19 * * *'  # 2pm EST
  - cron: '0 1 * * *'   # 8pm EST
```

### Clawdbot Cron (Telegram Alerts)

| Job | Horario | Target |
|-----|---------|--------|
| Scrape + Alert EN | 8:00, 14:00, 20:00 EST | Telegram EN |
| Alert ES | 8:05, 14:05, 20:05 EST | Telegram ES |
| Check Sold/Price Drops | Domingos 9:00 EST | Telegram EN |

---

## 🔧 Configuración

### Variables de Entorno

```bash
# Apify (Instagram/Facebook scraping)
APIFY_API_KEY=apify_api_xxx

# Supabase (Base de datos producción)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJxxx  # Service role, NO anon key

# GitHub Secrets necesarios en micasavenezuela repo:
# - SUPABASE_URL
# - SUPABASE_SERVICE_KEY
# - APIFY_TOKEN (opcional, para Instagram)
```

### Agregar Nueva Fuente Web

1. **Agregar configuración en `WEBSITES`:**
```python
# scrape-websites.py
WEBSITES = {
    'nuevositio': {
        'name': 'Nuevo Sitio',
        'listing_url': 'https://nuevositio.com/propiedades',
        'base_url': 'https://nuevositio.com',
        'parser': 'parse_nuevositio',
    },
}
```

2. **Crear función parser:**
```python
def parse_nuevositio(html):
    soup = BeautifulSoup(html, 'lxml')
    listings = []
    
    for card in soup.find_all('div', class_='property-card'):
        # Extraer datos...
        listing = {
            'url': url,
            'source': 'nuevositio',
            'text': text,
            'price': price,
            'images': images,
            # ...
        }
        listings.append(listing)
    
    return listings
```

3. **Agregar detail fetcher (opcional):**
```python
def fetch_detail_images(url, source):
    # ...
    elif source == 'nuevositio':
        for img in soup.find_all('img', class_='gallery-image'):
            # ...
```

4. **Registrar parser:**
```python
PARSERS = {
    # ...
    'parse_nuevositio': parse_nuevositio,
}
```

---

## 🐛 Problemas Resueltos

### 1. Formato de Números Latino (2026-02-27)
**Problema:** "811,91" se parseaba como 81191 en vez de 811.91  
**Causa:** La coma se interpretaba como separador de miles  
**Solución:** Detectar si la coma tiene ≤2 dígitos después (decimal) vs 3 (miles)

```python
# Antes
"811,91" → 81191 ❌

# Después  
"811,91" → 811.91 ✅
"1.200" → 1200 ✅ (punto como miles)
```

### 2. Instagram Solo Mostraba 1 Imagen (2026-02-27)
**Problema:** Carruseles de Instagram solo mostraban la primera imagen  
**Causa:** Usábamos `displayUrl` en vez del array `images`  
**Solución:** Usar campo `images` que ya viene de Apify

```python
# Antes
'images': [post.get('displayUrl')]  # Solo 1 imagen

# Después
'images': post.get('images') or [post.get('displayUrl')]  # Carrusel completo
```

### 3. Websites con Pocas Imágenes (2026-02-27)
**Problema:** Solo se extraía el thumbnail del listado, no la galería completa  
**Causa:** Solo scrapeábamos la página de listado, no la de detalle  
**Solución:** Agregar `--fetch-details` para visitar páginas de detalle

```python
# Nuevo flujo
1. Scrape listado → obtener URLs
2. Para cada listing con <3 imágenes:
   - Visitar página de detalle
   - Extraer galería completa
```

### 4. URLs de Instagram Expiran
**Problema:** Las URLs de cdninstagram.com tienen tokens temporales  
**Estado:** Documentado, no resuelto  
**Solución futura:** Opción C - Almacenar imágenes en Supabase Storage  
**Documento:** `docs/ARCHITECTURE-IMAGE-STORAGE.md`

### 5. GitHub Action Fallaba (2026-02-27)
**Problema:** Sync to Supabase fallaba con "SUPABASE_URL required"  
**Causa:** Secrets no configurados en el repo  
**Solución:** Agregar secrets en GitHub repo settings

---

## 📊 Métricas y Monitoreo

### Métricas Actuales

```sql
-- Total listings por fuente
SELECT source, COUNT(*) as total
FROM mcv_listings
GROUP BY source;

-- Listings con imágenes
SELECT 
  source,
  COUNT(*) as total,
  COUNT(*) FILTER (WHERE array_length(images, 1) > 0) as with_images,
  AVG(array_length(images, 1)) as avg_images
FROM mcv_listings
GROUP BY source;
```

### Alertas Recomendadas

- [ ] GitHub Action falla 2+ veces seguidas
- [ ] <10 listings nuevos en 24h
- [ ] >50% listings sin imágenes
- [ ] Supabase storage >80%

---

## 🚀 Mejoras Futuras

### Corto Plazo
- [ ] Agregar más perfiles de Instagram
- [ ] Implementar scraping de comentarios (precio/vendido)
- [ ] Mejorar detección de duplicados cross-source

### Mediano Plazo
- [ ] Facebook Marketplace scraping
- [ ] Almacenamiento de imágenes (Opción C)
- [ ] Geocoding de direcciones
- [ ] Detección automática de propiedades vendidas

### Largo Plazo
- [ ] ML para categorización automática
- [ ] Estimación de precios por zona
- [ ] API pública para terceros
- [ ] Real-time streaming (webhooks)

---

## 📁 Estructura de Archivos

```
maracaibo-realestate/
├── scripts/
│   ├── scrape-websites.py      # Web scraper principal
│   ├── scrape-ig-profile.sh    # Instagram via Apify
│   ├── scrape-fb.sh            # Facebook (deshabilitado)
│   ├── process-to-db.py        # Transform → SQLite
│   ├── run-scrape.sh           # Orchestrator script
│   ├── check-listings.py       # Detectar vendidos/price drops
│   └── db.py                   # SQLite utilities
├── data/
│   ├── listings.db             # SQLite local
│   ├── ig-*.json               # Raw Instagram data
│   ├── websites-*.json         # Raw website data
│   └── fb-*.json               # Raw Facebook data
├── docs/
│   ├── ETL-PIPELINE-ARCHITECTURE.md  # Este documento
│   └── ARCHITECTURE-IMAGE-STORAGE.md # Opción C futuro
└── dashboard.py                # Streamlit dashboard (legacy)

micasavenezuela/
├── .github/workflows/
│   └── sync-listings.yml       # GitHub Action (3x/día)
├── scripts/
│   └── sync-listings.py        # Transform → Supabase
├── supabase/
│   └── migrations/             # Schema SQL
└── src/                        # Next.js app
```

---

## 🔐 Seguridad

- **Nunca** commitear API keys o secrets
- Usar GitHub Secrets para CI/CD
- Service role key solo en backend, nunca en frontend
- Rate limiting en scrapers (1-3s entre requests)
- Respetar robots.txt cuando aplique

---

## 📞 Troubleshooting

### GitHub Action falla
1. Verificar secrets configurados
2. Revisar logs: `gh run view <id> --log-failed`
3. Test manual: `python scripts/sync-listings.py`

### Scraper no encuentra listings
1. Verificar si el sitio cambió su HTML
2. Probar en browser si la página carga
3. Revisar selectores CSS en el parser

### Imágenes no cargan en web
1. Verificar si la URL es de Instagram (403)
2. Probar URL directamente en browser
3. Considerar implementar Opción C

---

*Documentación mantenida por el equipo de Mi Casa Venezuela*
