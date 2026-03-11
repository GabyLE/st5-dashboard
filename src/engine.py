import math
from .config import CONFIG_WEIGHTS, COLUMN_MAP, MM_LEVELS

def fix_weights_logic(weights):

    total = sum(weights)
    if not math.isclose(total, 1.0, rel_tol=1e-7):
        return [w / total for w in weights]
    return weights

def calculate_maturity(df):
    dim_weights = [d["weight_dim"] for d in CONFIG_WEIGHTS.values()]
    fixed_dim_weights = fix_weights_logic(dim_weights)

    # weight items in dimension
    for dim_key in CONFIG_WEIGHTS:
        item_weights = [it["weight_item"] for it in CONFIG_WEIGHTS[dim_key]["items"].values()]
        fixed_item_weights = fix_weights_logic(item_weights)

        for i, item_key in enumerate(CONFIG_WEIGHTS[dim_key]["items"]):
            CONFIG_WEIGHTS[dim_key]["items"][item_key]["weight_item"] = fixed_item_weights[i]

    # --- SCORES ---
    for dim_id, dim_info in CONFIG_WEIGHTS.items():

        cols = [it["ls_code"] for it in dim_info["items"].values()]
        weights = [it["weight_item"] for it in dim_info["items"].values()]

        # (Val * Weights).sum()
        df[f"Score_{dim_id}"] = df[cols].multiply(weights, axis=1).sum(axis=1)


    score_cols = [f"Score_{dim_id}" for dim_id in CONFIG_WEIGHTS.keys()]
    df["Maturity_Score"] = df[score_cols].dot(fixed_dim_weights)

    # Level
    df["Maturity_Level"] = df["Maturity_Score"].apply(get_level_label)

    return df

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