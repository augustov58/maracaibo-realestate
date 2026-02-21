#!/usr/bin/env python3
"""
Maracaibo Real Estate Dashboard
Run with: streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))
from db import get_listings, get_db

# Page config
st.set_page_config(
    page_title="🏠 Maracaibo Real Estate",
    page_icon="🏠",
    layout="wide"
)

# Preferred sectors (from USER.md)
PREFERRED_SECTORS = [
    'Tierra Negra', 'El Milagro', 'Av. El Milagro', 'Bancomara', 'Banco Mara',
    '5 de Julio', 'Milagro', 'Santa Rita', 'La Lago', 'Bella Vista',
    'Canta Claro', 'Av. 72', 'Zona Norte'
]

def extract_sector(location):
    """Extract sector from location string"""
    if pd.isna(location) or not location:
        return 'Sin ubicación'
    
    loc_lower = str(location).lower()
    
    # Check for preferred sectors first
    for sector in PREFERRED_SECTORS:
        if sector.lower() in loc_lower:
            return sector
    
    # Known Maracaibo sectors
    sectors = [
        'Bella Vista', 'Tierra Negra', 'La Lago', 'Lago Mar Beach', 'Santa Lucia',
        'El Milagro', 'Sabaneta', 'Juana de Avila', 'Virginia', 'La Virginia',
        'Cecilio Acosta', 'Don Bosco', 'La Victoria', 'Las Mercedes', 'Amparo',
        'Coquivacoa', 'Chiquinquira', 'Santa Fe', 'La Limpia', 'Ciudadela',
        'Pomona', 'Indio Mara', 'Monte Claro', 'Monte Bello', 'La Paragua',
        'Los Olivos', 'San Francisco', 'La Coromoto', 'Paraiso', 'Delicias',
        '5 de Julio', 'Padilla', 'Canta Claro', 'Irama', 'El Naranjal',
        'Panamericano', 'Los Haticos', 'Raul Leoni', 'El Trebol',
        'Isla Dorada', 'Las Naciones', 'San Jacinto', 'El Rosal', 
        'La Florida', 'Los Estanques', 'Villa Antoañona'
    ]
    
    for sector in sectors:
        if sector.lower() in loc_lower:
            return sector
    
    # Extract from " - " format
    if ' - ' in str(location):
        return str(location).split(' - ')[-1].strip()[:25]
    
    return 'Otro'

def calculate_opportunity_score(row, median_price_per_sqm, trend_slope, trend_intercept):
    """
    Calculate opportunity score (0-100) based on:
    - Price vs trend line (40 points max)
    - Preferred sector (20 points)
    - Days on market (20 points max)
    - Price per sqm vs median (20 points max)
    """
    score = 0
    reasons = []
    
    # 1. Price vs trend line (40 points)
    if row['price_usd'] and row['sqm'] and row['sqm'] > 0:
        expected_price = trend_slope * row['sqm'] + trend_intercept
        if expected_price > 0:
            discount_pct = (expected_price - row['price_usd']) / expected_price * 100
            if discount_pct > 0:
                trend_points = min(40, discount_pct * 1.3)  # 30% discount = 40 points
                score += trend_points
                if discount_pct > 15:
                    reasons.append(f"{discount_pct:.0f}% bajo tendencia")
    
    # 2. Preferred sector (20 points)
    if row['is_preferred']:
        score += 20
        reasons.append("Zona preferida")
    
    # 3. Days on market (20 points) - more days = more negotiable
    if row['days_on_market'] and row['days_on_market'] > 0:
        dom_points = min(20, row['days_on_market'] * 2)  # 10+ days = max points
        score += dom_points
        if row['days_on_market'] >= 7:
            reasons.append(f"{row['days_on_market']} días en mercado")
    
    # 4. Price per sqm vs median (20 points)
    if row['price_per_sqm'] and median_price_per_sqm > 0:
        psqm_discount = (median_price_per_sqm - row['price_per_sqm']) / median_price_per_sqm * 100
        if psqm_discount > 0:
            psqm_points = min(20, psqm_discount * 0.8)  # 25% below median = 20 points
            score += psqm_points
            if psqm_discount > 20:
                reasons.append(f"$/m² {psqm_discount:.0f}% bajo mediana")
    
    return min(100, score), reasons

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data():
    """Load listings from database"""
    from datetime import datetime
    
    listings = get_listings(limit=500)
    df = pd.DataFrame(listings)
    
    if len(df) == 0:
        return df
    
    # Clean data
    df['sector'] = df['location'].apply(extract_sector)
    df['is_preferred'] = df['sector'].apply(lambda x: x in PREFERRED_SECTORS)
    df['property_type'] = df['property_type'].fillna('otro')
    
    # Filter out rentals for main analysis
    df['is_rental'] = df['price_usd'].apply(lambda x: x is not None and x < 1000)
    
    # Calculate price per sqm
    df['price_per_sqm'] = df.apply(
        lambda r: r['price_usd'] / r['sqm'] if r['price_usd'] and r['sqm'] and r['sqm'] > 0 else None, 
        axis=1
    )
    
    # Calculate days on market
    today = datetime.now().strftime('%Y-%m-%d')
    df['days_on_market'] = df['listing_date'].apply(
        lambda x: (datetime.strptime(today, '%Y-%m-%d') - datetime.strptime(x, '%Y-%m-%d')).days 
        if pd.notna(x) and x else None
    )
    
    return df

def main():
    st.title("🏠 Maracaibo Real Estate Dashboard")
    
    # Load data
    df = load_data()
    
    if len(df) == 0:
        st.error("No listings found in database")
        return
    
    # Calculate opportunity scores
    # First, get trend line parameters from sales data
    sales_with_data = df[
        ~df['is_rental'] & 
        df['price_usd'].notna() & 
        df['sqm'].notna() & 
        (df['sqm'] > 0) &
        (df['price_usd'] >= 5000)
    ]
    
    if len(sales_with_data) > 2:
        trend_slope, trend_intercept = np.polyfit(sales_with_data['sqm'], sales_with_data['price_usd'], 1)
        median_psqm = sales_with_data['price_per_sqm'].median()
        
        # Calculate scores
        scores_and_reasons = df.apply(
            lambda row: calculate_opportunity_score(row, median_psqm, trend_slope, trend_intercept), 
            axis=1
        )
        df['opportunity_score'] = scores_and_reasons.apply(lambda x: x[0])
        df['score_reasons'] = scores_and_reasons.apply(lambda x: x[1])
    else:
        df['opportunity_score'] = 0
        df['score_reasons'] = [[]] * len(df)
    
    # Sidebar filters
    st.sidebar.header("🔍 Filtros")
    
    # Property type filter
    property_types = ['Todos'] + sorted(df['property_type'].dropna().unique().tolist())
    selected_type = st.sidebar.selectbox("Tipo de propiedad", property_types)
    
    # Sector filter
    sectors = ['Todos', '⭐ Zonas Preferidas'] + sorted(df['sector'].dropna().unique().tolist())
    selected_sector = st.sidebar.selectbox("Sector", sectors)
    
    # Price range
    sales_df = df[~df['is_rental'] & df['price_usd'].notna()]
    if len(sales_df) > 0:
        min_price = int(sales_df['price_usd'].min())
        max_price = int(sales_df['price_usd'].max())
        price_range = st.sidebar.slider(
            "Rango de precio (USD)",
            min_price, max_price, (min_price, max_price),
            step=5000, format="$%d"
        )
    else:
        price_range = (0, 10000000)
    
    # Bedrooms filter
    min_beds = st.sidebar.number_input("Mínimo habitaciones", 0, 10, 0)
    
    # Show only preferred sectors
    show_preferred_only = st.sidebar.checkbox("Solo zonas preferidas", False)
    
    # Apply filters
    filtered = df.copy()
    
    # Exclude rentals by default
    filtered = filtered[~filtered['is_rental']]
    
    if selected_type != 'Todos':
        filtered = filtered[filtered['property_type'] == selected_type]
    
    if selected_sector == '⭐ Zonas Preferidas':
        filtered = filtered[filtered['is_preferred']]
    elif selected_sector != 'Todos':
        filtered = filtered[filtered['sector'] == selected_sector]
    
    if show_preferred_only:
        filtered = filtered[filtered['is_preferred']]
    
    filtered = filtered[
        (filtered['price_usd'].isna()) | 
        ((filtered['price_usd'] >= price_range[0]) & (filtered['price_usd'] <= price_range[1]))
    ]
    
    if min_beds > 0:
        filtered = filtered[(filtered['bedrooms'].isna()) | (filtered['bedrooms'] >= min_beds)]
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total Listings", len(filtered))
    
    with col2:
        preferred_count = len(filtered[filtered['is_preferred']])
        st.metric("⭐ En Zonas Preferidas", preferred_count)
    
    with col3:
        with_price = filtered[filtered['price_usd'].notna()]
        if len(with_price) > 0:
            avg_price = with_price['price_usd'].mean()
            st.metric("💰 Precio Promedio", f"${avg_price:,.0f}")
        else:
            st.metric("💰 Precio Promedio", "N/A")
    
    with col4:
        with_sqm = filtered[filtered['price_per_sqm'].notna()]
        if len(with_sqm) > 0:
            avg_psqm = with_sqm['price_per_sqm'].mean()
            st.metric("📐 Promedio $/m²", f"${avg_psqm:,.0f}")
        else:
            st.metric("📐 Promedio $/m²", "N/A")
    
    # Charts
    st.header("📈 Análisis")
    
    # Scatter plot: Price vs Size (full width, larger)
    scatter_data = filtered[
        filtered['price_usd'].notna() & 
        filtered['sqm'].notna() & 
        (filtered['sqm'] > 0) & 
        (filtered['sqm'] < 2000) &
        (filtered['price_usd'] >= 5000)
    ].copy()
    
    if len(scatter_data) > 0:
        # Create custom hover text with all details
        scatter_data['hover_text'] = scatter_data.apply(
            lambda r: f"<b>{r['property_type'].title()}</b><br>" +
                      f"📍 {r['sector']}<br>" +
                      f"💰 ${r['price_usd']:,.0f}<br>" +
                      f"📐 {r['sqm']:.0f}m² (${r['price_per_sqm']:,.0f}/m²)<br>" +
                      f"🛏️ {int(r['bedrooms']) if pd.notna(r['bedrooms']) else '?'} hab<br>" +
                      f"<br><i>Click para ver →</i>",
            axis=1
        )
        
        # Mark preferred sectors
        scatter_data['marker_symbol'] = scatter_data['is_preferred'].apply(lambda x: 'star' if x else 'circle')
        
        fig = px.scatter(
            scatter_data,
            x='sqm',
            y='price_usd',
            color='property_type',
            symbol='is_preferred',
            custom_data=['url', 'sector', 'bedrooms', 'price_per_sqm', 'author'],
            hover_name='property_type',
            hover_data={
                'sqm': True,
                'price_usd': ':$,.0f',
                'sector': True,
                'bedrooms': True,
                'price_per_sqm': ':$,.0f',
                'is_preferred': False,
                'property_type': False
            },
            title="💰 Precio vs Tamaño (⭐ = Zona Preferida) — Click en un punto para ver detalles",
            labels={'sqm': 'Tamaño (m²)', 'price_usd': 'Precio (USD)', 'property_type': 'Tipo', 'is_preferred': 'Preferida'}
        )
        
        fig.update_traces(marker=dict(size=14, line=dict(width=1, color='white')))
        
        # Add trend line
        z = np.polyfit(scatter_data['sqm'], scatter_data['price_usd'], 1)
        x_line = np.linspace(scatter_data['sqm'].min(), scatter_data['sqm'].max(), 100)
        y_line = z[0] * x_line + z[1]
        
        fig.add_trace(go.Scatter(
            x=x_line,
            y=y_line,
            mode='lines',
            name=f'Tendencia (${z[0]:,.0f}/m²)',
            line=dict(color='black', width=2, dash='dash'),
            hoverinfo='skip'
        ))
        
        fig.update_layout(
            height=550,
            hovermode='closest',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        # Reset index for proper point mapping
        scatter_data = scatter_data.reset_index(drop=True)
        
        # Display chart with click events
        selected_point = st.plotly_chart(fig, use_container_width=True, on_select="rerun", key="scatter")
        
        # Handle click selection
        if selected_point and selected_point.selection and selected_point.selection.points:
            point = selected_point.selection.points[0]
            # Use x,y coordinates to find the matching row
            click_x = point.get('x')
            click_y = point.get('y')
            
            # Find row matching these coordinates
            matching = scatter_data[
                (scatter_data['sqm'] == click_x) & 
                (scatter_data['price_usd'] == click_y)
            ]
            
            if len(matching) > 0:
                clicked_row = matching.iloc[0]
            else:
                # Fallback to point_index
                idx = point.get('point_index', 0)
                clicked_row = scatter_data.iloc[idx] if idx < len(scatter_data) else None
            
            if clicked_row is not None:
                st.success(f"**Seleccionado:** {clicked_row['property_type'].title()} en {clicked_row['sector']}")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Precio", f"${clicked_row['price_usd']:,.0f}")
                with col2:
                    st.metric("Tamaño", f"{clicked_row['sqm']:.0f}m²")
                with col3:
                    st.metric("$/m²", f"${clicked_row['price_per_sqm']:,.0f}")
                
                st.markdown(f"**Realtor:** {clicked_row.get('author', 'N/A')}")
                st.markdown(f"🔗 **[Abrir listado]({clicked_row['url']})**")
    else:
        st.info("No hay datos suficientes para el gráfico")
    
    # Second row of charts
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        # Bar chart: Price per sqm by sector
        sector_data = filtered[
            filtered['price_per_sqm'].notna() & 
            (filtered['price_per_sqm'] > 10) &
            (filtered['price_per_sqm'] < 5000)
        ].copy()
        
        if len(sector_data) > 0:
            sector_avg = sector_data.groupby('sector').agg({
                'price_per_sqm': 'median',
                'price_usd': 'count'
            }).reset_index()
            sector_avg.columns = ['sector', 'median_price_sqm', 'count']
            sector_avg = sector_avg[sector_avg['count'] >= 1].sort_values('median_price_sqm')
            
            # Mark preferred sectors
            sector_avg['is_preferred'] = sector_avg['sector'].apply(lambda x: x in PREFERRED_SECTORS)
            
            fig = px.bar(
                sector_avg.tail(15),
                x='median_price_sqm',
                y='sector',
                color='is_preferred',
                color_discrete_map={True: '#27ae60', False: '#e74c3c'},
                orientation='h',
                title="📍 Precio/m² por Sector (verde = preferido)",
                labels={'median_price_sqm': '$/m² (mediana)', 'sector': 'Sector'},
                hover_data=['count']
            )
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos suficientes para el gráfico")
    
    with chart_col2:
        # Box plot: Price per sqm by property type
        box_data = filtered[
            filtered['price_per_sqm'].notna() & 
            (filtered['price_per_sqm'] > 10) &
            (filtered['price_per_sqm'] < 3000) &
            filtered['property_type'].isin(['apartamento', 'casa', 'townhouse'])
        ].copy()
        
        if len(box_data) > 0:
            fig = px.box(
                box_data,
                x='property_type',
                y='price_per_sqm',
                color='property_type',
                title="📊 Distribución $/m² por Tipo",
                labels={'price_per_sqm': '$/m²', 'property_type': 'Tipo'}
            )
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos suficientes para el gráfico")
    
    # Listings table
    st.header("🏘️ Propiedades")
    
    # Search bar
    search_query = st.text_input("🔍 Buscar", placeholder="Buscar por sector, descripción, realtor...")
    
    # Apply search filter
    search_filtered = filtered.copy()
    if search_query:
        query_lower = search_query.lower()
        search_filtered = filtered[
            filtered['sector'].str.lower().str.contains(query_lower, na=False) |
            filtered['text'].str.lower().str.contains(query_lower, na=False) |
            filtered['author'].str.lower().str.contains(query_lower, na=False) |
            filtered['property_type'].str.lower().str.contains(query_lower, na=False) |
            filtered['location'].str.lower().str.contains(query_lower, na=False)
        ]
        st.caption(f"Mostrando {len(search_filtered)} de {len(filtered)} propiedades")
    
    # Prepare display dataframe - keep numeric values for proper sorting
    display_cols = ['opportunity_score', 'property_type', 'price_usd', 'sqm', 'bedrooms', 'sector', 'is_preferred', 'days_on_market', 'author', 'text', 'url']
    display_df = search_filtered[display_cols].copy()
    
    # Only format non-numeric columns
    display_df['is_preferred'] = display_df['is_preferred'].apply(lambda x: "⭐" if x else "")
    display_df['author'] = display_df['author'].fillna('-')
    # Truncate description to 60 chars
    display_df['text'] = display_df['text'].apply(lambda x: (str(x)[:60] + "...") if pd.notna(x) and len(str(x)) > 60 else (x if pd.notna(x) else "-"))
    
    # Rename columns for display
    display_df.columns = ['Score', 'Tipo', 'Precio', 'Tamaño', 'Hab.', 'Sector', '⭐', 'Días', 'Realtor', 'Descripción', 'URL']
    
    # Sort by score descending
    display_df = display_df.sort_values('Score', ascending=False)
    
    st.dataframe(
        display_df,
        column_config={
            "Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%d"),
            "Precio": st.column_config.NumberColumn("Precio", format="$%,.0f"),
            "Tamaño": st.column_config.NumberColumn("Tamaño", format="%,.0f m²"),
            "Hab.": st.column_config.NumberColumn("Hab.", format="%d"),
            "Días": st.column_config.NumberColumn("Días", format="%d"),
            "URL": st.column_config.LinkColumn("Link", display_text="Ver →"),
            "Descripción": st.column_config.TextColumn("Descripción", width="medium"),
        },
        hide_index=True,
        use_container_width=True
    )
    
    # Top Opportunities (by score)
    st.header("🎯 Top Oportunidades")
    
    opportunity_data = filtered[
        filtered['price_usd'].notna() & 
        filtered['sqm'].notna() & 
        filtered['price_per_sqm'].notna() &
        (filtered['sqm'] > 30) &
        (filtered['price_usd'] >= 5000) &
        (filtered['opportunity_score'] > 0)
    ].copy()
    
    if len(opportunity_data) > 0:
        # Sort by opportunity score
        top_opps = opportunity_data.nlargest(10, 'opportunity_score')
        
        st.caption("Basado en: precio vs tendencia, zona preferida, días en mercado, $/m² vs mediana")
        
        # Display in 2 columns
        col1, col2 = st.columns(2)
        
        for i, (_, row) in enumerate(top_opps.iterrows()):
            pref_badge = "⭐" if row['is_preferred'] else ""
            score = row['opportunity_score']
            reasons = row['score_reasons']
            reasons_text = " • ".join(reasons[:2]) if reasons else "Buen precio"
            
            # Color based on score
            if score >= 60:
                score_color = "🟢"
            elif score >= 40:
                score_color = "🟡"
            else:
                score_color = "🟠"
            
            days_text = f"📅{int(row['days_on_market'])}d" if pd.notna(row['days_on_market']) else ""
            
            card_content = f"""
<small>{score_color} <b>{score:.0f}</b> | {pref_badge}{row['property_type'].title()} - {row['sector']}</small><br>
<small>💰${row['price_usd']:,.0f} | 📐{row['sqm']:.0f}m² | ${row['price_per_sqm']:,.0f}/m² {days_text}</small><br>
<small>_{reasons_text}_ — <a href="{row['url']}">Ver →</a></small>
"""
            
            with col1 if i % 2 == 0 else col2:
                st.markdown(card_content, unsafe_allow_html=True)
                st.markdown("---")
    else:
        st.info("No hay suficientes datos para detectar oportunidades")
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.caption(f"Total en BD: {len(df)} propiedades")
    st.sidebar.caption("Actualizado cada 5 minutos")
    
    if st.sidebar.button("🔄 Actualizar datos"):
        st.cache_data.clear()
        st.rerun()

if __name__ == "__main__":
    main()
