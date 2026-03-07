import streamlit as st
import pandas as pd
import maturity
import plotly.graph_objects as go

# Configure the main Streamlit page
st.set_page_config(layout="wide", page_title="I5.0 Transformations-Check")

TEST_PATH = "data/results-survey413141.csv"

@st.cache_data
def load_data(path=None):
    if path:
        df = pd.read_csv(path)
    else:
        df = maturity.sample_data(1000)
    df = maturity.get_scores(df)
    return df

# Load the dataset
st.sidebar.header("Data Source")
data_source = st.sidebar.radio("Select Data Source:", ["Sample Data", "Upload CSV"])

df = None
if data_source == "Sample Data":
    num_samples = st.sidebar.number_input("Number of samples", min_value=1, max_value=10000, value=1000)
    if st.sidebar.button("Generate Samples"):
        df = maturity.sample_data(num_samples)
        df = maturity.get_scores(df)
        st.session_state['df'] = df
    elif 'df' in st.session_state and st.session_state['df'] is not None:
        df = st.session_state['df']
    else:
        df = maturity.sample_data(num_samples)
        df = maturity.get_scores(df)
        st.session_state['df'] = df
else:
    uploaded_file = st.sidebar.file_uploader("Upload CSV file", type=["csv"])
    if uploaded_file is not None:
        df = load_data(uploaded_file)
        st.session_state['df'] = df
    elif 'df' in st.session_state and st.session_state['df'] is not None:
        df = st.session_state['df']
    else:
        st.info("Please upload a CSV file or select 'Sample Data' to continue.")
        st.stop()


dim_cols = [f"Dimension_{i}_Score" for i in range(1, maturity.MM_NUM_DIMS + 1)]
mean_scores = df[dim_cols].mean()
mean_overall = df["Maturity_Score"].mean()

st.sidebar.header("Options")

if "Antwort ID" in df.columns:
    row_selector = st.sidebar.selectbox("Select Record (Antwort ID)", df["Antwort ID"].astype(str).tolist())
    selected_row = df[df["Antwort ID"].astype(str) == row_selector].iloc[0]
else:
    row_selector = st.sidebar.selectbox("Select Record (Index)", df.index.tolist())
    selected_row = df.loc[row_selector]

compare_mean = st.sidebar.checkbox("Compare to Dataset Mean", value=True)

# ==========================================
# Main layout
# ==========================================
st.title("Transformations-Check Standortbestimmung")

# 1. Overall Maturity Score
st.header("Gesamtergebnis")
col1, col2 = st.columns(2)

with col1:
    score = selected_row["Maturity_Score"]
    level = maturity.get_level(score)
    st.metric(label="Ihr Ergebnis", value=f"{score:.2f} ({level})")

with col2:
    if compare_mean:
        diff = selected_row["Maturity_Score"] - mean_overall
        st.metric(label="Durchschnittsergebnis anderer Unternehmen", value=f"{mean_overall:.2f}", delta=f"{diff:.2f}")

# ==========================================
# 2. Maturity Dimensions Radar Chart (Enhanced)
# ==========================================
st.header("Ihr Reifegrad-Profil")

# Data Prep: To "close" the radar loop, we repeat the first value at the end
dimension_labels = list(maturity.MM_DIM_SHORT_NAMES)
dimension_labels += [dimension_labels[0]]

r_selected = [selected_row[col] for col in dim_cols]
r_selected += [r_selected[0]]

if compare_mean:
    r_mean = [mean_scores[col] for col in dim_cols]
    r_mean += [r_mean[0]]

fig = go.Figure()

# Selected Company Trace
fig.add_trace(go.Scatterpolar(
    r=r_selected,
    theta=dimension_labels,
    fill='toself',
    name='Ihr Unternehmen',
    line=dict(color='#004b23', width=3), # Deep green professional look
    fillcolor='rgba(0, 75, 35, 0.2)',
    marker=dict(size=8, symbol='circle'),
    hovertemplate="<b>%{theta}</b><br>Score: %{r:.2f}<extra></extra>"
))

# Mean Comparison Trace (if enabled)
if compare_mean:
    fig.add_trace(go.Scatterpolar(
        r=r_mean,
        theta=dimension_labels,
        fill='toself',
        name='Durchschnitt',
        line=dict(color='#6c757d', width=2, dash='dash'), # Muted gray dash
        fillcolor='rgba(108, 117, 125, 0.1)',
        marker=dict(size=6, symbol='x'),
        hovertemplate="<b>%{theta}</b><br>Durchschnitt: %{r:.2f}<extra></extra>"
    ))

fig.update_layout(
    polar=dict(
        radialaxis=dict(
            visible=True,
            range=[0, 5],
            tickvals=[1, 2, 3, 4, 5],
            tickfont=dict(size=11, color="#444"),
            gridcolor="#e9ecef", # Subtle grid lines
            linecolor="rgba(0,0,0,0)", # Hide axis line
        ),
        angularaxis=dict(
            tickfont=dict(size=13, color="#212529", family="Arial Black"),
            gridcolor="#e9ecef",
            rotation=90, # Starts first dimension at the top
            direction="clockwise"
        ),
        bgcolor="white"
    ),
    showlegend=True,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.2,
        xanchor="center",
        x=0.5
    ),
    margin=dict(l=100, r=100, t=40, b=40),
    height=550,
    paper_bgcolor="rgba(0,0,0,0)", # Transparent background for Streamlit
    plot_bgcolor="rgba(0,0,0,0)",
)

st.plotly_chart(fig, width="stretch", config={'displayModeBar': False})

# 3. Raw Data Display
st.subheader("Detailwerte der Reifegradanalyse")
data_to_show = pd.DataFrame({
    "Bereich": maturity.MM_DIM_SHORT_NAMES,
    "Ihr Ergebnis": [selected_row[col] for col in dim_cols]
})

if compare_mean:
    data_to_show["Durchschnitt anderer Unternehmen"] = [mean_scores[col] for col in dim_cols]

data_to_show = data_to_show.round(decimals=2)

st.dataframe(data_to_show, hide_index=True)
