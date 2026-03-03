#!/usr/bin/env python3
"""
AI-powered enrichment for real estate listings.
Uses Gemini (free tier), OpenAI, or regex fallback.
"""

import os
import json
import re
from typing import Optional

# Try to import AI clients
HAS_OPENAI = False
HAS_GEMINI = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    pass

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    pass

# Known sectors in Maracaibo (for normalization)
KNOWN_SECTORS = [
    "5 de Julio", "Amparo", "Av. El Milagro", "Bancomara", "Bella Vista",
    "Canchancha", "Canta Claro", "Cecilio Acosta", "Circunvalación 2",
    "Ciudadela Faria", "Coquivacoa", "Delicias", "Don Bosco", "El Milagro",
    "El Pilar", "El Rosal", "Fuerzas Armadas", "Gallo Verde", "Indio Mara",
    "Juana de Ávila", "La California", "La Coromoto", "La Florida", "La Lago",
    "La Limpia", "La Paragua", "La Paz", "La Trinidad", "La Victoria",
    "La Virginia", "Lago Mar Beach", "Las Acacias", "Las Delicias", "Las Mercedes",
    "Los Estanques", "Los Haticos", "Los Olivos", "Monte Bello", "Monte Claro",
    "Paraíso", "Pomona", "Raúl Leoni", "Sabaneta", "San Francisco",
    "San Jacinto", "Santa Fe", "Santa Lucía", "Santa María", "Santa Rita",
    "Sector Veritas", "Sierra Maestra", "Tierra Negra", "Urb. La Trinidad",
    "Valle Frío", "Villa Antoanona", "Zapara", "Zona Industrial", "Zona Norte",
    "Av. 72", "Av. Universidad", "Padilla", "Chiquinquirá"
]

# Mapping for normalization
SECTOR_ALIASES = {
    "acacias": "Las Acacias",
    "las acacias": "Las Acacias",
    "5 julio": "5 de Julio",
    "cinco de julio": "5 de Julio",
    "av 5 de julio": "5 de Julio",
    "milagro": "Av. El Milagro",
    "el milagro": "Av. El Milagro",
    "av el milagro": "Av. El Milagro",
    "av. el milagro": "Av. El Milagro",
    "la lago": "La Lago",
    "lalago": "La Lago",
    "tierra negra": "Tierra Negra",
    "tierranegra": "Tierra Negra",
    "bella vista": "Bella Vista",
    "bellavista": "Bella Vista",
    "lago mar": "Lago Mar Beach",
    "lagomarbeach": "Lago Mar Beach",
    "lago mar beach": "Lago Mar Beach",
    "juana de avila": "Juana de Ávila",
    "virginia": "La Virginia",
    "la virginia": "La Virginia",
    "antoanona": "Villa Antoanona",
    "villa antoanona": "Villa Antoanona",
    "sabaneta": "Sabaneta",
    "pomona": "Pomona",
    "indio mara": "Indio Mara",
    "indiomara": "Indio Mara",
    "monte claro": "Monte Claro",
    "monteclaro": "Monte Claro",
    "monte bello": "Monte Bello",
    "montebello": "Monte Bello",
    "cecilio acosta": "Cecilio Acosta",
    "don bosco": "Don Bosco",
    "donbosco": "Don Bosco",
    "canta claro": "Canta Claro",
    "cantaclaro": "Canta Claro",
    "zona norte": "Zona Norte",
    "av 72": "Av. 72",
    "avenida 72": "Av. 72",
    "calle 72": "Av. 72",
    "c 72": "Av. 72",
    "santa rita": "Santa Rita",
    "santarita": "Santa Rita",
    "san francisco": "San Francisco",
    "sanfrancisco": "San Francisco",
    "coromoto": "La Coromoto",
    "la coromoto": "La Coromoto",
    "paraiso": "Paraíso",
    "el paraiso": "Paraíso",
}


def load_env():
    """Load environment variables from .env file."""
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    env_vars[key] = value.strip('"\'')
    return env_vars


def get_gemini_model():
    """Get Gemini model with API key from environment."""
    api_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        env_vars = load_env()
        api_key = env_vars.get('GEMINI_API_KEY') or env_vars.get('GOOGLE_API_KEY')
    
    if not api_key or not HAS_GEMINI:
        return None
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.0-flash')


def get_openai_client():
    """Get OpenAI client with API key from environment."""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        env_vars = load_env()
        api_key = env_vars.get('OPENAI_API_KEY')
    
    if not api_key or not HAS_OPENAI:
        return None
    
    return OpenAI(api_key=api_key)


def normalize_sector(sector: str) -> str:
    """Normalize sector name to canonical form."""
    if not sector:
        return sector
    
    # Clean up
    sector_clean = sector.strip().lower()
    sector_clean = re.sub(r'\s+', ' ', sector_clean)
    
    # Check aliases
    if sector_clean in SECTOR_ALIASES:
        return SECTOR_ALIASES[sector_clean]
    
    # Check if it's already a known sector (case insensitive)
    for known in KNOWN_SECTORS:
        if known.lower() == sector_clean:
            return known
    
    # Return title case if not found
    return sector.strip().title()


def extract_sector_from_text(text: str) -> Optional[str]:
    """Try to extract sector using regex patterns (fast, no API)."""
    text_lower = text.lower()
    
    # Direct mention patterns
    patterns = [
        r'(?:sector|urb\.?|urbanización|ubicado en|zona)\s+([a-záéíóúñ\s]+)',
        r'en\s+(las?\s+[a-záéíóúñ]+)',  # "en Las Acacias", "en La Lago"
        r'(?:maracaibo|mcbo)[,\s]+([a-záéíóúñ\s]+)',  # After Maracaibo comma
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            candidate = match.group(1).strip()
            # Check if it's a known sector
            normalized = normalize_sector(candidate)
            if normalized in KNOWN_SECTORS:
                return normalized
    
    # Check for any known sector mentioned in text
    for known in KNOWN_SECTORS:
        if known.lower() in text_lower:
            return known
    
    # Check aliases
    for alias, canonical in SECTOR_ALIASES.items():
        if alias in text_lower:
            return canonical
    
    return None


def clean_description_regex(text: str) -> str:
    """Clean description using regex (fast, no API)."""
    if not text:
        return text
    
    # Remove social media spam
    text = re.sub(r'(?:Copiar link|Whatsapp|Facebook|Twitter|LinkedIn|Instagram)\s*', '', text, flags=re.I)
    text = re.sub(r'(?:Previous|Next|Ver más|Más detalles)\s*', '', text, flags=re.I)
    
    # Remove URLs
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'www\.\S+', '', text)
    
    # Remove repeated promotional text
    text = re.sub(r'Le invitamos a navegar en www\..*?(?:disponibles para usted\.?)?', '', text, flags=re.I)
    text = re.sub(r'Póngase siempre en manos de un profesional inmobiliario\.?', '', text, flags=re.I)
    text = re.sub(r'La información contenida en este anuncio.*?propietario\.?', '', text, flags=re.I | re.DOTALL)
    text = re.sub(r'cada propiedad tiene una historia.*?profesional\.?', '', text, flags=re.I)
    
    # Remove property codes (API, Cód., etc.)
    text = re.sub(r'(?:API|Cód\.?|Código)\s*\d+\s*', '', text, flags=re.I)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def enrich_with_ai(listing: dict, client=None, force_ai: bool = False) -> dict:
    """Enrich a listing with AI extraction.
    
    Args:
        listing: Dict with 'text', 'location', etc.
        client: AI client (Gemini or OpenAI, optional, will create if needed)
        force_ai: Always use AI (for Instagram, etc.)
    
    Returns:
        Enriched listing dict
    """
    text = listing.get('text', '')
    current_location = listing.get('location', '')
    source = listing.get('source', 'website')
    
    # Instagram always needs AI - captions are too messy for regex
    is_instagram = source == 'instagram'
    
    # First try regex-based extraction (fast, free) - skip for Instagram
    if not is_instagram:
        extracted_sector = extract_sector_from_text(text)
        cleaned_text = clean_description_regex(text)
        
        # If location is generic and we found a sector, update it
        if current_location in ['Maracaibo', 'Zulia', None, ''] and extracted_sector:
            listing['location'] = f"Maracaibo - {extracted_sector}"
            listing['sector'] = extracted_sector
        elif extracted_sector and extracted_sector not in (current_location or ''):
            # Add sector even if location exists
            listing['sector'] = extracted_sector
        
        # Update cleaned description
        if cleaned_text != text:
            listing['description_clean'] = cleaned_text
    
    # Determine if we need AI
    needs_ai = force_ai or is_instagram or (
        (current_location in ['Maracaibo', 'Zulia', None, ''] and not listing.get('sector')) or
        len(text) > 500  # Long descriptions might have hidden info
    )
    
    # Try AI enrichment if needed (prefer Gemini - free tier)
    if needs_ai:
        if HAS_GEMINI:
            if client is None:
                client = get_gemini_model()
            if client:
                listing = _enrich_with_gemini(listing, client)
        elif HAS_OPENAI:
            if client is None:
                client = get_openai_client()
            if client:
                listing = _enrich_with_openai(listing, client)
    
    return listing


def _get_ai_prompt(text: str, source: str = 'website') -> str:
    """Generate the prompt for AI extraction."""
    
    if source == 'instagram':
        return f"""Analiza este post de Instagram de una inmobiliaria en Maracaibo, Venezuela.
Extrae la información estructurada del inmueble.

Post de Instagram:
{text}

Responde SOLO en JSON con estos campos (usa null si no encuentras el dato):
{{
  "sector": "sector/barrio/urbanización (ej: Las Acacias, Tierra Negra)",
  "tipo": "apartamento|casa|townhouse|terreno|local",
  "precio": número en USD (solo el número, sin símbolos),
  "habitaciones": número,
  "banos": número,
  "metros": número de m²,
  "descripcion": "descripción limpia y concisa del inmueble (sin hashtags, sin datos de contacto, sin emojis excesivos, máximo 200 caracteres)"
}}"""
    else:
        return f"""Analiza este anuncio de inmueble en Maracaibo, Venezuela y extrae:

1. SECTOR: El sector/barrio/urbanización específico (ej: "Las Acacias", "Tierra Negra", "5 de Julio")
2. DESCRIPCION_LIMPIA: La descripción limpia sin spam, links ni texto promocional

Texto del anuncio:
{text}

Responde SOLO en JSON:
{{"sector": "nombre del sector o null", "descripcion_limpia": "texto limpio"}}"""


def _parse_ai_response(listing: dict, content: str, source: str = 'website') -> dict:
    """Parse AI response and update listing."""
    try:
        # Handle markdown code blocks
        if '```' in content:
            match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
            if match:
                content = match.group(1)
        
        data = json.loads(content)
        
        # Sector (common to all sources)
        sector = data.get('sector')
        if sector and str(sector).lower() not in ['null', 'none', '']:
            normalized = normalize_sector(sector)
            listing['sector'] = normalized
            if listing.get('location') in ['Maracaibo', 'Zulia', None, '']:
                listing['location'] = f"Maracaibo - {normalized}"
        
        # Instagram: extract additional structured data
        if source == 'instagram':
            # Property type
            tipo = data.get('tipo')
            if tipo and str(tipo).lower() not in ['null', 'none', '']:
                listing['property_type'] = tipo.lower()
            
            # Price
            precio = data.get('precio')
            if precio and str(precio).lower() not in ['null', 'none', '']:
                try:
                    listing['price_usd'] = float(str(precio).replace(',', '').replace('$', ''))
                except:
                    pass
            
            # Bedrooms
            hab = data.get('habitaciones')
            if hab and str(hab).lower() not in ['null', 'none', '']:
                try:
                    listing['bedrooms'] = int(hab)
                except:
                    pass
            
            # Bathrooms
            banos = data.get('banos')
            if banos and str(banos).lower() not in ['null', 'none', '']:
                try:
                    listing['bathrooms'] = int(banos)
                except:
                    pass
            
            # Square meters
            metros = data.get('metros')
            if metros and str(metros).lower() not in ['null', 'none', '']:
                try:
                    listing['sqm'] = float(metros)
                except:
                    pass
            
            # Clean description
            desc = data.get('descripcion')
            if desc and str(desc).lower() not in ['null', 'none', '']:
                listing['description_clean'] = desc
        else:
            # Website: just clean description
            clean_desc = data.get('descripcion_limpia')
            if clean_desc:
                listing['description_clean'] = clean_desc
            
    except Exception:
        pass
    
    return listing


def _enrich_with_gemini(listing: dict, model) -> dict:
    """Use Gemini to extract additional information (FREE tier!)."""
    text = listing.get('text', '')[:2000]
    source = listing.get('source', 'website')
    prompt = _get_ai_prompt(text, source)
    
    try:
        response = model.generate_content(prompt)
        content = response.text.strip()
        listing = _parse_ai_response(listing, content, source)
    except Exception:
        pass
    
    return listing


def _enrich_with_openai(listing: dict, client) -> dict:
    """Use OpenAI to extract additional information."""
    text = listing.get('text', '')[:2000]
    source = listing.get('source', 'website')
    prompt = _get_ai_prompt(text, source)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0,
        )
        content = response.choices[0].message.content.strip()
        listing = _parse_ai_response(listing, content, source)
    except Exception:
        pass
    
    return listing


def enrich_batch(listings: list, use_ai: bool = True) -> list:
    """Enrich a batch of listings.
    
    Args:
        listings: List of listing dicts
        use_ai: Whether to use AI for complex cases
    
    Returns:
        List of enriched listings
    """
    client = None
    if use_ai and HAS_OPENAI:
        client = get_openai_client()
    
    enriched = []
    for listing in listings:
        enriched.append(enrich_with_ai(listing, client))
    
    return enriched


# Test
if __name__ == '__main__':
    import sys
    
    # Test cases
    test_listings = [
        {
            'source': 'angelpinton',
            'text': 'APARTAMENTO VENTA LAS ACACIAS MARACAIBO VENEZUELA API 8800 APARTAMENTO Cód. 8800 Las Acacias, Maracaibo - V Previous Next Copiar link Whatsapp Facebook Twitter LinkedIn US$ 34,000.00 Venta Consta de 98mtrs 3 habitaciones con clóset 3 salas sanitarias Cocina empotrada Sala Comedor Lavanderia Bondades Gas por tuberia Poco razonamiento circuito cerrado Portón eléctrico Queda en la Negociación 1 Aire de 3 toneladas Cocina Campana Despensa en la cocina Póngase siempre en manos de un profesional inmobiliario Le invitamos a navegar en www.angelpinton.com donde encontrará una gran gama de inmuebles disponibles para usted.',
            'location': 'Maracaibo',
        },
        {
            'source': 'website',
            'text': 'Hermoso apartamento en venta ubicado en el sector Tierra Negra, 3 habitaciones, 2 baños, cocina empotrada. Precio negociable.',
            'location': 'Maracaibo',
        },
        {
            'source': 'website',
            'text': 'Casa en venta Bella Vista, 4 hab, 3 baños, piscina. $150,000',
            'location': None,
        },
        {
            'source': 'instagram',
            'text': '''🏠✨ APARTAMENTO EN VENTA ✨🏠

📍 Sector Tierra Negra, Maracaibo

💰 $45,000 USD (NEGOCIABLE)

🛏️ 3 Habitaciones amplias con closet
🚿 2 Baños completos  
📐 120 m²
🍳 Cocina empotrada
🚗 Puesto de estacionamiento

✅ Excelente ubicación
✅ Cerca de centros comerciales
✅ Vigilancia 24 horas

📞 Contacto: 0424-123-4567
📱 WhatsApp: +58 424 123 4567

#apartamentoenventamaracaibo #tierranegra #maracaibo #inmuebles #bienesraices #venezuela #apartamento #venta #inversion #hogar #realestate''',
            'location': 'Maracaibo',
        }
    ]
    
    # Check if AI is available
    print(f"Gemini available: {HAS_GEMINI}")
    print(f"OpenAI available: {HAS_OPENAI}")
    
    if '--ai' in sys.argv:
        # Test with AI (requires API key)
        model = get_gemini_model()
        if not model:
            model = get_openai_client()
        if model:
            print(f"\nUsing AI model for enrichment...")
        else:
            print("\nNo AI API key found - using regex only")
            model = None
    else:
        model = None
        print("\nUsing regex only (pass --ai to test with AI)")
    
    for listing in test_listings:
        print(f"\n{'='*50}")
        print(f"Source: {listing.get('source')}")
        print(f"Original Location: {listing.get('location')}")
        print(f"Text: {listing['text'][:80]}...")
        
        enriched = enrich_with_ai(listing.copy(), client=model)
        
        print(f"\n--- Enriched ---")
        print(f"Location: {enriched.get('location')}")
        print(f"Sector: {enriched.get('sector')}")
        print(f"Type: {enriched.get('property_type')}")
        print(f"Price: {enriched.get('price_usd')}")
        print(f"Beds: {enriched.get('bedrooms')}")
        print(f"Baths: {enriched.get('bathrooms')}")
        print(f"SQM: {enriched.get('sqm')}")
        if enriched.get('description_clean'):
            print(f"Clean: {enriched.get('description_clean')[:100]}...")
