# PRD: Maracaibo Real Estate Intelligence Platform

**Versión:** 1.0  
**Fecha:** 2025-02-25  
**Branch:** `feature/lead-capture-platform`  
**Propuesta original:** @rockoloco  
**Status:** 🟡 Pendiente aprobación

---

## 📋 Resumen Ejecutivo

Transformar el scraper actual de propiedades en Maracaibo en una **plataforma de inteligencia inmobiliaria** que:

1. **Captura leads** de compradores potenciales a través de una web pública
2. **Agrega inteligencia** del mercado inmobiliario marabino
3. **Ofrece servicios B2B** a realtors locales una vez construida la base de datos

**Objetivo final:** Crear el mejor agregador de inteligencia real estate en Maracaibo, sirviendo tanto a compradores finales como a casas de realtors.

---

## 🎯 Objetivos

### Corto Plazo (MVP - 4 semanas)
- [ ] Web pública con búsqueda y filtros amigables
- [ ] Sistema de captura de leads (email, WhatsApp)
- [ ] Métricas básicas de tráfico y conversión

### Mediano Plazo (8 semanas)
- [ ] Expandir fuentes de datos (más realtors)
- [ ] Dashboard de métricas avanzado
- [ ] Sistema de alertas personalizadas para usuarios

### Largo Plazo (12+ semanas)
- [ ] Portal B2B para realtors
- [ ] API de inteligencia de mercado
- [ ] Servicios de marketing y leads para realtors

---

## 🏗️ Arquitectura Actual

```
┌─────────────────────────────────────────────────────────────┐
│                    SISTEMA ACTUAL                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Instagram   │    │   Websites   │    │   Facebook   │  │
│  │  (Apify)     │    │  (Scraping)  │    │   (Apify)    │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                   │                   │          │
│         └───────────────────┴───────────────────┘          │
│                             │                              │
│                    ┌────────▼────────┐                     │
│                    │   process-to-   │                     │
│                    │     db.py       │                     │
│                    └────────┬────────┘                     │
│                             │                              │
│                    ┌────────▼────────┐                     │
│                    │   SQLite DB     │                     │
│                    │  listings.db    │                     │
│                    └────────┬────────┘                     │
│                             │                              │
│              ┌──────────────┼──────────────┐               │
│              │              │              │               │
│     ┌────────▼────────┐ ┌───▼────┐ ┌──────▼──────┐        │
│     │   Streamlit     │ │Telegram│ │   Cron      │        │
│     │   Dashboard     │ │ Alerts │ │   Jobs      │        │
│     │  (localhost)    │ │        │ │             │        │
│     └─────────────────┘ └────────┘ └─────────────┘        │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Datos actuales:
- ~500 listings en DB
- 5 websites monitoreados
- 6 perfiles Instagram
- 6 hashtags Instagram
- Dashboard Streamlit local
```

---

## 🚀 Arquitectura Propuesta

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       PLATAFORMA NUEVA                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    FUENTES DE DATOS (Expandidas)                │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────────┐    │   │
│  │  │  IG    │ │  Web   │ │  FB    │ │ Nuevos │ │ Realtors   │    │   │
│  │  │Profiles│ │Scraping│ │ Groups │ │Realtors│ │ Direct API │    │   │
│  │  └────────┘ └────────┘ └────────┘ └────────┘ └────────────┘    │   │
│  └─────────────────────────────┬───────────────────────────────────┘   │
│                                │                                        │
│                       ┌────────▼────────┐                              │
│                       │   PostgreSQL    │                              │
│                       │   + Supabase    │                              │
│                       └────────┬────────┘                              │
│                                │                                        │
│    ┌───────────────────────────┼───────────────────────────┐           │
│    │                           │                           │           │
│    │  ┌────────────────────────▼────────────────────────┐  │           │
│    │  │              WEB PÚBLICA                        │  │           │
│    │  │  ┌─────────────────────────────────────────┐   │  │           │
│    │  │  │  Next.js / Astro Frontend               │   │  │           │
│    │  │  │  - Búsqueda con filtros avanzados       │   │  │           │
│    │  │  │  - Mapa interactivo                     │   │  │           │
│    │  │  │  - Comparador de propiedades            │   │  │           │
│    │  │  │  - Alertas personalizadas               │   │  │           │
│    │  │  └─────────────────────────────────────────┘   │  │           │
│    │  │                        │                        │  │           │
│    │  │  ┌─────────────────────▼─────────────────────┐ │  │           │
│    │  │  │         CAPTURA DE LEADS                  │ │  │           │
│    │  │  │  - Registro con email/WhatsApp           │ │  │           │
│    │  │  │  - "Guardar búsqueda" requiere login     │ │  │           │
│    │  │  │  - "Contactar vendedor" → captura        │ │  │           │
│    │  │  │  - Newsletter semanal                    │ │  │           │
│    │  │  └─────────────────────┬─────────────────────┘ │  │           │
│    │  └────────────────────────┼────────────────────────┘  │           │
│    │                           │                           │           │
│    │  ┌────────────────────────▼────────────────────────┐  │           │
│    │  │              ANALYTICS                          │  │           │
│    │  │  - Plausible/PostHog (privacy-first)           │  │           │
│    │  │  - Funnels de conversión                       │  │           │
│    │  │  - Heatmaps                                    │  │           │
│    │  │  - Tracking de búsquedas populares             │  │           │
│    │  └────────────────────────┬────────────────────────┘  │           │
│    │                           │                           │           │
│    └───────────────────────────┼───────────────────────────┘           │
│                                │                                        │
│    ┌───────────────────────────▼───────────────────────────┐           │
│    │              PORTAL B2B (Fase 2)                      │           │
│    │  - Dashboard para realtors                            │           │
│    │  - Acceso a base de leads (pagado)                    │           │
│    │  - Listados preferenciales                            │           │
│    │  - Inteligencia de mercado                            │           │
│    └───────────────────────────────────────────────────────┘           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📝 Especificaciones Detalladas

### Fase 1: Web Pública con Captura de Leads (MVP)

#### 1.1 Frontend Web

**Stack recomendado:**
- **Framework:** Next.js 14 (App Router) o Astro
- **UI:** Tailwind CSS + shadcn/ui
- **Maps:** Mapbox o Leaflet (OSM)
- **Hosting:** Vercel (gratis para proyectos pequeños)

**Páginas:**

| Página | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| Home | `/` | Búsqueda principal, listados destacados | No |
| Búsqueda | `/buscar` | Filtros avanzados, resultados | No |
| Detalle | `/propiedad/[id]` | Info completa, galería, mapa | No |
| Favoritos | `/favoritos` | Propiedades guardadas | Sí |
| Alertas | `/alertas` | Configurar notificaciones | Sí |
| Perfil | `/perfil` | Datos del usuario | Sí |

**Filtros de búsqueda:**
- Tipo de propiedad (casa, apartamento, townhouse, terreno)
- Rango de precio (USD)
- Habitaciones (min/max)
- Baños (min/max)
- Metros cuadrados (min/max)
- Sector/Zona (dropdown + mapa)
- Fuente (realtor específico)
- Ordenar por: precio, fecha, $/m², oportunidad

**Features UX:**
- [ ] Búsqueda con autocompletado de sectores
- [ ] Vista mapa + lista (toggle)
- [ ] Comparador de hasta 3 propiedades
- [ ] Galería de imágenes con zoom
- [ ] Calculadora de hipoteca básica
- [ ] Compartir propiedad (WhatsApp, link)

#### 1.2 Sistema de Leads

**Puntos de captura (no intrusivos):**

| Trigger | Captura | Valor para usuario |
|---------|---------|-------------------|
| Guardar propiedad | Email/WhatsApp | Acceso a favoritos |
| Crear alerta | Email/WhatsApp + criterios | Notificaciones de nuevos listings |
| Contactar vendedor | Email/WhatsApp + mensaje | Conexión directa |
| Newsletter | Email | Resumen semanal personalizado |
| Ver teléfono vendedor | Email/WhatsApp | Desbloquear info |

**Modelo de datos - Leads:**

```sql
CREATE TABLE leads (
    id UUID PRIMARY KEY,
    email VARCHAR(255),
    whatsapp VARCHAR(20),
    name VARCHAR(100),
    source VARCHAR(50),  -- 'alert', 'favorite', 'contact', 'newsletter'
    preferences JSONB,   -- criterios de búsqueda
    created_at TIMESTAMP,
    last_active TIMESTAMP,
    status VARCHAR(20)   -- 'new', 'engaged', 'contacted', 'converted'
);

CREATE TABLE lead_interactions (
    id UUID PRIMARY KEY,
    lead_id UUID REFERENCES leads(id),
    listing_id INTEGER,
    action VARCHAR(50),  -- 'view', 'favorite', 'contact', 'share'
    metadata JSONB,
    created_at TIMESTAMP
);
```

#### 1.3 Analytics y Métricas

**KPIs a trackear:**

| Métrica | Descripción | Meta |
|---------|-------------|------|
| Visitantes únicos | Usuarios que entran | 1000/mes |
| Tasa de registro | Visitors → Leads | 5% |
| Leads calificados | Con preferencias claras | 50/mes |
| Contactos a realtors | Clicks en contactar | 100/mes |
| Conversiones | Leads que reportan compra | Trackear |

**Herramientas:**
- **Plausible** (analytics privacy-first, ~$9/mes)
- **PostHog** (product analytics, free tier)
- Custom event tracking para funnels

**Eventos a trackear:**
```javascript
// Ejemplos
track('search', { filters: {...}, results_count: 15 });
track('listing_view', { listing_id: 123, source: 'search' });
track('lead_capture', { source: 'alert', method: 'whatsapp' });
track('contact_realtor', { listing_id: 123, realtor: 'regalado' });
```

### Fase 2: Expansión de Fuentes

#### 2.1 Nuevos Realtors a Investigar

**Metodología de búsqueda:**
1. Buscar en Instagram: `#inmobiliariamaracaibo`, `#realtormaracaibo`
2. Google Maps: "inmobiliaria maracaibo"
3. Facebook Groups de bienes raíces Maracaibo
4. Referencias de listings actuales (campo `author`)

**Candidatos iniciales a investigar:**
- [ ] Buscar en IG por hashtags y ubicación
- [ ] Revisar autores frecuentes en DB actual
- [ ] Buscar en Google "inmobiliaria maracaibo"
- [ ] Grupos Facebook (ej: "Bienes Raíces Maracaibo")

#### 2.2 Mejoras al Scraping

- [ ] Detección automática de duplicados cross-platform
- [ ] Extracción de contacto del vendedor (cuando esté público)
- [ ] Geocoding de direcciones (Nominatim/Mapbox)
- [ ] Scraping de precios históricos (tracking cambios)

### Fase 3: Portal B2B (Futuro)

**Servicios para Realtors:**

| Servicio | Descripción | Pricing |
|----------|-------------|---------|
| Listado preferencial | Aparece primero en búsquedas | $X/mes |
| Acceso a leads | Base de datos de prospectos | $X/lead o suscripción |
| Inteligencia de mercado | Reportes de precios, demanda | $X/mes |
| Marketing | Email a leads con sus propiedades | $X/campaña |

**Esto requiere validación de mercado primero.**

---

## 🛠️ Plan de Ejecución

### Sprint 1 (Semana 1-2): Foundation

| Tarea | Esfuerzo | Prioridad |
|-------|----------|-----------|
| Setup proyecto Next.js + Tailwind | 2h | P0 |
| Migrar DB a Supabase (PostgreSQL) | 4h | P0 |
| API endpoints básicos (listings) | 4h | P0 |
| Página de búsqueda con filtros | 8h | P0 |
| Página de detalle de propiedad | 4h | P0 |
| Deploy inicial a Vercel | 2h | P0 |

**Entregable:** Web funcional con búsqueda básica

### Sprint 2 (Semana 3-4): Lead Capture

| Tarea | Esfuerzo | Prioridad |
|-------|----------|-----------|
| Auth con email/WhatsApp (Supabase) | 4h | P0 |
| Sistema de favoritos | 4h | P0 |
| Sistema de alertas | 6h | P0 |
| Formulario "Contactar vendedor" | 2h | P0 |
| Setup Plausible analytics | 2h | P1 |
| Event tracking básico | 4h | P1 |

**Entregable:** Sistema de captura de leads funcionando

### Sprint 3 (Semana 5-6): UX Polish

| Tarea | Esfuerzo | Prioridad |
|-------|----------|-----------|
| Vista de mapa con clusters | 6h | P1 |
| Comparador de propiedades | 4h | P1 |
| Galería de imágenes mejorada | 3h | P1 |
| Mobile-first responsive | 4h | P0 |
| Newsletter semanal automático | 4h | P1 |
| SEO básico | 2h | P1 |

**Entregable:** UX pulido, ready for launch

### Sprint 4 (Semana 7-8): Métricas y Expansión

| Tarea | Esfuerzo | Prioridad |
|-------|----------|-----------|
| Dashboard interno de métricas | 6h | P1 |
| Investigar nuevos realtors | 4h | P1 |
| Agregar nuevas fuentes | 4h | P1 |
| A/B testing framework | 4h | P2 |
| Landing page para realtors (B2B) | 4h | P2 |

**Entregable:** Plataforma con métricas, más fuentes

---

## 💰 Costos Estimados

| Recurso | Costo/mes | Notas |
|---------|-----------|-------|
| Vercel | $0 | Free tier suficiente inicialmente |
| Supabase | $0 | Free tier (500MB, 50K requests) |
| Plausible | $9 | Analytics |
| Dominio | $1 | .com.ve o similar |
| Apify | ~$10 | Ya existente |
| **Total MVP** | **~$20/mes** | |

---

## 📊 Métricas de Éxito

### MVP (8 semanas)
- [ ] Web live con dominio propio
- [ ] ≥100 visitantes únicos/mes
- [ ] ≥10 leads capturados
- [ ] ≥500 listings en DB

### 3 meses
- [ ] ≥500 visitantes únicos/mes
- [ ] ≥50 leads activos
- [ ] ≥3 conversiones trackeadas
- [ ] ≥1000 listings en DB

### 6 meses
- [ ] ≥2000 visitantes únicos/mes
- [ ] ≥200 leads activos
- [ ] Primeros ingresos B2B
- [ ] ≥2000 listings en DB

---

## ⚠️ Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Bajo tráfico | Alta | Alto | SEO, contenido, redes sociales |
| Datos desactualizados | Media | Alto | Scraping más frecuente, validación |
| Realtors molestos | Baja | Medio | Dar crédito, ofrecer partnership |
| Competencia | Baja | Medio | Diferenciarse con UX y datos |
| Abandono de proyecto | Media | Alto | Sprints cortos, MVPs iterativos |

---

## 🤔 Decisiones Pendientes

1. **¿Dominio?** Opciones: maracaiborealestate.com, casasmaracaibo.com, inmuebles-mcbo.com
2. **¿Framework?** Next.js vs Astro (Astro más simple, Next.js más features)
3. **¿Mapa?** Mapbox (mejor UX, costo) vs Leaflet (gratis, más trabajo)
4. **¿Auth?** Solo email vs WhatsApp vs ambos
5. **¿Nombre del proyecto?** Sugerencias bienvenidas

---

## ✅ Próximos Pasos

Esperando aprobación para:

1. Confirmar stack técnico (Next.js + Supabase + Vercel)
2. Definir dominio
3. Comenzar Sprint 1

---

*Documento creado por Alfred | Última actualización: 2025-02-25*
