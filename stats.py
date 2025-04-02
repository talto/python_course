from typing import Dict, List, Union

import numpy as np


def compute_statistics(times: List[float]) -> Dict[str, Union[float, int]]:
    """Вычисляет статистику по времени отклика"""
    if not times:
        return {}

    arr = np.array(times)
    return {
        "count": len(arr),
        "mean": round(arr.mean(), 4),
        "median": round(np.median(arr), 4),
        "min": round(arr.min(), 4),
        "max": round(arr.max(), 4),
    }
