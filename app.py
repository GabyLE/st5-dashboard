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
        if 'view_mode' not in st.session_state: st.session_state.view_mode = 'general'


        def reset_benchmark():
            st.session_state.view_mode = 'general'
            st.session_state.id_input_val = ""
            st.query_params.clear()


        # 2. Input ID
        st.text_input("Geben Sie Ihre Antwort-ID ein:", key="id_input_val")
        input_id = st.session_state.id_input_val

        # 3. Lógica de datos unificada (aquí forzamos la sincronización)
        if input_id and input_id.isdigit():
            data = df_full[df_full['id'] == int(input_id)]
            if not data.empty:
                st.session_state.view_mode = 'individual'
                r_principal = data[score_cols].values.flatten().tolist()
                score_actual = data['Maturity_Score'].iloc[0]  # El score exacto del individuo
                serie_a_mostrar = data.iloc[0]
                nombre_principal, color_principal = 'Ihr Ergebnis', '#2ecc71'
                if st.button("Zurück zum allgemeinen Benchmark", on_click=reset_benchmark): st.rerun()
            else:
                st.error("ID nicht gefunden.")
                st.session_state.view_mode = 'general'
                r_principal = group_means  # Usamos los promedios del filtro
                score_actual = filter_avg  # Sincronizado con las tarjetas superiores
                nombre_principal, color_principal = 'Aktueller Filter', COLOR_VERDE
        else:
            st.session_state.view_mode = 'general'
            r_principal = group_means
            score_actual = filter_avg  # Sincronizado con las tarjetas superiores
            nombre_principal, color_principal = 'Aktueller Filter', COLOR_VERDE

        # 4. KPI METRICS (Sincronizadas)
        def get_label_by_score(score):
            for label, (min_val, max_val) in MM_LEVELS:
                # Usamos <= para el límite superior para evitar solapamientos
                if min_val <= score < max_val:
                    return label
            return "Senior" if score >= 4.0 else "Außenseiter"  # Fallback


        # 2. Bloque de KPI Metrics actualizado
        col1, col2, col3 = st.columns(3)

        # Calculamos la etiqueta dinámica
        label_actual = get_label_by_score(score_actual)

        col1.metric("Ø Maturity Score", f"{score_actual:.2f}")
        col2.metric("Abstand zum Ziel (5.0)", f"{(5.0 - score_actual):.2f}")
        col3.metric("Level", label_actual)

        # --- 3. RADAR CON COMPARADORES ---

        benchmarks = st.multiselect(
            "Vergleich hinzufügen:",
            ["Gesamtmarkt", "Branchen-Schnitt", "Unternehmensgröße"]
        )

        fig_radar = go.Figure()

        # 1. Trazo Principal: SIEMPRE VERDE DE MARCA
        fig_radar.add_trace(go.Scatterpolar(
            r=r_principal + [r_principal[0]],
            theta=dim_names + [dim_names[0]],
            fill='toself',
            fillcolor='rgba(168, 212, 58, 0.2)',  # Verde suave de relleno
            name=nombre_principal,
            line=dict(color=COLOR_VERDE, width=3)  # Grosor 3 para que resalte
        ))

        # 2. Trazos comparativos: Colores oscuros/fuertes y mayor grosor
        if "Gesamtmarkt" in benchmarks:
            fig_radar.add_trace(go.Scatterpolar(
                r=global_means + [global_means[0]],
                theta=dim_names + [dim_names[0]],
                name='Gesamtmarkt',
                line=dict(dash='dash', color='#2d2e83', width=2.5)  # Azul oscuro
            ))

        if "Branchen-Schnitt" in benchmarks:
            sector_actual = serie_a_mostrar['Sector']
            sec_means = df_full[df_full['Sector'] == sector_actual][score_cols].mean().tolist()
            fig_radar.add_trace(go.Scatterpolar(
                r=sec_means + [sec_means[0]],
                theta=dim_names + [dim_names[0]],
                name=f'Sektor: {sector_actual}',
                line=dict(dash='dot', color='#d35400', width=2.5)  # Naranja/Rojo fuerte (contraste)
            ))

        if "Unternehmensgröße" in benchmarks:
            size_actual = serie_a_mostrar['Size']
            size_means = df_full[df_full['Size'] == size_actual][score_cols].mean().tolist()
            fig_radar.add_trace(go.Scatterpolar(
                r=size_means + [size_means[0]],
                theta=dim_names + [dim_names[0]],
                name=f'Größe: {size_actual}',
                line=dict(dash='longdash', color='#8e44ad', width=2.5)  # Púrpura fuerte
            ))

        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[1, 5])),
            legend=dict(orientation="h", y=-0.2),
            height=500
        )

        st.plotly_chart(fig_radar, use_container_width=True)

        # --- 4. ACCIÓN: STÄRKEN & SCHWÄCHEN ---
        st.divider()
        col_s, col_w = st.columns(2)

        # Ordenamos las dimensiones para hallar top 3
        dim_scores = sorted(zip(dim_names, r_principal), key=lambda x: x[1], reverse=True)

        with col_s:
            st.success("Top 3 Stärken")
            for name, val in dim_scores[:3]: st.write(f"✅ **{name}**: {val:.2f}")
        with col_w:
            st.error("Top 3 Handlungsfelder")
            for name, val in dim_scores[-3:]: st.write(f"⚠️ **{name}**: {val:.2f}")

        # --- 5. TABLA DETALLADA ---
        st.divider()
        st.subheader("🚦 Item-Performance (Detail)")
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
        st.dataframe(df_p.style.apply(lambda row: ['background-color: #d4edda' if (row[
                                                                                       'Dein Wert'] if 'Dein Wert' in row else
                                                                                   row[
                                                                                       'Ø Gruppe']) >= 4 else 'background-color: #f8d7da'] * len(
            row), axis=1), use_container_width=True)



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