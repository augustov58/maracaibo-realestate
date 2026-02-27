# Arquitectura: Sistema de Almacenamiento de Imágenes (Opción C)

**Status:** 📋 Documentado para implementación futura  
**Fecha:** 2026-02-27  
**Prioridad:** Media (implementar si URLs de Instagram siguen expirando)

---

## Problema que resuelve

1. **URLs de Instagram expiran** - Las URLs de `cdninstagram.com` tienen tokens temporales que expiran después de días/semanas
2. **Hotlink protection** - Algunos sitios bloquean referencias externas (403 Forbidden)
3. **Dependencia de terceros** - Si el sitio original baja la imagen, la perdemos
4. **Rendimiento** - Cargar desde múltiples dominios es más lento que un CDN propio

---

## Arquitectura Propuesta

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FLUJO DE IMÁGENES                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────┐    │
│  │  Scrapers    │────▶│  Image       │────▶│  Supabase        │    │
│  │  (IG, Web)   │     │  Processor   │     │  Storage         │    │
│  │              │     │              │     │  (Bucket: images)│    │
│  │  URLs temp   │     │  - Download  │     │                  │    │
│  │  originales  │     │  - Resize    │     │  /listings/{id}/ │    │
│  │              │     │  - Optimize  │     │    - thumb.webp  │    │
│  │              │     │  - Upload    │     │    - 1.webp      │    │
│  └──────────────┘     └──────────────┘     │    - 2.webp      │    │
│                                            │    - ...         │    │
│                                            └────────┬─────────┘    │
│                                                     │              │
│                       ┌─────────────────────────────┘              │
│                       │                                            │
│                       ▼                                            │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │                    mcv_listings                          │     │
│  │  ───────────────────────────────────────────────────────│     │
│  │  id: 123                                                 │     │
│  │  images_original: ["https://cdninstagram.com/..."]       │     │
│  │  images_stored: [                                        │     │
│  │    "https://blvambo...supabase.co/storage/v1/object/    │     │
│  │     public/images/listings/123/1.webp",                  │     │
│  │    "https://blvambo...supabase.co/storage/v1/object/    │     │
│  │     public/images/listings/123/2.webp"                   │     │
│  │  ]                                                       │     │
│  │  thumbnail: "https://.../listings/123/thumb.webp"        │     │
│  └──────────────────────────────────────────────────────────┘     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Componentes

### 1. Image Processor (Python)

```python
# scripts/process-images.py

import os
import httpx
from PIL import Image
from io import BytesIO
from supabase import create_client

SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_KEY = os.environ['SUPABASE_SERVICE_KEY']
BUCKET = 'images'

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

async def process_listing_images(listing_id: int, image_urls: list[str]) -> dict:
    """
    Download, optimize, and store images for a listing.
    Returns dict with stored URLs.
    """
    stored = []
    thumbnail = None
    
    async with httpx.AsyncClient() as client:
        for i, url in enumerate(image_urls[:10]):  # Max 10 images
            try:
                # Download
                resp = await client.get(url, timeout=30)
                if resp.status_code != 200:
                    continue
                
                # Process with Pillow
                img = Image.open(BytesIO(resp.content))
                
                # Convert to WebP for smaller size
                buffer = BytesIO()
                img.save(buffer, 'WEBP', quality=85)
                buffer.seek(0)
                
                # Upload to Supabase Storage
                path = f"listings/{listing_id}/{i+1}.webp"
                supabase.storage.from_(BUCKET).upload(
                    path, 
                    buffer.getvalue(),
                    {'content-type': 'image/webp'}
                )
                
                # Get public URL
                public_url = supabase.storage.from_(BUCKET).get_public_url(path)
                stored.append(public_url)
                
                # Create thumbnail from first image
                if i == 0:
                    img.thumbnail((400, 300))
                    thumb_buffer = BytesIO()
                    img.save(thumb_buffer, 'WEBP', quality=80)
                    thumb_buffer.seek(0)
                    
                    thumb_path = f"listings/{listing_id}/thumb.webp"
                    supabase.storage.from_(BUCKET).upload(
                        thumb_path,
                        thumb_buffer.getvalue(),
                        {'content-type': 'image/webp'}
                    )
                    thumbnail = supabase.storage.from_(BUCKET).get_public_url(thumb_path)
                    
            except Exception as e:
                print(f"Error processing image {url}: {e}")
                continue
    
    return {
        'images_stored': stored,
        'thumbnail': thumbnail
    }
```

### 2. Supabase Storage Setup

```sql
-- Crear bucket público para imágenes
INSERT INTO storage.buckets (id, name, public)
VALUES ('images', 'images', true);

-- Policy: permitir lectura pública
CREATE POLICY "Public read access"
ON storage.objects FOR SELECT
USING (bucket_id = 'images');

-- Policy: permitir escritura solo con service key
CREATE POLICY "Service role write access"
ON storage.objects FOR INSERT
WITH CHECK (
    bucket_id = 'images' 
    AND auth.role() = 'service_role'
);
```

### 3. Modificar tabla mcv_listings

```sql
-- Agregar columnas para URLs almacenadas
ALTER TABLE mcv_listings 
ADD COLUMN images_stored TEXT[] DEFAULT '{}',
ADD COLUMN thumbnail TEXT;

-- Índice para búsquedas
CREATE INDEX idx_listings_has_stored_images 
ON mcv_listings ((images_stored IS NOT NULL AND array_length(images_stored, 1) > 0));
```

### 4. GitHub Action para procesar imágenes

```yaml
# .github/workflows/process-images.yml
name: Process Images

on:
  schedule:
    - cron: '30 */6 * * *'  # Cada 6 horas
  workflow_dispatch:

jobs:
  process:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install httpx pillow supabase
      
      - name: Process pending images
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_SERVICE_KEY: ${{ secrets.SUPABASE_SERVICE_KEY }}
        run: python scripts/process-images.py --pending-only
```

### 5. Frontend: Usar imágenes almacenadas

```typescript
// components/property/PropertyCard.tsx

function getImageUrl(listing: Listing): string {
  // Preferir thumbnail almacenado
  if (listing.thumbnail) {
    return listing.thumbnail;
  }
  
  // Fallback a imágenes almacenadas
  if (listing.images_stored?.length > 0) {
    return listing.images_stored[0];
  }
  
  // Último recurso: URL original (puede expirar)
  if (listing.images?.length > 0) {
    const img = listing.images[0];
    // Skip Instagram URLs (403)
    if (!img.includes('instagram') && !img.includes('cdninstagram')) {
      return img;
    }
  }
  
  return '/placeholder-house.svg';
}
```

---

## Costos Estimados

| Recurso | Free Tier | Costo estimado |
|---------|-----------|----------------|
| Supabase Storage | 1GB | $0.021/GB después |
| Bandwidth | 2GB/mes | $0.09/GB después |
| **Estimado mensual** | | **$0-5/mes** (con ~1000 listings) |

---

## Pasos de Implementación

1. [ ] Crear bucket `images` en Supabase Storage
2. [ ] Agregar columnas `images_stored` y `thumbnail` a `mcv_listings`
3. [ ] Crear script `process-images.py`
4. [ ] Agregar GitHub Action para procesamiento
5. [ ] Modificar frontend para preferir URLs almacenadas
6. [ ] Backfill: procesar imágenes de listings existentes

---

## Cuándo implementar

Implementar si:
- ❌ Más del 30% de imágenes dan 403/404
- ❌ Usuarios se quejan de imágenes rotas
- ❌ Instagram cambia su política de URLs

Por ahora, la **Opción A** (usar el campo `images` existente) es suficiente.
