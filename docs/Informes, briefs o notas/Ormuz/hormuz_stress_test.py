import pandas as pd
from pathlib import Path
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def save_table_as_png(df, filename, title):
    # Premium Color Palette (Institutional Style)
    header_color = '#1f3b64'  # Dark Blue
    row_even_color = '#f8f9fa' # Very Light Grey
    row_odd_color = 'white'
    text_color = '#212529'
    
    # Calculate height dynamically with more breathing room
    calculated_height = 100 + (len(df) * 45)
    
    # Determine alignment for each column (Center for numbers, Left for names)
    alignments = ['left'] + ['center'] * (len(df.columns) - 1)
    
    fig = go.Figure(data=[go.Table(
        columnorder=list(range(len(df.columns))),
        columnwidth=[220] + [130] * (len(df.columns) - 1),
        header=dict(
            values=[f"<b>{col}</b>" for col in df.columns],
            fill_color=header_color,
            align='center',
            font=dict(color='white', size=14, family="Arial"),
            height=40
        ),
        cells=dict(
            values=[df[col] for col in df.columns],
            fill_color=[[row_odd_color, row_even_color] * (len(df) // 2 + 1)],
            align=alignments, # First col left, others centered
            font=dict(color=text_color, size=12, family="Arial"),
            height=35,
            line_color='white'
        ))
    ])
    
    fig.update_layout(
        title={
            'text': f"<b>{title}</b>",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=18, color=header_color)
        },
        margin=dict(l=20, r=20, t=60, b=20),
        width=1000,
        height=calculated_height
    )
    
    fig.write_image(filename, scale=2)

def save_scatter_analysis(hubs_df, exp_df, gulf_countries, country_map, filename):
    # Select key industries
    industries = {
        'Extraction crude petroleum and natural gas': 'Crudo y Gas Natural',
        'Basic chemicals except fertilizers': 'Química Básica',
        'Fertilizers and nitrogen compounds': 'Fertilizantes'
    }
    
    # Hub scores for Gulf countries
    gulf_hubs = hubs_df[hubs_df['country'].isin(gulf_countries)].copy()
    
    # Create subplots
    fig = make_subplots(
        rows=1, cols=3, 
        subplot_titles=[f"<b>{name}</b>" for name in industries.values()],
        horizontal_spacing=0.1
    )
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
    country_colors = {country: colors[i % len(colors)] for i, country in enumerate(gulf_countries)}
    
    for i, (ind_name, label) in enumerate(industries.items()):
        # Calculate Sectoral Export Importance
        ind_data = exp_df[exp_df['industry'] == ind_name]
        sector_imp = ind_data.groupby('exporter')['dep_total'].sum().reset_index()
        sector_imp.columns = ['country', 'sector_importance']
        
        # Merge with hub scores
        merged = pd.merge(gulf_hubs, sector_imp, on='country', how='left').fillna(0)
        
        # Add traces
        for idx, row in merged.iterrows():
            c_name = country_map.get(row['country'], row['country'])
            fig.add_trace(
                go.Scatter(
                    x=[row['global_score']],
                    y=[row['sector_importance']],
                    mode='markers',
                    name=c_name,
                    marker=dict(size=15, color=country_colors[row['country']], line=dict(width=1, color='white')),
                    showlegend=(i == 0) # Only show legend once
                ),
                row=1, col=i+1
            )
        
        fig.update_xaxes(title_text="Global Hub Score (IDC)", row=1, col=i+1, gridcolor='#eee')
        fig.update_yaxes(title_text="Importancia Exportadora", row=1, col=i+1, gridcolor='#eee')

    fig.update_layout(
        title={
            'text': "<b>Producción vs. Centralidad Logística: El Paradigma del Golfo</b>",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'font': dict(size=20, color='#1f3b64')
        },
        template='plotly_white',
        width=1200,
        height=550, # Slightly more height for bottom legend
        margin=dict(l=60, r=40, t=100, b=120),
        legend=dict(
            orientation="h", 
            yanchor="top", 
            y=-0.2, 
            xanchor="center", 
            x=0.5
        )
    )
    
    fig.write_image(filename, scale=2)

def main():
    print("===================================================================")
    print("ANÁLISIS DE ESTRÉS: CIERRE DEL ESTRECHO DE ORMUZ (Base: 2022)")
    print("===================================================================\n")
    
    base_path = Path(r"c:\Users\Usuario\Documents\Github\Seguridad Economica")
    data_path = base_path / "data" / "processed" / "historico"
    output_dir = base_path / "docs" / "Informes, briefs o notas" / "Ormuz"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    country_map = {
        'ARE': 'Emiratos Árabes',
        'SAU': 'Arabia Saudí',
        'OMN': 'Omán',
        'IRN': 'Irán',
        'QAT': 'Qatar',
        'KWT': 'Kuwait',
        'IRQ': 'Irak',
        'BHR': 'Bahréin',
        'PAK': 'Pakistán',
        'PHL': 'Filipinas',
        'ESP': 'España',
        'MMR': 'Myanmar',
        'ETH': 'Etiopía',
        'ERI': 'Eritrea',
        'SOM': 'Somalia',
        'YEM': 'Yemen',
        'IND': 'India',
        'CHN': 'China',
        'BGD': 'Bangladesh',
        'LKA': 'Sri Lanka',
        'VNM': 'Vietnam',
        'THA': 'Tailandia',
        'MYS': 'Malasia',
        'IDN': 'Indonesia',
        'SGP': 'Singapur'
    }
    
    gulf_countries = ['IRN', 'SAU', 'ARE', 'QAT', 'KWT', 'IRQ', 'OMN', 'BHR']
    
    try:
        exp_df = pd.read_parquet(data_path / "explorer_2022.parquet")
        hubs_df = pd.read_parquet(data_path / "hubs_2022.parquet")
    except Exception as e:
        print(f"Error cargando los datos: {e}")
        return
        
    # --- FIGURA 1: SCATTER HUB VS PRODUCER ---
    try:
        save_scatter_analysis(hubs_df, exp_df, gulf_countries, country_map, output_dir / "fig_1_hub_vs_producer.png")
        print("[OK] Figura 1 (Scatter Hub) exportada.")
    except Exception as e:
        print(f"Error Figura 1: {e}")

    # --- TABLA 1: HUBS ---
    try:
        hubs_gulf = hubs_df[hubs_df['country'].isin(gulf_countries)][['country', 'global_score', 'global_rank']].sort_values('global_score', ascending=False)
        hubs_gulf['country'] = hubs_gulf['country'].map(country_map).fillna(hubs_gulf['country'])
        hubs_gulf.columns = ['Economía', 'Global Hub Score (IDC)', 'Rango Mundial']
        hubs_gulf['Global Hub Score (IDC)'] = hubs_gulf['Global Hub Score (IDC)'].round(2)
        save_table_as_png(hubs_gulf, output_dir / "tabla_1_hubs.png", "Tabla 1: Indicadores de Centralidad Regional")
        print("[OK] Tabla 1 (Hubs) exportada.")
    except Exception as e:
        print(f"Error Tabla 1: {e}")

    # --- TABLA 2: ESPAÑA ---
    esp_exp = exp_df[exp_df['importer'] == 'ESP'].copy()
    esp_gulf = esp_exp[esp_exp['exporter'].isin(gulf_countries)].copy()
    block_deps = esp_gulf.groupby(['industry'])[['dep_total', 'dep_direct', 'dep_indirect']].sum().reset_index()
    block_deps = block_deps.sort_values(by='dep_total', ascending=False).head(10)
    block_deps.columns = ['Industria', 'Vulnerabilidad Total (IDC)', 'Riesgo Directo', 'Riesgo Oculto (Indirecto)']
    block_deps = block_deps.round(2)
    save_table_as_png(block_deps, output_dir / "tabla_2_espana.png", "Tabla 2: Exposición Sectorial de España al Bloque del Golfo")
    print("[OK] Tabla 2 (España) exportada.")

    # --- TABLA 3: GLOBAL ---
    crude_industry_name = "Extraction crude petroleum and natural gas"
    global_crude = exp_df[exp_df['industry'] == crude_industry_name]
    global_crude_gulf = global_crude[global_crude['exporter'].isin(gulf_countries)]
    global_crude_deps = global_crude_gulf.groupby('importer')[['dep_total', 'dep_direct', 'dep_indirect']].sum().reset_index()
    global_crude_deps = global_crude_deps.sort_values(by='dep_total', ascending=False).head(10)
    global_crude_deps['importer'] = global_crude_deps['importer'].map(country_map).fillna(global_crude_deps['importer'])
    global_crude_deps.columns = ['Economía', 'Dependencia Total (IDC)', 'Riesgo Directo', 'Vulnerabilidad Indirecta']
    global_crude_deps = global_crude_deps.round(2)
    save_table_as_png(global_crude_deps, output_dir / "tabla_3_global.png", "Tabla 3: Países con Mayor Dependencia Sistémica (Crudo)")
    print("[OK] Tabla 3 (Global) exportada.")

if __name__ == "__main__":
    main()
