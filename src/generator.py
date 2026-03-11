import random
import pandas as pd
from .config import CONFIG_WEIGHTS, MAP_SECTOR, MAP_NUM_EMP

def generate_dummy_data(n=100):
    data = []
    for i in range(n):
        row = {
            'id': i + 1,
            'submitdate': '2024-05-20 10:00:00',
            'anzMA': random.choice(list(MAP_NUM_EMP.keys())),
            'branche': random.choice(list(MAP_SECTOR.keys())),
            'plz': random.randint(31,59)
        }

        for dim in CONFIG_WEIGHTS.values():
            for item in dim['items'].values():
                row[item['ls_code']] = random.randint(1,5)

        data.append(row)

    return pd.DataFrame(data)
