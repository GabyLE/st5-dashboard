import pandas as pd
from .config import CONFIG_WEIGHTS, COLUMN_MAP, MM_LEVELS

def calculate_maturity(df):
    results_df = df.copy()

    # Calcular Scores por Dimensión
    for dim_id, dim_info in CONFIG_WEIGHTS.items():
        score_col = f"Score_{dim_id}"
        results_df[score_col] = 0.0

        for item_info in dim_info['items'].values():
            ls_col = item_info.get('ls_code')
            weight = item_info.get('weight_item', 0)

            if ls_col in results_df.columns:
                results_df[score_col] += pd.to_numeric(results_df[ls_col], errors='coerce').fillna(0) * weight

    # Calcular Maturity Score Global (Fórmula: suma de Dim_Score * Dim_Weight)
    results_df['Maturity_Score'] = 0.0
    for dim_id, dim_info in CONFIG_WEIGHTS.items():
        results_df['Maturity_Score'] += results_df[f"Score_{dim_id}"] * dim_info['weight_dim']

    # Nivel de Madurez (Maturity_Level)
    results_df['Maturity_Level'] = results_df['Maturity_Score'].apply(get_level_label)

    return results_df

def get_level_label(score):
    from .config import MM_LEVELS
    for label, (low, high) in MM_LEVELS:
        if low <= score < high:
            return label

    if score >= 5.0: return "Senior"
    return "Undefined"

def get_dimension_avg(df):
    """
    Calculate the mean of the whole data base for each dimension
    """
    dim_cols = [f'Score_{dim}' for dim in CONFIG_WEIGHTS.keys()]
    return df[dim_cols].mean()