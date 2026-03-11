import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Tus módulos personalizados
from src.config import CONFIG_WEIGHTS, MAP_SECTOR, MAP_NUM_EMP, MM_LEVELS
from src.engine import calculate_maturity
from src.generator import generate_dummy_data

# 1. CONFIGURACIÓN E INTERFAZ INICIAL
st.set_page_config(page_title="I5.0 Transformation Check", layout="wide")

# --- LÓGICA DE CARGA DE DATOS ---
st.sidebar.header("Data Source")
data_source = st.sidebar.radio("Datenquelle auswählen:", ["Sample Data", "Upload CSV"])

df_full = None

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

# --- PREPARACIÓN DE DATOS PARA VISUALIZACIÓN ---
# Creamos columnas legibles para los filtros
df_full['Sector'] = df_full['branche'].map(MAP_SECTOR)
df_full['Size'] = df_full['anzMA'].map(MAP_NUM_EMP)
df_full['PLZ_Group'] = df_full['plz'].astype(str).str[:2]

dim_cols = [f"Score_dim{i}" for i in range(1, 8)]
dim_names = [info['name_de'] for info in CONFIG_WEIGHTS.values()]

# --- SIDEBAR: FILTROS GLOBALES ---
st.sidebar.divider()
st.sidebar.header("Globaler Filter")
filter_sector = st.sidebar.selectbox("Branche", ["Alle"] + list(MAP_SECTOR.values()))
filter_size = st.sidebar.selectbox("Unternehmensgröße", ["Alle"] + list(MAP_NUM_EMP.values()))

compare_mode = st.sidebar.checkbox("Vergleiche aktivieren", value=True)

# Aplicar filtros (df_filtered para la tabla/empresa, df_full para promedios globales)
df_filtered = df_full.copy()
if filter_sector != "Alle":
    df_filtered = df_filtered[df_filtered['Sector'] == filter_sector]
if filter_size != "Alle":
    df_filtered = df_filtered[df_filtered['Size'] == filter_size]

# --- TABS PRINCIPALES ---
st.title("📊 I5.0 Transformations-Check Standortbestimmung")
tab_gen, tab_ind = st.tabs(["Allgemeine Analyse (Strategisch)", "Bericht nach Unternehmen (Diagnose)"])

# ==========================================
# PÁGINA 1: ANÁLISIS GENERAL
# ==========================================
with tab_gen:
    st.header("Panorama der digitalen Reife")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Reifegrad nach Region (PLZ)")
        geo_data = df_filtered.groupby('PLZ_Group')['Maturity_Score'].mean().reset_index()
        fig_heat = px.bar(geo_data, x='PLZ_Group', y='Maturity_Score',
                          color='Maturity_Score', color_continuous_scale='Viridis',
                          labels={'PLZ_Group': 'PLZ (Erste 2 Ziffern)', 'Maturity_Score': 'Durchschnitt'})
        st.plotly_chart(fig_heat, use_container_width=True)

    with col2:
        st.subheader("Aufteilung nach Sektoren")
        sector_data = df_filtered.groupby('Sector')['Maturity_Score'].mean().sort_values().reset_index()
        fig_sec = px.bar(sector_data, x='Maturity_Score', y='Sector', orientation='h',
                         color='Maturity_Score', color_continuous_scale='Blues')
        st.plotly_chart(fig_sec, use_container_width=True)

    st.divider()
    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Größe vs. Reife")
        fig_box = px.box(df_filtered, x='Size', y='Maturity_Score', color='Size',
                         category_orders={"Size": ["<= 10", "<= 50", "<= 100", "<= 250", "> 250"]})
        st.plotly_chart(fig_box, use_container_width=True)

    with col4:
        st.subheader("Globaldurchschnitt der Dimensionen")
        avg_dims = df_filtered[dim_cols].mean().reset_index()
        avg_dims.columns = ['Dim', 'Mean']
        avg_dims['Name'] = dim_names
        fig_avg = px.bar(avg_dims, x='Mean', y='Name', orientation='h', text_auto='.2f',
                         color='Mean', color_continuous_scale='GnBu')
        st.plotly_chart(fig_avg, use_container_width=True)

# ==========================================
# PÁGINA 2: INFORME POR EMPRESA
# ==========================================
with tab_ind:
    if df_filtered.empty:
        st.warning("Keine Daten mit den aktuellen Filtern verfügbar.")
    else:
        emp_id = st.selectbox("Wählen Sie die Firmen-ID:", df_filtered['id'].unique())
        selected_row = df_filtered[df_filtered['id'] == emp_id].iloc[0]

        col_gauge, col_radar = st.columns([1, 2])

        with col_gauge:
            st.subheader("Gesamt-Reifegrad")
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=selected_row['Maturity_Score'],
                title={'text': f"Level: {selected_row['Maturity_Level']}"},
                gauge={
                    'axis': {'range': [1, 5]},
                    'bar': {'color': "#004b23"},
                    'steps': [
                        {'range': [1, 2], 'color': "#ffadad"},
                        {'range': [2, 3], 'color': "#ffd6a5"},
                        {'range': [3, 4], 'color': "#fdffb6"},
                        {'range': [4, 5], 'color': "#caffbf"}]
                }
            ))
            fig_gauge.update_layout(height=350, margin=dict(t=50, b=0))
            st.plotly_chart(fig_gauge, use_container_width=True)

        with col_radar:
            st.subheader("Dimensionen-Vergleich")
            r_emp = [selected_row[c] for c in dim_cols]

            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(r=r_emp + [r_emp[0]], theta=dim_names + [dim_names[0]],
                                                fill='toself', name='Unternehmen', line_color='#004b23'))

            if compare_mode:
                # Media sectorial (del df_full para que sea robusta)
                sec_mean = df_full[df_full['Sector'] == selected_row['Sector']][dim_cols].mean().tolist()
                fig_radar.add_trace(go.Scatterpolar(r=sec_mean + [sec_mean[0]], theta=dim_names + [dim_names[0]],
                                                    name=f'Sektor-Schnitt ({selected_row["Sector"]})',
                                                    line=dict(dash='dot', color='#0077b6')))

                # Media global
                glob_mean = df_full[dim_cols].mean().tolist()
                fig_radar.add_trace(go.Scatterpolar(r=glob_mean + [glob_mean[0]], theta=dim_names + [dim_names[0]],
                                                    name='Global-Schnitt', line=dict(dash='dash', color='gray')))

            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
                                    legend=dict(orientation="h", y=-0.2), height=450)
            st.plotly_chart(fig_radar, use_container_width=True)

        st.divider()
        col_gap, col_ampel = st.columns(2)

        with col_gap:
            st.subheader("Gap Analysis (Ziel: Senior 5.0)")
            gap_data = pd.DataFrame({'Dimension': dim_names, 'Gap': [5.0 - selected_row[c] for c in dim_cols]})
            fig_gap = px.bar(gap_data, x='Gap', y='Dimension', orientation='h',
                             color='Gap', color_continuous_scale='Reds')
            st.plotly_chart(fig_gap, use_container_width=True)

        with col_ampel:
            st.subheader("🚦 Item-Ampel")
            dim_key = st.selectbox("Detail-Analyse Dimension:", list(CONFIG_WEIGHTS.keys()),
                                   format_func=lambda x: CONFIG_WEIGHTS[x]['name_de'])

            items_list = []
            for i_id, i_info in CONFIG_WEIGHTS[dim_key]['items'].items():
                val = selected_row[i_info['ls_code']]
                status = "🟢" if val >= 4 else "🟡" if val >= 2.5 else "🔴"
                items_list.append({"Item": i_info['name_de'], "Wert": val, "Status": status})

            st.table(pd.DataFrame(items_list))