import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from src.limesurvey import get_responses_df
from src.config import CONFIG_WEIGHTS, MAP_SECTOR, MAP_NUM_EMP, MM_LEVELS, LIKERT_LABELS
from src.engine import calculate_maturity, get_level_label

COLOR_NAVY = "#102F60"     # Primary
COLOR_CORAL = "#F37B6E"    # Mensch
COLOR_PURPLE = "#A773B6"   # Resilienz
COLOR_TEAL = "#188580"     # Nachhaltigkeit
COLOR_GRAY = "#B2B2B2"     # Neutral
COLOR_BLACK = "#000000"    # Text
CORP_SCALE = [COLOR_GRAY, COLOR_NAVY, COLOR_TEAL, COLOR_PURPLE, COLOR_CORAL]

DIMENSION_COLORS = {
    "Mensch": COLOR_CORAL,
    "Resilienz": COLOR_PURPLE,
    "Nachhaltigkeit": COLOR_TEAL,
    "Default": COLOR_NAVY
}

market_cols = {
    "marktPosition[erfolg1]": "Erfolg: Letztes Jahr",
    "marktPosition[erfolg2]": "Erfolg: Aktuelles Jahr",
    "marktPosition[mpA1]": "Position: Aktuell",
    "marktPosition[mpA2]": "Position: Kurzfristig",
    "marktPosition[mpA3]": "Position: Mittelfristig",
    "marktPosition[mpA4]": "Position: Langfristig"
}


# --- 2. FUNCTIONS ---
def get_label_by_score(score):
    for label, (min_val, max_val) in MM_LEVELS:
        if min_val <= score < max_val: return label
    return "Senior" if score >= 4.0 else "Außenseiter"


def process_sectors(df):
    def get_sector_name(row):
        if str(row.get('branche', '')).strip() in ['-oth-', 'bran9']:
            other_val = row.get('branche[other]', '')
            return str(other_val).strip() if pd.notna(other_val) and str(
                other_val).strip() != '' else "Sonstiges (Nicht spezifiziert)"
        return MAP_SECTOR.get(row['branche'], row['branche'])

    df['Sector'] = df.apply(get_sector_name, axis=1)
    return df


def reset_benchmark():
    st.session_state.view_mode = 'general'
    st.session_state.id_input_val = ""
    st.query_params.clear()
    st.rerun()

def local_css(file_name):
    try:
        with open(file_name, encoding="utf-8") as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"File not found: {file_name}")
    except Exception as e:
        st.error(f"Fail to load CSS: {e}")

# --- 3. CARGA DE DATOS ---
@st.cache_data(ttl=600)
def load_from_limesurvey():
    try:
        s = st.secrets["lime_survey"]
        raw = get_responses_df(s["url"], s["username"], s["password"], s["survey_id"])
        return calculate_maturity(raw) if raw is not None else None
    except Exception as e:
        st.error(f"Verbindungsfehler: {e}")
        return None


# --- 4. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="I5.0 Transformation Check", layout="wide")
local_css("assets/css/style.css")

# --- 5. LÓGICA PRINCIPAL Y FLUJO ---
st.sidebar.header("Datenquelle")
data_source = st.sidebar.radio("Quelle auswählen:", ["LimeSurvey API (Live)", "CSV-Datei hochladen"])

if 'df' not in st.session_state: st.session_state['df'] = None

if data_source == "LimeSurvey API (Live)":
    if st.sidebar.button("Daten jetzt aktualisieren") or st.session_state['df'] is None:
        with st.spinner("Lade Daten..."):
            st.session_state['df'] = load_from_limesurvey()
else:
    uploaded_file = st.sidebar.file_uploader("CSV-Datei auswählen", type=["csv"])
    if uploaded_file:
        raw = pd.read_csv(uploaded_file, sep=None, engine='python')
        st.session_state['df'] = calculate_maturity(raw)

# --- 6. PROCESAMIENTO FINAL Y SINCRONIZACIÓN ---
df_full = st.session_state['df']

if df_full is not None:
    df_full = process_sectors(df_full)
    df_full['Size'] = df_full['anzMA'].map(MAP_NUM_EMP)
    df_full['PLZ_Group'] = df_full['plz'].astype(str).str[:2]

    # Sincronización URL
    params = st.query_params
    url_id = params.get("id")

    if url_id and str(url_id) not in df_full['id'].astype(str).values:
        with st.spinner('Sincronizando ID...'):
            st.cache_data.clear()
            st.session_state['df'] = load_from_limesurvey()
            st.rerun()

    if url_id and url_id.isdigit():
        st.session_state.id_input_val = url_id
        st.session_state.current_tab = "Benchmark"
        st.session_state.view_mode = 'individual'

    # AQUÍ COMIENZA TU DASHBOARD (gráficos, tablas, etc.)
else:
    st.info("Bitte laden Sie Daten, um fortzufahren.")


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
    filter_sectors = st.sidebar.multiselect("Branchen auswählen", options=list_real_sectors, default=[])
    filter_sizes = st.sidebar.multiselect("Unternehmensgrößen auswählen", options=list_sizes, default=[])
    filter_regions = st.sidebar.multiselect("Regionen (PLZ Zone) auswählen", options=list_real_regions, default=[])

    # 3. Lógica de filtrado acumulativo
    df_filtered = df_full.copy()

    if filter_sectors:
        df_filtered = df_filtered[df_filtered['Sector'].isin(filter_sectors)]

    if filter_sizes:
        df_filtered = df_filtered[df_filtered['Size'].isin(filter_sizes)]

    if filter_regions:
        df_filtered = df_filtered[df_filtered['PLZ_Group'].isin(filter_regions)]

    # Mostrar un aviso si el filtro deja el dashboard vacío
    if df_filtered.empty:
        st.warning("Keine Daten für diese Auswahl gefunden.")

# --- HEADER CON LOGO Y TÍTULO ---
col_title, col_logo = st.columns([4,2 ])
with col_logo:
    # Ajusta el nombre de tu archivo de imagen
    st.image("assets/img/st5.png", width=240)

with col_title:
    st.markdown('<h1 class="main-title">I5.0 Transformations-Check Standortbestimmung</h1>', unsafe_allow_html=True)

# --- KEY METRICS  ---
if df_filtered.empty:
    st.markdown(f"""
        <div style="background-color: #f8f9fa; padding: 30px; border-radius: 12px; border: 1px solid #2d2e83; text-align: center;">
            <h3 style="color: #2d2e83; margin-top: 0;"> Keine passenden Daten gefunden</h3>
            <p style="color: #555;">Für die aktuelle Kombination existieren keine Einträge:</p>
            <ul style="list-style: none; padding: 0; color: #2d2e83; font-weight: bold;">
                <li>Branche: {filter_sectors}</li>
                <li>Größe: {filter_sizes}</li>
                <li>Region: {filter_regions}</li>
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
if 'current_tab' not in st.session_state:
    st.session_state.current_tab = "Allgemeine Analyse"

nav = st.radio("Navigation", ["Allgemeine Analyse", "Benchmark"],
               index=["Allgemeine Analyse", "Benchmark"].index(st.session_state.current_tab),
               horizontal=True, key="nav_radio", label_visibility="collapsed")

st.session_state.current_tab = nav

if nav == "Allgemeine Analyse":
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

        # 1. Crear el gráfico con range_x fijo en [1, 5]
        fig_avg = px.bar(avg_dims,
                         x='Mean',
                         y='Name',
                         orientation='h',
                         text_auto='.2f',
                         color='Mean',
                         color_continuous_scale=CORP_SCALE,
                         range_color=[1, 5])

        # 2. Configurar el eje X y añadir líneas guía
        fig_avg.update_layout(
            xaxis=dict(range=[1, 5], dtick=1),  # Fuerza el eje de 1 a 5 con marcas cada 1
            showlegend=False
        )

        # 3. Añadir líneas verticales para los niveles de MM_LEVELS (opcional pero recomendado)
        for val in [2.0, 3.0, 4.0]:
            fig_avg.add_vline(x=val, line_dash="dash", line_color="#B2B2B2", line_width=1)

        # 4. (Opcional) Si quieres que el usuario sepa qué es 4 o 5, puedes añadir anotaciones sutiles arriba
        fig_avg.add_annotation(x=4.5, y=1.1, text="Senior", showarrow=False, xref="x", yref="paper",
                               font=dict(color="#B2B2B2"))
        fig_avg.add_annotation(x=1.5, y=1.1, text="Außenseiter", showarrow=False, xref="x", yref="paper",
                               font=dict(color="#B2B2B2"))

        st.plotly_chart(fig_avg, use_container_width=True)

elif nav == "Benchmark":
    score_cols = [f"Score_{dim}" for dim in CONFIG_WEIGHTS.keys()]
    dim_names = [d["name_de"] for d in CONFIG_WEIGHTS.values()]

    # 1. Avisar si hay filtros activos
    if len(filter_sectors) > 0 or len(filter_sizes) > 0 or len(filter_regions) > 0:
        st.info(f"💡 Benchmark-Ansicht: Gefiltert auf {len(df_filtered)} Unternehmen.")

    if df_filtered.empty and 'id_input_val' not in st.session_state:
        st.warning("Keine Daten mit den aktuellen Filtern verfügbar.")
    else:
        # --- Lógica de Estado ---
        id_val = st.session_state.get("id_input_val", "")
        input_id = st.text_input("Geben Sie Ihre Antwort-ID ein:", value=id_val)

        if input_id != id_val:
            st.session_state.id_input_val = input_id
            st.rerun()

        # Determinamos los datos principales
        if id_val and id_val.isdigit():
            data = df_full[df_full['id'] == int(id_val)]
            if not data.empty:
                st.session_state.view_mode = 'individual'
                serie_a_mostrar = data.iloc[0]
                r_principal = serie_a_mostrar[score_cols].values.flatten().tolist()
                score_actual = serie_a_mostrar['Maturity_Score']
                nombre_principal = 'Ihr Ergebnis'
                if st.button("Zurück zum allgemeinen Benchmark", on_click=reset_benchmark): st.rerun()
            else:
                st.error("ID nicht gefunden.")
                st.session_state.view_mode = 'general'
                r_principal = df_filtered[dim_cols].mean().tolist()
                score_actual = df_filtered['Maturity_Score'].mean()
                nombre_principal = 'Ø Gruppe (Filter)'
                serie_a_mostrar = None
        else:
            st.session_state.view_mode = 'general'
            r_principal = df_filtered[dim_cols].mean().tolist()
            score_actual = df_filtered['Maturity_Score'].mean()
            nombre_principal = 'Ø Gruppe (Filter)'
            serie_a_mostrar = None

        # --- KPI Metrics ---
        col1, col2, col3 = st.columns(3)
        col1.metric("Ø Maturity Score", f"{score_actual:.2f}")
        col2.metric("Abstand zum Ziel", f"{(5.0 - score_actual):.2f}")
        col3.metric("Level", get_label_by_score(score_actual))

        # --- RADAR (Simplificado) ---
        fig_radar = go.Figure()

        # 1. Trazo Principal (Tu resultado o promedio general del filtro)
        fig_radar.add_trace(go.Scatterpolar(
            r=r_principal + [r_principal[0]],
            theta=dim_names + [dim_names[0]],
            fill='toself', fillcolor='rgba(243, 123, 110, 0.2)',
            name=nombre_principal, line=dict(color=COLOR_CORAL, width=3)
        ))

        # 2. Referencia: Promedio del grupo (Sidebar Filter)
        group_means = df_filtered[dim_cols].mean().tolist()
        fig_radar.add_trace(go.Scatterpolar(
            r=group_means + [group_means[0]],
            theta=dim_names + [dim_names[0]],
            name="Ø Gruppe (Filter)",
            line=dict(dash='dash', color=COLOR_NAVY, width=2.5)
        ))

        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[1, 5])),
                                legend=dict(orientation="h", y=-0.2), height=500)
        st.plotly_chart(fig_radar, use_container_width=True)

        # --- STÄRKEN & SCHWÄCHEN (Solo si es individual) ---
        if st.session_state.view_mode == 'individual':
            st.divider()
            col_s, col_w = st.columns(2)
            dim_scores = sorted(zip(dim_names, r_principal), key=lambda x: x[1], reverse=True)
            with col_s:
                st.success("Top 3 Stärken")
                for name, val in dim_scores[:3]: st.write(f"✅ **{name}**: {val:.2f}")
            with col_w:
                st.error("Top 3 Handlungsfelder")
                for name, val in dim_scores[-3:]: st.write(f"⚠️ **{name}**: {val:.2f}")

        # --- TABLA DETALLADA ---
        st.divider()
        st.subheader("🚦 Item-Performance")
        dim_key = st.selectbox("Dimension auswählen:", list(CONFIG_WEIGHTS.keys()),
                               format_func=lambda x: CONFIG_WEIGHTS[x]['name_de'])

        items_list = []
        for i_id, i_info in CONFIG_WEIGHTS[dim_key]['items'].items():
            val_grupo = float(df_filtered[i_info['ls_code']].mean())
            row = {"Item": i_info['name_de'], "Ø Gruppe": val_grupo}
            if st.session_state.view_mode == 'individual':
                row["Dein Wert"] = float(serie_a_mostrar[i_info['ls_code']])
            items_list.append(row)

        df_p = pd.DataFrame(items_list)
        format_dict = {"Ø Gruppe": "{:.2f}"}
        if "Dein Wert" in df_p.columns: format_dict["Dein Wert"] = "{:.2f}"

        st.dataframe(
            df_p.style.apply(
                lambda row: ['background-color: #d4edda' if (row['Dein Wert'] if 'Dein Wert' in row else row['Ø Gruppe']) >= 4
                             else 'background-color: #f8d7da'] * len(row), axis=1
            ).format(format_dict), use_container_width=True
        )
        # --- BLOQUE: MERCADO Y ÉXITO ---
        st.divider()
        st.subheader("🎯 Markt-Einschätzung & Erfolg")
        market_data = []
        for col, label in market_cols.items():
            # El promedio del grupo siempre está disponible (si hay datos)
            val_grupo = float(df_filtered[col].mean())

            row = {"Frage": label, "Ø Gruppe (Filter)": val_grupo}

            # Si estamos en modo individual, añadimos la columna personalizada
            if st.session_state.view_mode == 'individual' and serie_a_mostrar is not None:
                val_indiv = float(serie_a_mostrar[col])
                row["Deine Antwort"] = val_indiv
                row["Differenz"] = val_indiv - val_grupo

            market_data.append(row)

        df_market = pd.DataFrame(market_data)

        # Mostrar tabla con formato condicional solo si tenemos los datos necesarios
        def highlight_max(s):
            return ['background-color: #d1e7dd' if v >= 4 else '' for v in s]

        st.dataframe(
            df_market.style.format({"Ø Gruppe (Filter)": "{:.1f}", "Deine Antwort": "{:.1f}", "Differenz": "{:+.1f}"})
            .apply(highlight_max, subset=["Ø Gruppe (Filter)"]),
            use_container_width=True
        )


#tab_gen, tab_ind  = st.tabs(["Allgemeine Analyse", "Benchmark"])

# # ==========================================
# # tab 2: BENCHMARK GRUPAL (Antes Individual)
# # ==========================================
# with tab_ind:
#     # 1. DEFINICIONES SIEMPRE PRESENTES (Fuera de cualquier 'if')
#     # Esto asegura que score_cols siempre exista para el gráfico
#
#
# # ==========================================
# # TAB 2: GENERAL
# # ==========================================
# with tab_gen:
#