"""Recheck evolved search windows directly from the exported CUDA timeline.

This reader does not call the collector's trace analyser. It checks the unchanged
launch model and operation totals against raw ordered kernel timestamps.
"""

import math
from pathlib import Path
import sqlite3


def audit_trace(directory: Path, claimed: dict, *, row_sort: bool = False, resident: bool = False) -> dict:
    """Validate the fixed 110,592-particle, 480-step diagnostic trace."""
    with sqlite3.connect(f"file:{directory / 'cuda.sqlite'}?mode=ro", uri=True) as db:
        kernels = list(db.execute("SELECT start,end,correlationId,gridX,blockX FROM CUPTI_ACTIVITY_KIND_KERNEL ORDER BY start"))
        launches = list(db.execute("SELECT a.start,a.correlationId FROM CUPTI_ACTIVITY_KIND_RUNTIME a JOIN StringIds s ON a.nameId=s.id WHERE s.value='cuLaunchKernel' ORDER BY a.start"))
        syncs = list(db.execute("SELECT a.end FROM CUPTI_ACTIVITY_KIND_RUNTIME a JOIN StringIds s ON a.nameId=s.id WHERE s.value='cuStreamSynchronize' ORDER BY a.start"))
        transfers = list(db.execute("SELECT copyKind,bytes FROM CUPTI_ACTIVITY_KIND_MEMCPY"))
    # 17 bitonic levels need 153 passes; each step also has 54 solver kernels.
    operations = [0, 1, 2] + [3] * 153 + [4, 12] + list(range(5, 11)) * 8 + [11]
    if row_sort:
        operations.insert(158, 18)
    per_step = len(operations)
    if len(kernels) != per_step * 480 or len(launches) != len(kernels) or len(syncs) != (14_901 if resident else 24_481):
        raise ValueError("changed diagnostic launch or completion count")
    if claimed["whole"]["kernel_count"] != len(kernels) or claimed["whole"]["completion_count"] != len(syncs):
        raise ValueError("false diagnostic launch or completion summary")
    if any(kernel[2] != launch[1] for kernel, launch in zip(kernels, launches, strict=True)):
        raise ValueError("kernel and launch correlation differ")
    expected = {1: (483, 427_331_424) if resident else (1_920, 1_698_743_040), 2: (12_480, 2_972_920_320)}
    for kind, (calls, size) in expected.items():
        selected = [n for k, n in transfers if k == kind]
        if len(selected) != calls or sum(selected) != size:
            raise ValueError("changed diagnostic transfers")
        name = "host_to_device" if kind == 1 else "device_to_host"
        if claimed["whole"]["transfers"][name] != {"calls": calls, "bytes": size}:
            raise ValueError("false diagnostic transfer summary")
    checked = {}
    for first, last in ((1, 120), (121, 240), (241, 480)):
        start_index, stop_index = (first - 1) * per_step, last * per_step
        start = launches[start_index][0]
        stop = launches[stop_index][0] if stop_index < len(launches) else syncs[-1][0]
        row = claimed["windows"][f"{first}-{last}"]
        window_s = (stop - start) / 1_000_000_000
        if not math.isclose(row["window_s"], window_s, rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError("false evolved window duration")
        totals = {str(op): 0 for op in (*range(13), 18) if row_sort or op != 18}
        for index in range(start_index, stop_index):
            a, b, _, grid, block = kernels[index]
            if b <= a:
                raise ValueError("invalid kernel duration")
            operation = operations[index % per_step]
            lanes = 110592 * 32 if operation == 18 else 131072 if operation in (2, 3) else 110592
            if block != 128 or grid != (lanes + 127) // 128:
                raise ValueError("wrong kernel launch dimensions")
            totals[str(operation)] += b - a
        seconds = {key: value / 1_000_000_000 for key, value in totals.items()}
        if row["operations_device_s"].keys() != seconds.keys() or any(
            not math.isclose(row["operations_device_s"][key], value, rel_tol=1e-12, abs_tol=1e-12)
            for key, value in seconds.items()
        ):
            raise ValueError("false evolved operation duration")
        checked[f"{first}-{last}"] = {"count_s": seconds["4"], "fill_sort_s": seconds["12"] + seconds.get("18", 0)}
    return {"kernel_count": len(kernels), "completion_count": len(syncs), "windows": checked}
