#!/usr/bin/env python3
"""
Real Estate Data Analysis & Visualization
Generates charts to find undervalued properties.
"""

import sys
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from db import get_listings

# Style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

OUTPUT_DIR = Path(__file__).parent.parent / 'data' / 'charts'
OUTPUT_DIR.mkdir(exist_ok=True)

def load_data():
    """Load listings into a pandas DataFrame"""
    listings = get_listings(limit=500)
    df = pd.DataFrame(listings)
    
    # Clean data
    df = df[df['price_usd'].notna() & (df['price_usd'] > 0)]
    df = df[df['sqm'].notna() & (df['sqm'] > 0)]
    
    # Calculate price per sqm
    df['price_per_sqm'] = df['price_usd'] / df['sqm']
    
    # Clean property types
    df['property_type'] = df['property_type'].fillna('otro')
    
    # Extract neighborhood from location
    df['neighborhood'] = df['location'].apply(lambda x: x.split(' - ')[-1] if pd.notna(x) and ' - ' in str(x) else (x if pd.notna(x) else 'Unknown'))
    
    return df

def scatter_price_vs_size(df):
    """Scatter plot: Price vs Size with trend line"""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Color by property type
    property_types = df['property_type'].unique()
    colors = sns.color_palette("husl", len(property_types))
    
    for ptype, color in zip(property_types, colors):
        subset = df[df['property_type'] == ptype]
        ax.scatter(subset['sqm'], subset['price_usd'], 
                   label=ptype.title(), alpha=0.7, s=100, c=[color])
    
    # Add trend line (all data)
    z = np.polyfit(df['sqm'], df['price_usd'], 1)
    p = np.poly1d(z)
    x_line = np.linspace(df['sqm'].min(), df['sqm'].max(), 100)
    ax.plot(x_line, p(x_line), "r--", alpha=0.8, linewidth=2, label=f'Trend (${z[0]:,.0f}/m²)')
    
    # Find undervalued (below trend line)
    df['expected_price'] = p(df['sqm'])
    df['discount'] = (df['expected_price'] - df['price_usd']) / df['expected_price'] * 100
    undervalued = df[df['discount'] > 20].sort_values('discount', ascending=False)
    
    # Highlight undervalued
    if len(undervalued) > 0:
        ax.scatter(undervalued['sqm'], undervalued['price_usd'], 
                   s=200, facecolors='none', edgecolors='green', linewidths=3,
                   label=f'Undervalued ({len(undervalued)})')
    
    ax.set_xlabel('Size (m²)', fontsize=12)
    ax.set_ylabel('Price (USD)', fontsize=12)
    ax.set_title('Price vs Size - Find Undervalued Properties', fontsize=14, fontweight='bold')
    ax.legend(loc='upper left')
    
    # Format y-axis as currency
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    
    plt.tight_layout()
    filepath = OUTPUT_DIR / 'scatter_price_vs_size.png'
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()
    
    return filepath, undervalued

def price_per_sqm_by_area(df):
    """Bar chart: Average price per m² by neighborhood"""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Group by neighborhood
    area_stats = df.groupby('neighborhood').agg({
        'price_per_sqm': ['mean', 'median', 'count'],
        'price_usd': 'mean'
    }).round(0)
    area_stats.columns = ['avg_per_sqm', 'median_per_sqm', 'count', 'avg_price']
    area_stats = area_stats[area_stats['count'] >= 2]  # At least 2 listings
    area_stats = area_stats.sort_values('avg_per_sqm', ascending=True)
    
    # Plot
    colors = ['green' if x < area_stats['avg_per_sqm'].median() else 'coral' 
              for x in area_stats['avg_per_sqm']]
    
    bars = ax.barh(area_stats.index, area_stats['avg_per_sqm'], color=colors, alpha=0.8)
    
    # Add count labels
    for i, (idx, row) in enumerate(area_stats.iterrows()):
        ax.text(row['avg_per_sqm'] + 10, i, f"n={int(row['count'])}", va='center', fontsize=9)
    
    ax.axvline(area_stats['avg_per_sqm'].median(), color='navy', linestyle='--', 
               label=f"Median: ${area_stats['avg_per_sqm'].median():,.0f}/m²")
    
    ax.set_xlabel('Average Price per m² (USD)', fontsize=12)
    ax.set_ylabel('Neighborhood', fontsize=12)
    ax.set_title('Price per m² by Area - Green = Below Median (Better Value)', fontsize=14, fontweight='bold')
    ax.legend()
    
    plt.tight_layout()
    filepath = OUTPUT_DIR / 'price_per_sqm_by_area.png'
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()
    
    return filepath, area_stats

def price_per_sqm_by_type(df):
    """Box plot: Price per m² by property type"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Filter to main types
    main_types = ['apartamento', 'casa', 'townhouse']
    df_filtered = df[df['property_type'].isin(main_types)]
    
    sns.boxplot(data=df_filtered, x='property_type', y='price_per_sqm', ax=ax, palette='husl')
    
    # Add individual points
    sns.stripplot(data=df_filtered, x='property_type', y='price_per_sqm', 
                  ax=ax, color='black', alpha=0.5, size=4)
    
    ax.set_xlabel('Property Type', fontsize=12)
    ax.set_ylabel('Price per m² (USD)', fontsize=12)
    ax.set_title('Price per m² Distribution by Property Type', fontsize=14, fontweight='bold')
    
    # Add median labels
    medians = df_filtered.groupby('property_type')['price_per_sqm'].median()
    for i, ptype in enumerate(main_types):
        if ptype in medians.index:
            ax.text(i, medians[ptype], f'${medians[ptype]:,.0f}', 
                    ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    filepath = OUTPUT_DIR / 'price_per_sqm_by_type.png'
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()
    
    return filepath

def find_undervalued(df, top_n=10):
    """Find the most undervalued properties"""
    # Calculate avg price per sqm by type and location
    df_clean = df.copy()
    
    # Group average
    type_avg = df_clean.groupby('property_type')['price_per_sqm'].mean()
    overall_avg = df_clean['price_per_sqm'].mean()
    
    # Calculate how much below average each listing is
    df_clean['type_avg'] = df_clean['property_type'].map(type_avg)
    df_clean['discount_pct'] = (df_clean['type_avg'] - df_clean['price_per_sqm']) / df_clean['type_avg'] * 100
    
    # Get top undervalued
    undervalued = df_clean[df_clean['discount_pct'] > 0].nlargest(top_n, 'discount_pct')
    
    return undervalued[['property_type', 'location', 'price_usd', 'sqm', 'price_per_sqm', 'discount_pct', 'url']]

def generate_report():
    """Generate all charts and return summary"""
    print("Loading data...")
    df = load_data()
    print(f"Loaded {len(df)} listings with price and size data")
    
    if len(df) < 5:
        print("Not enough data for analysis")
        return None
    
    print("\nGenerating scatter plot...")
    scatter_path, scatter_undervalued = scatter_price_vs_size(df)
    print(f"  Saved: {scatter_path}")
    
    print("\nGenerating price per m² by area...")
    area_path, area_stats = price_per_sqm_by_area(df)
    print(f"  Saved: {area_path}")
    
    print("\nGenerating price per m² by type...")
    type_path = price_per_sqm_by_type(df)
    print(f"  Saved: {type_path}")
    
    print("\nFinding undervalued properties...")
    undervalued = find_undervalued(df)
    
    # Summary
    print("\n" + "="*50)
    print("📊 ANALYSIS SUMMARY")
    print("="*50)
    print(f"\nTotal listings analyzed: {len(df)}")
    print(f"Average price: ${df['price_usd'].mean():,.0f}")
    print(f"Average price/m²: ${df['price_per_sqm'].mean():,.0f}")
    print(f"Median price/m²: ${df['price_per_sqm'].median():,.0f}")
    
    print("\n🏆 TOP UNDERVALUED PROPERTIES:")
    for i, (_, row) in enumerate(undervalued.head(5).iterrows(), 1):
        print(f"\n{i}. {row['property_type'].title()} - {row['location']}")
        print(f"   💰 ${row['price_usd']:,.0f} | 📐 {row['sqm']:.0f}m² | ${row['price_per_sqm']:,.0f}/m²")
        print(f"   📉 {row['discount_pct']:.0f}% below avg for type")
        print(f"   🔗 {row['url']}")
    
    return {
        'charts': [scatter_path, area_path, type_path],
        'undervalued': undervalued,
        'stats': {
            'total': len(df),
            'avg_price': df['price_usd'].mean(),
            'avg_per_sqm': df['price_per_sqm'].mean(),
            'median_per_sqm': df['price_per_sqm'].median()
        }
    }

if __name__ == '__main__':
    generate_report()
