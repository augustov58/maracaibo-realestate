#!/usr/bin/env python3
"""
Real Estate Data Analysis v2 - Improved charts
- Filter outliers
- Better sector extraction
- Proper scales
"""

import sys
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import seaborn as sns
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from db import get_listings

plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

OUTPUT_DIR = Path(__file__).parent.parent / 'data' / 'charts'
OUTPUT_DIR.mkdir(exist_ok=True)

MARACAIBO_SECTORS = [
    'Bella Vista', 'Tierra Negra', 'La Lago', 'Lago Mar Beach', 'Santa Lucia',
    'El Milagro', 'Sabaneta', 'Juana de Avila', 'Virginia', 'La Virginia',
    'Cecilio Acosta', 'Don Bosco', 'La Victoria', 'Las Mercedes', 'Amparo',
    'Coquivacoa', 'Chiquinquira', 'Santa Fe', 'La Limpia', 'Ciudadela',
    'Pomona', 'Indio Mara', 'Monte Claro', 'Monte Bello', 'La Paragua',
    'Los Olivos', 'San Francisco', 'La Coromoto', 'Paraiso', 'Delicias',
    '5 de Julio', 'Padilla', 'Canta Claro', 'Irama', 'El Naranjal',
    'Panamericano', 'Los Haticos', 'Raul Leoni', 'Sur America', 'El Trebol',
    'Isla Dorada', 'Banco Mara', 'Las Naciones', 'San Jacinto', 'Veritas',
    'Bellas Artes', 'El Rosal', 'La Florida', 'Los Estanques', 'Urb Maracaibo'
]

def extract_sector(location):
    """Extract specific sector from location string"""
    if pd.isna(location):
        return 'Sin ubicación'
    
    loc_lower = str(location).lower()
    
    # Check for known sectors
    for sector in MARACAIBO_SECTORS:
        if sector.lower() in loc_lower:
            return sector
    
    # If has " - " format, take the second part
    if ' - ' in str(location):
        parts = str(location).split(' - ')
        if len(parts) > 1:
            return parts[1].strip()[:20]
    
    # Default to city level
    if 'maracaibo' in loc_lower:
        return 'Maracaibo (otro)'
    elif 'zulia' in loc_lower:
        return 'Zulia (otro)'
    
    return 'Otro'

def load_data():
    """Load and clean listings data"""
    listings = get_listings(limit=500)
    df = pd.DataFrame(listings)
    
    # Filter: must have price and size
    df = df[df['price_usd'].notna() & (df['price_usd'] > 0)]
    df = df[df['sqm'].notna() & (df['sqm'] > 0)]
    
    # Filter out obvious outliers
    df = df[df['sqm'] < 2000]  # No properties > 2000m²
    df = df[df['sqm'] > 10]    # No properties < 10m²
    df = df[df['price_usd'] >= 1000]  # Filter out rentals (< $1000)
    
    # Calculate price per sqm
    df['price_per_sqm'] = df['price_usd'] / df['sqm']
    
    # Filter extreme price/sqm
    df = df[df['price_per_sqm'] < 5000]  # Max $5000/m²
    df = df[df['price_per_sqm'] > 10]    # Min $10/m²
    
    # Extract sectors
    df['sector'] = df['location'].apply(extract_sector)
    
    # Clean property types
    df['property_type'] = df['property_type'].fillna('otro')
    
    print(f"Loaded {len(df)} listings after filtering")
    return df

def scatter_price_vs_size(df):
    """Improved scatter plot with proper scale"""
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Color by property type
    property_types = ['apartamento', 'casa', 'townhouse', 'terreno', 'comercial']
    colors = {'apartamento': '#2ecc71', 'casa': '#e74c3c', 'townhouse': '#3498db', 
              'terreno': '#f39c12', 'comercial': '#9b59b6', 'otro': '#95a5a6'}
    
    for ptype in property_types:
        subset = df[df['property_type'] == ptype]
        if len(subset) > 0:
            ax.scatter(subset['sqm'], subset['price_usd'], 
                       label=f"{ptype.title()} ({len(subset)})", 
                       alpha=0.7, s=150, c=colors.get(ptype, '#95a5a6'),
                       edgecolors='white', linewidths=1)
    
    # Add trend line
    z = np.polyfit(df['sqm'], df['price_usd'], 1)
    p = np.poly1d(z)
    x_line = np.linspace(df['sqm'].min(), df['sqm'].max(), 100)
    ax.plot(x_line, p(x_line), "k--", alpha=0.6, linewidth=2, 
            label=f'Tendencia (${z[0]:,.0f}/m²)')
    
    # Find undervalued (30%+ below trend)
    df['expected_price'] = p(df['sqm'])
    df['discount'] = (df['expected_price'] - df['price_usd']) / df['expected_price'] * 100
    undervalued = df[df['discount'] > 30].copy()
    
    # Highlight undervalued
    if len(undervalued) > 0:
        ax.scatter(undervalued['sqm'], undervalued['price_usd'], 
                   s=300, facecolors='none', edgecolors='#27ae60', linewidths=3,
                   label=f'🎯 Subvalorado >30% ({len(undervalued)})', zorder=5)
        
        # Annotate top 3 undervalued
        for _, row in undervalued.nlargest(3, 'discount').iterrows():
            ax.annotate(f"-{row['discount']:.0f}%", 
                       (row['sqm'], row['price_usd']),
                       xytext=(10, 10), textcoords='offset points',
                       fontsize=10, fontweight='bold', color='#27ae60')
    
    ax.set_xlabel('Tamaño (m²)', fontsize=14)
    ax.set_ylabel('Precio (USD)', fontsize=14)
    ax.set_title('Precio vs Tamaño - Encuentra Oportunidades Subvaloradas', 
                 fontsize=16, fontweight='bold', pad=20)
    ax.legend(loc='upper left', fontsize=11)
    
    # Format axes
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    ax.set_xlim(0, df['sqm'].max() * 1.1)
    ax.set_ylim(0, df['price_usd'].max() * 1.1)
    
    # Add grid
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    filepath = OUTPUT_DIR / 'scatter_price_vs_size_v2.png'
    plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    return filepath, undervalued

def price_per_sqm_by_sector(df):
    """Price per m² by Maracaibo sector"""
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Group by sector
    sector_stats = df.groupby('sector').agg({
        'price_per_sqm': ['mean', 'median', 'count'],
        'price_usd': 'mean'
    }).round(0)
    sector_stats.columns = ['avg_per_sqm', 'median_per_sqm', 'count', 'avg_price']
    sector_stats = sector_stats[sector_stats['count'] >= 1]  # At least 1 listing
    sector_stats = sector_stats.sort_values('median_per_sqm', ascending=True)
    
    # Limit to top 15 sectors
    if len(sector_stats) > 15:
        sector_stats = sector_stats.head(15)
    
    # Plot
    median_val = sector_stats['median_per_sqm'].median()
    colors = ['#27ae60' if x < median_val else '#e74c3c' for x in sector_stats['median_per_sqm']]
    
    bars = ax.barh(sector_stats.index, sector_stats['median_per_sqm'], 
                   color=colors, alpha=0.85, height=0.7, edgecolor='white')
    
    # Add value and count labels
    for i, (idx, row) in enumerate(sector_stats.iterrows()):
        ax.text(row['median_per_sqm'] + 15, i, 
                f"${row['median_per_sqm']:,.0f}/m² (n={int(row['count'])})", 
                va='center', fontsize=11, fontweight='bold')
    
    ax.axvline(median_val, color='navy', linestyle='--', linewidth=2,
               label=f"Mediana: ${median_val:,.0f}/m²")
    
    ax.set_xlabel('Precio Mediano por m² (USD)', fontsize=14)
    ax.set_ylabel('Sector', fontsize=14)
    ax.set_title('Precio por m² por Sector - Verde = Mejor Valor', 
                 fontsize=16, fontweight='bold', pad=20)
    ax.legend(loc='lower right', fontsize=12)
    
    # Expand x-axis for labels
    ax.set_xlim(0, sector_stats['median_per_sqm'].max() * 1.4)
    
    plt.tight_layout()
    filepath = OUTPUT_DIR / 'price_per_sqm_by_sector_v2.png'
    plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    return filepath, sector_stats

def price_per_sqm_distribution(df):
    """Box plot with better scale"""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Filter to main types
    main_types = ['apartamento', 'casa', 'townhouse']
    df_filtered = df[df['property_type'].isin(main_types)].copy()
    
    # Create box plot with swarm
    colors = {'apartamento': '#2ecc71', 'casa': '#e74c3c', 'townhouse': '#3498db'}
    
    box = ax.boxplot([df_filtered[df_filtered['property_type'] == t]['price_per_sqm'] 
                      for t in main_types],
                     labels=[t.title() for t in main_types],
                     patch_artist=True, widths=0.6)
    
    # Color boxes
    for patch, ptype in zip(box['boxes'], main_types):
        patch.set_facecolor(colors[ptype])
        patch.set_alpha(0.7)
    
    # Add individual points
    for i, ptype in enumerate(main_types):
        subset = df_filtered[df_filtered['property_type'] == ptype]['price_per_sqm']
        x = np.random.normal(i+1, 0.08, size=len(subset))
        ax.scatter(x, subset, alpha=0.5, s=60, c=colors[ptype], edgecolors='white')
    
    # Add median labels
    for i, ptype in enumerate(main_types):
        subset = df_filtered[df_filtered['property_type'] == ptype]['price_per_sqm']
        median = subset.median()
        count = len(subset)
        ax.text(i+1, median + 30, f'${median:,.0f}\n(n={count})', 
                ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    ax.set_xlabel('Tipo de Propiedad', fontsize=14)
    ax.set_ylabel('Precio por m² (USD)', fontsize=14)
    ax.set_title('Distribución del Precio por m² - Por Tipo de Propiedad', 
                 fontsize=16, fontweight='bold', pad=20)
    
    # Better y-axis scale
    ax.set_ylim(0, df_filtered['price_per_sqm'].quantile(0.95) * 1.2)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    ax.grid(True, axis='y', alpha=0.3)
    
    plt.tight_layout()
    filepath = OUTPUT_DIR / 'distribution_by_type_v2.png'
    plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    return filepath

def generate_report():
    """Generate all improved charts"""
    print("Loading and cleaning data...")
    df = load_data()
    
    if len(df) < 5:
        print("Not enough data for analysis")
        return None
    
    print(f"\nData summary:")
    print(f"  Total listings: {len(df)}")
    print(f"  Price range: ${df['price_usd'].min():,.0f} - ${df['price_usd'].max():,.0f}")
    print(f"  Size range: {df['sqm'].min():.0f} - {df['sqm'].max():.0f} m²")
    print(f"  Sectors found: {df['sector'].nunique()}")
    
    print("\nGenerating scatter plot...")
    scatter_path, undervalued = scatter_price_vs_size(df)
    print(f"  ✓ {scatter_path}")
    
    print("\nGenerating sector comparison...")
    sector_path, sector_stats = price_per_sqm_by_sector(df)
    print(f"  ✓ {sector_path}")
    
    print("\nGenerating type distribution...")
    dist_path = price_per_sqm_distribution(df)
    print(f"  ✓ {dist_path}")
    
    print("\n" + "="*50)
    print("🏆 TOP SUBVALORADAS (>30% bajo tendencia):")
    print("="*50)
    
    if len(undervalued) > 0:
        for i, (_, row) in enumerate(undervalued.nlargest(5, 'discount').iterrows(), 1):
            print(f"\n{i}. {row['property_type'].title()} - {row['sector']}")
            print(f"   💰 ${row['price_usd']:,.0f} | 📐 {row['sqm']:.0f}m² | ${row['price_per_sqm']:,.0f}/m²")
            print(f"   📉 {row['discount']:.0f}% bajo tendencia")
            print(f"   🔗 {row['url']}")
    else:
        print("No se encontraron propiedades significativamente subvaloradas.")
    
    return [scatter_path, sector_path, dist_path]

if __name__ == '__main__':
    generate_report()
