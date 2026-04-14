import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from src.limesurvey import get_responses_df
from src.config import CONFIG_WEIGHTS, MAP_SECTOR, MAP_NUM_EMP, MM_LEVELS, LIKERT_LABELS
from src.engine import calculate_maturity, get_level_label


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
st.sidebar.header("Datenquelle")
# Solo dos opciones: La API en vivo o subir un archivo manual
data_source = st.sidebar.radio("Quelle auswählen:", ["LimeSurvey API (Live)", "CSV-Datei hochladen"])

@st.cache_data(ttl=600) # Cache de 10 minutos para velocidad
def load_from_limesurvey():
    try:
        s = st.secrets["lime_survey"]
        raw = get_responses_df(s["url"], s["username"], s["password"], s["survey_id"])
        if raw is not None:
            # Importante: calculamos la madurez inmediatamente
            return calculate_maturity(raw)
        return None
    except Exception as e:
        st.error(f"Verbindungsfehler zur API: {e}")
        return None

if data_source == "LimeSurvey API (Live)":
    # Botón para forzar actualización manual si hay nuevas respuestas
    if st.sidebar.button("Daten jetzt aktualisieren") or 'df' not in st.session_state:
        with st.spinner("Lade Live-Daten aus LimeSurvey..."):
            df_full = load_from_limesurvey()
            if df_full is not None:
                st.session_state['df'] = df_full
                st.write("Columnas disponibles:", df_full.columns.tolist())
            else:
                st.stop()
    else:
        df_full = st.session_state['df']

else: # Opción: Upload CSV
    uploaded_file = st.sidebar.file_uploader("CSV-Datei auswählen", type=["csv"])
    if uploaded_file is not None:
        # sep=None con engine='python' detecta automáticamente si es coma o punto y coma
        raw = pd.read_csv(uploaded_file, sep=None, engine='python')
        df_full = calculate_maturity(raw)
        st.session_state['df'] = df_full
    elif 'df' in st.session_state:
        df_full = st.session_state['df']
    else:
        st.info("Bitte laden Sie eine CSV-Datei hoch, um fortzufahren.")
        st.stop()

# --- ESTADO DE LA CONEXIÓN (Opcional pero útil) ---
if df_full is not None:
    print(f"DEBUG: ¡Conexión exitosa! Filas cargadas: {len(df_full)}")


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

st.title("I5.0 Transformations-Check Standortbestimmung")
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
        fig_avg = px.bar(avg_dims, x='Mean', y='Name', orientation='h', text_auto='.2f',
                         color='Mean', color_continuous_scale=CORP_SCALE, range_color=[1, 5], )
        # color_continuous_scale='GnBu')
        st.plotly_chart(fig_avg, use_container_width=True)

elif nav == "Benchmark":
    score_cols = [f"Score_{dim}" for dim in CONFIG_WEIGHTS.keys()]
    dim_names = [d["name_de"] for d in CONFIG_WEIGHTS.values()]

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

        # --- RADAR: COMPARATIVA ---
        st.subheader("Benchmark & Analyse")

        # 1. Gestión del estado
        if 'view_mode' not in st.session_state:
            st.session_state.view_mode = 'general'


        def reset_benchmark():
            st.session_state.view_mode = 'general'
            st.session_state.id_input_val = ""
            st.query_params.clear()


        st.text_input("Geben Sie Ihre Antwort-ID ein:", key="id_input_val")
        input_id = st.session_state.id_input_val
        # 2. DETERMINACIÓN DE DATOS (Individual vs Grupo)
        if input_id and input_id.isdigit():
            individual_data = df_full[df_full['id'] == int(input_id)]
            if not individual_data.empty:
                st.session_state.view_mode = 'individual'
                # Datos para Gráficos
                r_principal = individual_data[score_cols].values.flatten().tolist()
                # Datos para GAPs y Tabla
                serie_a_mostrar = individual_data.iloc[0]
                nombre_principal = 'Ihr Ergebnis'
                color_principal = '#2ecc71'
                st.success(f"Individueller Bericht für ID: {input_id}")
                st.button("Zurück zum allgemeinen Benchmark", on_click=reset_benchmark)
            else:
                st.error("ID nicht gefunden.")
                st.session_state.view_mode = 'general'
                r_principal, serie_a_mostrar = group_means, df_filtered[
                    [it['ls_code'] for d in CONFIG_WEIGHTS.values() for it in d['items'].values()]].mean()
                nombre_principal, color_principal = 'Aktueller Filter', COLOR_VERDE
        else:
            st.session_state.view_mode = 'general'
            r_principal = group_means
            serie_a_mostrar = df_filtered[
                [it['ls_code'] for d in CONFIG_WEIGHTS.values() for it in d['items'].values()]].mean()
            nombre_principal, color_principal = 'Aktueller Filter', COLOR_VERDE

        # 3. RADAR (Usa r_principal)
        fig_radar = go.Figure()
        fig_radar.add_trace(
            go.Scatterpolar(r=r_principal + [r_principal[0]], theta=dim_names + [dim_names[0]], fill='toself',
                            name=nombre_principal, line_color=color_principal))
        fig_radar.add_trace(go.Scatterpolar(r=global_means + [global_means[0]], theta=dim_names + [dim_names[0]],
                                            name='Gesamtmarkt (Global)', line=dict(dash='dash', color=COLOR_AZUL)))
        st.plotly_chart(fig_radar, use_container_width=True)

        st.divider()
        col_gap, col_ampel = st.columns(2)

        # 4. GAP ANALYSIS (Usa r_principal que viene de valores_comparacion)
        with col_gap:
            st.subheader("Gap Analysis (Ziel: 5.0)")
            # r_principal contiene los scores de la dimensión activa
            gap_df = pd.DataFrame({'Dimension': dim_names, 'Gap': [5.0 - m for m in r_principal]})
            gap_df['Color'] = ['#2ecc71' if g <= 1.0 else '#e74c3c' for g in gap_df['Gap']]

            fig_gap = px.bar(gap_df, x='Gap', y='Dimension', orientation='h', text_auto='.2f', color='Color',
                             color_discrete_map="identity", range_x=[0, 5])
            fig_gap.add_vrect(x0=0, x1=1.0, fillcolor="rgba(46, 204, 113, 0.15)", line_width=0)
            fig_gap.add_vline(x=1.0, line_dash="dot", line_color="#34495e", line_width=2)
            st.plotly_chart(fig_gap, use_container_width=True)

        # 5. ITEM-PERFORMANCE (Usa serie_a_mostrar)
        with col_ampel:
            st.subheader("🚦 Item-Performance")
            dim_key = st.selectbox("Dimension auswählen:", list(CONFIG_WEIGHTS.keys()),
                                   format_func=lambda x: CONFIG_WEIGHTS[x]['name_de'])

            items_list = []
            for i_id, i_info in CONFIG_WEIGHTS[dim_key]['items'].items():
                ls_code = i_info['ls_code']

                # Valor del grupo (siempre lo tenemos)
                val_grupo = float(df_filtered[ls_code].mean())

                # Estructura base
                row = {"Item": i_info['name_de'], "Ø Gruppe": val_grupo}

                # Si es modo individual, añadimos el valor personal
                if st.session_state.view_mode == 'individual':
                    val_indiv = float(serie_a_mostrar[ls_code])
                    row["Dein Wert"] = val_indiv
                    val_para_color = val_indiv  # El color se basa en TU valor
                else:
                    val_para_color = val_grupo  # El color se basa en el promedio del grupo

                items_list.append(row)

            df_performance = pd.DataFrame(items_list)


            # Función de color condicional
            def highlight_performance(row):
                # Determinamos qué valor usar para el color según la columna que exista
                val = row['Dein Wert'] if 'Dein Wert' in row else row['Ø Gruppe']
                if val >= 4:
                    color = 'background-color: #d4edda'  # Verde
                elif val >= 3:
                    color = 'background-color: #fff3cd'  # Amarillo
                else:
                    color = 'background-color: #f8d7da'  # Rojo
                return [color] * len(row)


            # Formateo dinámico: solo añadir columnas si existen
            format_dict = {"Ø Gruppe": "{:.2f}"}
            if 'Dein Wert' in df_performance.columns:
                format_dict["Dein Wert"] = "{:.2f}"

            st.dataframe(
                df_performance.style.apply(highlight_performance, axis=1).format(format_dict),
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