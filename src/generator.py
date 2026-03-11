from .config import CONFIG_WEIGHTS, MAP_SECTOR, MAP_NUM_EMP
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta


def generate_dummy_data(n=100):
    rows = []
    now = datetime.now()

    allowed_plz = [32, 33, 34, 37, 40, 41, 42, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 57, 58, 59]

    for i in range(n):

        row = {
            "id": i + 1000,
            "submitdate": (now - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d %H:%M:%S"),
            "lastpage": 8,
            "startlanguage": "de",
            "seed": random.randint(10000, 99999),
        }

        # data company
        branch_code = random.choice(list(MAP_SECTOR.keys()))
        row["branche"] = branch_code
        row["branche[other]"] = "Spezialindustrie" if branch_code == "bran9" else ""

        row["anzMA"] = random.choice(list(MAP_NUM_EMP.keys()))

        row["plz"] = random.choice(allowed_plz)

        for dim_info in CONFIG_WEIGHTS.values():
            for item in dim_info["items"].values():
                row[item["ls_code"]] = np.random.choice([1, 2, 3, 4, 5], p=[0.1, 0.2, 0.4, 0.2, 0.1])

        rows.append(row)

    return pd.DataFrame(rows)