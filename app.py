import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from src.config import CONFIG_WEIGHTS, MAP_SECTOR, MAP_NUM_EMP, MM_LEVELS, LIKERT_LABELS
from src.engine import calculate_maturity, get_level_label
from src.generator import generate_dummy_data

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

st.set_page_config(page_title="I5.0 Transformation Check", layout="wide")
local_css("style.css")

# --- colores de marca ---
COLOR_AZUL = "#2d2e83"
COLOR_VERDE = "#a8d43a"
COLOR_TURQUESA = "#69c0ac"
COLOR_CELESTE = "#1b85c2"
COLOR_GRIS = "#b2b2b2"

# escala
CORP_SCALE =  [COLOR_GRIS, COLOR_AZUL, COLOR_CELESTE, COLOR_TURQUESA, COLOR_VERDE]

# --- LOAD DATA ---
st.sidebar.header("Data Source")
data_source = st.sidebar.radio("Datenquelle auswählen:", ["Sample Data", "Upload CSV"])

df_full = None

def process_sectors(df):
    def get_sector_name(row):

        if str(row.get('branche', '')).strip() in ['-oth-', 'bran9']:
            other_val = row.get('branche[other]', '')
            if pd.notna(other_val) and str(other_val).strip() != '':
                return str(other_val).strip()
            return "Sonstiges (Nicht spezifiziert)"
        return MAP_SECTOR.get(row['branche'], row['branche'])

    df['Sector'] = df.apply(get_sector_name, axis=1)
    return df

if data_source == "Sample Data":
    num_samples = st.sidebar.number_input("Anzahl der Stichproben", 10, 5000, 200)
    if st.sidebar.button("Daten generieren") or 'df' not in st.session_state:
        raw = generate_dummy_data(num_samples)
        df_full = calculate_maturity(raw)
        st.session_state['df'] = df_full
    else:
        df_full = st.session_state['df']
else:
    uploaded_file = st.sidebar.file_uploader("CSV-Datei hochladen", type=["csv"])
    if uploaded_file is not None:
        raw = pd.read_csv(uploaded_file)
        df_full = calculate_maturity(raw)
        st.session_state['df'] = df_full
    elif 'df' in st.session_state:
        df_full = st.session_state['df']
    else:
        st.info("Bitte laden Sie eine Datei hoch oder nutzen Sie Sample Data.")
        st.stop()



# --- PREPARE DATA FOR VISUALIZATION ---
if df_full is not None:

    df_full = process_sectors(df_full)


    df_full['Size'] = df_full['anzMA'].map(MAP_NUM_EMP)
    df_full['PLZ_Group'] = df_full['plz'].astype(str).str[:2]

    dim_cols = [f"Score_dim{i}" for i in range(1, 8)]
    dim_names = [info['name_de'] for info in CONFIG_WEIGHTS.values()]

    # --- SIDEBAR: GLOBALER FILTER ---
    st.sidebar.divider()
    st.sidebar.header("Globaler Filter")

    # 1. Obtener listas únicas para los selectores
    list_real_sectors = sorted(df_full['Sector'].unique().tolist())
    list_real_regions = sorted(df_full['PLZ_Group'].unique().tolist())  # Regiones por código postal
    list_sizes = list(MAP_NUM_EMP.values())

    # 2. Widgets de la Sidebar
    filter_sector = st.sidebar.selectbox("Branche", ["Alle"] + list_real_sectors)
    filter_size = st.sidebar.selectbox("Unternehmensgröße", ["Alle"] + list_sizes)
    filter_region = st.sidebar.selectbox("Region (PLZ Zone)", ["Alle"] + list_real_regions)


    # 3. Lógica de filtrado acumulativo
    df_filtered = df_full.copy()

    if filter_sector != "Alle":
        df_filtered = df_filtered[df_filtered['Sector'] == filter_sector]

    if filter_size != "Alle":
        df_filtered = df_filtered[df_filtered['Size'] == filter_size]

    if filter_region != "Alle":
        df_filtered = df_filtered[df_filtered['PLZ_Group'] == filter_region]

st.title("I5.0 Transformations-Check Standortbestimmung")
# --- KEY METRICS  ---
if df_filtered.empty:
    st.markdown(f"""
        <div style="background-color: #f8f9fa; padding: 30px; border-radius: 12px; border: 1px solid #2d2e83; text-align: center;">
            <h3 style="color: #2d2e83; margin-top: 0;"> Keine passenden Daten gefunden</h3>
            <p style="color: #555;">Für die aktuelle Kombination existieren keine Einträge:</p>
            <ul style="list-style: none; padding: 0; color: #2d2e83; font-weight: bold;">
                <li>Branche: {filter_sector}</li>
                <li>Größe: {filter_size}</li>
                <li>Region: {filter_region}</li>
            </ul>
            <p style="color: #888; font-size: 13px;">Bitte passen Sie die Filter in der Sidebar an.</p>
        </div>
    """, unsafe_allow_html=True)
    st.stop()
else:

    filter_n = len(df_filtered)
    avg_score = df_filtered['Maturity_Score'].mean()
    avg_level = get_level_label(avg_score)

    # highest dimension
    avg_by_dim = df_filtered[dim_cols].mean()
    top_dim_idx = avg_by_dim.argmax()
    top_dim_name = dim_names[top_dim_idx]

    # --- CSS for the cards ---
    st.markdown("""
    <style>
        .metric-card {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 12px;
            border: 1px solid #e6e9ef;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            text-align: center;
            height: 120px; 
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .metric-label { 
            font-size: 13px; 
            color: #555; 
            text-transform: uppercase; 
            font-weight: 600;
            margin-bottom: 8px;
        }
        .metric-value { 
            font-size: 24px; 
            font-weight: bold; 
            color: #004b23; 
        }
        .metric-subtext { 
            font-size: 14px; 
            color: #888; 
            font-weight: 400;
            margin-top: 4px;
        }
        .low-dim { color: #9d0208; } 
    </style>
    """, unsafe_allow_html=True)

    if df_full is not None:
        # Métricas del Filtro (Lo que cambia)
        filter_n = len(df_filtered)
        filter_avg = df_filtered['Maturity_Score'].mean()
        filter_level = get_level_label(filter_avg)

        # Métricas Globales (Lo que se mantiene fijo como referencia)
        global_n = len(df_full)
        global_avg = df_full['Maturity_Score'].mean()

        # Columnas
        c1, c2, c3, c4 = st.columns([1, 1, 2, 2])

        # best dimension
        top_dim_idx = avg_by_dim.argmax()
        top_dim_name = dim_names[top_dim_idx]

        # worst dimension
        low_dim_idx = avg_by_dim.argmin()
        low_dim_name = dim_names[low_dim_idx]


        # columns
        c1, c2, c3, c4 = st.columns([1, 1, 2, 2])

        with c1:
            st.markdown(f'''<div class="metric-card">
                <div class="metric-label">Unternehmen</div>
                <div class="metric-value">{filter_n}</div>
                <div class="metric-subtext">Global: {global_n}</div>
            </div>''', unsafe_allow_html=True)

        with c2:
            # Aquí mostramos el score del filtro y abajo el global
            st.markdown(f'''<div class="metric-card">
                <div class="metric-label">Ø Maturity</div>
                <div class="metric-value">{filter_avg:.2f}</div>
                <div class="metric-subtext">{filter_level} <br> <span style="font-size:11px;">(Global: {global_avg:.2f})</span></div>
            </div>''', unsafe_allow_html=True)

        with c3:
            st.markdown(f'''<div class="metric-card">
                <div class="metric-label">⭐ Stärkste Dimension</div>
                <div class="metric-value" style="font-size: 18px;">{top_dim_name}</div>
            </div>''', unsafe_allow_html=True)

        with c4:
            st.markdown(f'''<div class="metric-card">
                <div class="metric-label">⚠️ Kritische Dimension</div>
                <div class="metric-value low-dim" style="font-size: 18px;">{low_dim_name}</div>
            </div>''', unsafe_allow_html=True)

    st.divider()

# --- TABS ---

tab_ind, tab_gen = st.tabs(["Benchmark", "Allgemeine Analyse"])

# ==========================================
# tab 1: BENCHMARK GRUPAL (Antes Individual)
# ==========================================
with tab_ind:
    if df_filtered.empty:
        st.warning("Keine Daten mit den aktuellen Filtern verfügbar.")
    else:
        # # Título dinámico basado en los filtros de la sidebar
        # st.header("Benchmark")

        # 1. CÁLCULOS DE PROMEDIOS (FILTRADO VS GLOBAL)
        # Promedio del grupo que el usuario filtró en la sidebar
        group_means = df_filtered[dim_cols].mean().tolist()
        group_overall = df_filtered['Maturity_Score'].mean()
        group_level = get_level_label(group_overall)

        # Promedio total de toda la base de datos (Global)
        global_means = df_full[dim_cols].mean().tolist()
        global_overall = df_full['Maturity_Score'].mean()

        col_gauge, col_radar = st.columns([1, 2])

        # # --- GAUGE: PROMEDIO DEL GRUPO FILTRADO ---
        # with col_gauge:
        #     st.subheader("Ø Gesamt-Reifegrad (Filter)")
        #     fig_gauge = go.Figure(go.Indicator(
        #         mode="gauge+number",
        #         value=group_overall,
        #         title={'text': f"Niveau: {group_level}"},
        #         gauge={
        #             'axis': {'range': [1, 5]},
        #             'bar': {'color': COLOR_AZUL},
        #             'steps': [
        #                 {'range': [1, 2], 'color': "#ffadad"},
        #                 {'range': [2, 3], 'color': "#ffd6a5"},
        #                 {'range': [3, 4], 'color': "#fdffb6"},
        #                 {'range': [4, 5], 'color': "#caffbf"}]
        #         }
        #     ))
        #     fig_gauge.update_layout(height=350, margin=dict(t=50, b=0))
        #     st.plotly_chart(fig_gauge, use_container_width=True)

        # --- RADAR: COMPARATIVA GRUPO VS GLOBAL ---
        # with col_radar:
        st.subheader("Dimensions-Benchmark")

        fig_radar = go.Figure()

        # Grupo Filtrado
        fig_radar.add_trace(go.Scatterpolar(
            r=group_means + [group_means[0]],
            theta=dim_names + [dim_names[0]],
            fill='toself',
            name='Aktueller Filter',
            line_color=COLOR_VERDE
        ))

        # Global (Fijo para referencia)
        fig_radar.add_trace(go.Scatterpolar(
            r=global_means + [global_means[0]],
            theta=dim_names + [dim_names[0]],
            name='Gesamtmarkt (Global)',
            line=dict(dash='dash', color=COLOR_AZUL)
        ))

        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[1, 5])),
            legend=dict(orientation="h", y=-0.1),  # Leyenda abajo centrada
            height=500,  # Un poco más alto ya que es el gráfico principal
            margin=dict(t=20, b=20, l=40, r=40)
        )
        st.plotly_chart(fig_radar, use_container_width=True)

        st.divider()
        col_gap, col_ampel = st.columns(2)

        # --- GAP ANALYSIS: DEL GRUPO FILTRADO ---
        with col_gap:
            st.subheader("Ø Gap Analysis (Ziel: 5.0)")
            # Calculamos el gap del promedio del grupo respecto al máximo (5.0)
            group_gaps = [5.0 - m for m in group_means]
            gap_df = pd.DataFrame({'Dimension': dim_names, 'Gap': group_gaps})

            fig_gap = px.bar(
                gap_df, x='Gap', y='Dimension', orientation='h',
                text_auto='.2f',
                color='Gap',
                color_continuous_scale='Reds',  # Rojo indica urgencia del gap
                range_x=[0, 4]
            )
            fig_gap.update_layout(showlegend=False)
            st.plotly_chart(fig_gap, use_container_width=True)

        # --- ITEM-AMPEL: PROMEDIO POR INDICADOR ---
        with col_ampel:
            st.subheader("🚦 Item-Performance")
            dim_key = st.selectbox("Dimension auswählen:", list(CONFIG_WEIGHTS.keys()),
                                   format_func=lambda x: CONFIG_WEIGHTS[x]['name_de'])

            # Extraer códigos de LimeSurvey para los ítems de esta dimensión
            items_config = CONFIG_WEIGHTS[dim_key]['items']
            items_list = []

            for i_id, i_info in items_config.items():
                ls_code = i_info['ls_code']
                # Calculamos el promedio del ítem para el grupo filtrado
                avg_val = df_filtered[ls_code].mean()

                # Lógica de semáforo para el promedio
                status = "🟢" if avg_val >= 4 else "🟡" if avg_val >= 3 else "🔴"

                items_list.append({
                    "Item": i_info['name_de'],
                    "Ø Wert": f"{avg_val:.2f}",
                    "Status": status
                })

            st.table(pd.DataFrame(items_list))

# ==========================================
# TAB 2: GENERAL
# ==========================================
with tab_gen:
    st.header("Panorama der digitalen Reife")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Regionale Verteilung")

        geo_data = df_filtered.groupby('PLZ_Group').agg(
            Avg_Maturity=('Maturity_Score', 'mean'),
            Count=('id', 'count')
        ).reset_index()

        # Treemap
        # values='Count' size square
        # color='Avg_Maturity' color
        fig_tree = px.treemap(
            geo_data,
            path=['PLZ_Group'],
            values='Count',
            color='Avg_Maturity',
            color_continuous_scale='RdYlGn',
            range_color=[1, 5],
            labels={'PLZ_Group': 'PLZ Zone', 'Avg_Maturity': 'Ø Reife', 'Count': 'Anzahl Unternehmen'},
            title="Größe = Anzahl Firmen | Farbe = Reifegrad"
        )
        fig_tree.update_traces(textinfo="label+value")
        st.plotly_chart(fig_tree, use_container_width=True)

    with col2:
        st.subheader("Aufteilung nach Sektoren")
        sector_data = df_filtered.groupby('Sector')['Maturity_Score'].mean().sort_index().reset_index()


        fig_sec = px.bar(
            sector_data,
            x='Maturity_Score',
            y='Sector',
            orientation='h',
            text_auto='.2f',
            color='Maturity_Score',
            color_continuous_scale=CORP_SCALE,
            range_color=[1, 5],
            labels={'Maturity_Score': 'Durchschnittlicher Maturity Score', 'Sector': 'Branche'}
        )

        fig_sec.update_layout(coloraxis_showscale=True)
        st.plotly_chart(fig_sec, use_container_width=True)

    st.divider()
    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Größe vs. Reife")
        fig_box = px.box(df_filtered, x='Size', y='Maturity_Score', color='Size', color_discrete_sequence=CORP_SCALE,
                         category_orders={"Size": ["<= 10", "<= 50", "<= 100", "<= 250", "> 250"]})

        st.plotly_chart(fig_box, use_container_width=True)

    with col4:
        st.subheader("Globaldurchschnitt der Dimensionen")
        avg_dims = df_filtered[dim_cols].mean().reset_index()
        avg_dims.columns = ['Dim', 'Mean']
        avg_dims['Name'] = dim_names
        fig_avg = px.bar(avg_dims, x='Mean', y='Name', orientation='h', text_auto='.2f',
                         color='Mean', color_continuous_scale=CORP_SCALE, range_color=[1, 5],)
                         #color_continuous_scale='GnBu')
        st.plotly_chart(fig_avg, use_container_width=True)