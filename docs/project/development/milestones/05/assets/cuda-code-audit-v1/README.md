# CUDA code audit receipt

This supports the [audit](/docs/project/development/milestones/05/performance-cuda-code-audit.md)
and [file review](/docs/project/development/milestones/05/performance-cuda-file-review.md).
`audit.json` identifies 51 reviewed files and records the source/trace checks performed locally
on 26 October 2026. It is not a new timing campaign, executable qualification or Git checkpoint.

The ordinary source matched all 180 hashes of the preceding host-coordination control.
Its full base commit, working-tree fingerprint, binary identity and reconstruction are recorded.
The [control patch](/docs/project/development/milestones/05/assets/host-coordination-v1/control.patch)
reconstructs that source from the named base; no whole source tree is duplicated here.

The receipt derives operation shares and ideal removal ceilings from the retained 110,592-particle
trace. An independent reader rechecked launch counts/dimensions, operation windows, transfers and
completions directly from its shared SQLite export. The normal solver median remains a distinct
measurement. No host, GPU or driver cost is inferred from `btop` utilisation alone.

To repeat the trace check, first extract `verification.tar.xz` and `timeline.tar.xz` from
[host-coordination-v1](/docs/project/development/milestones/05/assets/host-coordination-v1/README.md)
into a new directory, then run from the EPQ root:

```sh
python3 - /path/to/extracted-evidence <<'PY'
import json
from pathlib import Path
import sys
from tests.performance.audit_neighbour_bands import audit_trace

root = Path(sys.argv[1])
claimed = json.loads((root / "ranking-timeline/windows.json").read_bytes())
print(json.dumps(audit_trace(root / "ranking-timeline", claimed, row_sort=True), indent=2))
PY
```

`SHA256SUMS` identifies this receipt and the two audit documents. Source-file hashes in the
receipt describe the inspected checkout, not future edits at its live navigation links.
The primary-PC campaign owns its original commands, environment and raw measurements.
