"""Recheck evolved search windows directly from the exported CUDA timeline.

This reader does not call the collector's trace analyser. It checks the unchanged
launch model and operation totals against raw ordered kernel timestamps.
"""

import math
from pathlib import Path
import sqlite3


def audit_trace(directory: Path, claimed: dict) -> dict:
    """Validate the fixed 110,592-particle, 480-step diagnostic trace."""
    with sqlite3.connect(f"file:{directory / 'cuda.sqlite'}?mode=ro", uri=True) as db:
        kernels = list(db.execute("SELECT start,end,correlationId FROM CUPTI_ACTIVITY_KIND_KERNEL ORDER BY start"))
        launches = list(db.execute("SELECT a.start,a.correlationId FROM CUPTI_ACTIVITY_KIND_RUNTIME a JOIN StringIds s ON a.nameId=s.id WHERE s.value='cuLaunchKernel' ORDER BY a.start"))
        syncs = list(db.execute("SELECT a.end FROM CUPTI_ACTIVITY_KIND_RUNTIME a JOIN StringIds s ON a.nameId=s.id WHERE s.value='cuStreamSynchronize' ORDER BY a.start"))
        transfers = list(db.execute("SELECT copyKind,bytes FROM CUPTI_ACTIVITY_KIND_MEMCPY"))
    # 17 bitonic levels need 153 passes; each step also has 54 solver kernels.
    operations = [0, 1, 2] + [3] * 153 + [4, 12] + list(range(5, 11)) * 8 + [11]
    if len(kernels) != 99_360 or len(launches) != len(kernels) or len(syncs) != 24_481:
        raise ValueError("changed diagnostic launch or completion count")
    if claimed["whole"]["kernel_count"] != len(kernels) or claimed["whole"]["completion_count"] != len(syncs):
        raise ValueError("false diagnostic launch or completion summary")
    if any(kernel[2] != launch[1] for kernel, launch in zip(kernels, launches, strict=True)):
        raise ValueError("kernel and launch correlation differ")
    expected = {1: (1_920, 1_698_743_040), 2: (12_480, 2_972_920_320)}
    for kind, (calls, size) in expected.items():
        selected = [n for k, n in transfers if k == kind]
        if len(selected) != calls or sum(selected) != size:
            raise ValueError("changed diagnostic transfers")
    checked = {}
    for first, last in ((1, 120), (121, 240), (241, 480)):
        start_index, stop_index = (first - 1) * 207, last * 207
        start = launches[start_index][0]
        stop = launches[stop_index][0] if stop_index < len(launches) else syncs[-1][0]
        row = claimed["windows"][f"{first}-{last}"]
        window_s = (stop - start) / 1_000_000_000
        if not math.isclose(row["window_s"], window_s, rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError("false evolved window duration")
        totals = {str(op): 0 for op in range(13)}
        for index in range(start_index, stop_index):
            a, b, _ = kernels[index]
            if b <= a:
                raise ValueError("invalid kernel duration")
            totals[str(operations[index % 207])] += b - a
        seconds = {key: value / 1_000_000_000 for key, value in totals.items()}
        if row["operations_device_s"].keys() != seconds.keys() or any(
            not math.isclose(row["operations_device_s"][key], value, rel_tol=1e-12, abs_tol=1e-12)
            for key, value in seconds.items()
        ):
            raise ValueError("false evolved operation duration")
        checked[f"{first}-{last}"] = {"count_s": seconds["4"], "fill_sort_s": seconds["12"]}
    return {"kernel_count": len(kernels), "completion_count": len(syncs), "windows": checked}
