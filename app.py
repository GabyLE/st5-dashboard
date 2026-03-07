import streamlit as st
import pandas as pd
import maturity
import plotly.graph_objects as go

# Configure the main Streamlit page
st.set_page_config(layout="wide", page_title="Industry 5.0 Maturity Assessment")

TEST_PATH = "data/results-survey413141.csv"

@st.cache_data
def load_data(path=None):
    """Loads the CSV survey dataset and computes the maturity scores."""
    if path:
        df = pd.read_csv(path)
    else:
        df = maturity.sample_data(1000)
    df = maturity.get_scores(df)
    return df

# Load the dataset
sample_data = True
df = load_data()


# Calculate Mean Values over the full dataset
dim_cols = [f"Dimension_{i}_Score" for i in range(1, 8)]
mean_scores = df[dim_cols].mean()
mean_overall = df["Maturity_Score"].mean()

# ==========================================
# Sidebar UI setup
# ==========================================
st.sidebar.header("Options")

# Let the user select a specific record by "Antwort ID" 
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
st.title("Industry 5.0 Maturity Assessment")

# 1. Overall Maturity Score
st.header("Overall Maturity Score")
col1, col2 = st.columns(2)

with col1:
    st.metric(label="Selected Record Score", value=f"{selected_row['Maturity_Score']:.2f}")

with col2:
    if compare_mean:
        diff = selected_row['Maturity_Score'] - mean_overall
        st.metric(label="Dataset Mean Score", value=f"{mean_overall:.2f}", delta=f"{diff:.2f}")

# 2. Maturity Dimensions Radar Chart
st.header("Maturity Dimensions Radar Chart")

# Labels for the 7 individual dimensions
dimension_labels = maturity.MM_ORIGINAL_DIM_NAMES

fig = go.Figure()

# Add the selected row trace (Filled Radar)
fig.add_trace(go.Scatterpolar(
    r=[selected_row[col] for col in dim_cols],
    theta=dimension_labels,
    fill='toself',
    name='Selected Record',
    line_color='blue'
))

# Add the mean trace if the user requested comparison (Filled Radar)
if compare_mean:
    fig.add_trace(go.Scatterpolar(
        r=[mean_scores[col] for col in dim_cols],
        theta=dimension_labels,
        fill='toself',
        name='Dataset Mean',
        line_color='orange'
    ))

# Standardize polar chart configuration
fig.update_layout(
    polar=dict(
        radialaxis=dict(
            visible=True,
            range=[0, 5]  # Scale constraint to match your max score logic
        )
    ),
    showlegend=True,
    height=600
)

# Render Plotly chart in Streamlit
st.plotly_chart(fig, width="stretch")

# 3. Raw Data Display
st.subheader("Dimension Scores Breakdown")
data_to_show = pd.DataFrame({
    "Dimension": dimension_labels,
    "Selected Record": [selected_row[col] for col in dim_cols]
})

if compare_mean:
    data_to_show["Dataset Mean"] = [mean_scores[col] for col in dim_cols]

st.dataframe(data_to_show)
