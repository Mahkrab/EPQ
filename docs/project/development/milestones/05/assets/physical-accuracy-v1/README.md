# Physical accuracy evidence

Read the [decision report](/docs/project/development/milestones/05/performance-physical-accuracy.md)
for the numerical findings, acceptance limits and recommendation. No production policy was admitted.

## Retained evidence and retention limit

The PC experiment ran under `/tmp/epq-physical-accuracy-20261028`. After the measurements and
summaries were copied locally, that temporary directory disappeared during final evidence transfer.
The cause was not established. A completed 241 MiB full archive was observed remotely, with SHA256
`8554540b28a2aa327d90537ce15241446941238f16693c833f01fddf908419a3`, but was **not transferred**.
That hash is a record of the lost object, not a claim that its contents are retained here.

The retained package therefore has a narrower audit boundary:

* `screen.json`, `validate.json` and `hydro.json` retain all completed campaign metrics, per-step
  timing arrays, parameter settings and independent health summaries. The failed first refresh is
  visible as a null result in the screen. Its raw failure request and preliminary run outputs were lost.
* `iteration-trace.json` and `refresh-summary.json` retain the later iteration and repaired-refresh
  health measurements. The refresh ran to completion; its summary is not a fresh production result.
* `oracle.json` retains the binary64 stage residuals and device/reference errors.
* `timings.json` retains all six control/candidate pairs, including warm-up pair zero.
  `cost-summary.json` reports the five admitted pairs and the fresh production timing.
* `production-fresh.json.gz` retains the complete production request, stdout and stderr, including
  resolved inputs, all step reports and the final snapshot. Its reconstructed binary snapshot exactly
  matches the independently transferred native one-second state.
* `identity.json` was copied before the loss and retains hashes for original input/state/source/device
  executables, hardware, compiler and precise build flags. The quality reader was reused from the
  preceding architecture study; it was not separately rehashed in this campaign's identity file.
* `retained-inputs-and-states.tar.xz` contains **65 hash-verified files**: original base inputs,
  reconstructed experimental inputs and driver sources, plus eight snapshots copied before the loss.
  `recovery.json` records each original and recovered hash: all 65 match. The original base input
  bytes came from the existing architecture study's retained `inputs.tar.xz`; reconstructed inputs
  are not misrepresented as original process outputs. Most intermediate/raw campaign states and
  experiment executables are unavailable. Their retained hashes do not replace those files.
* `production-preservation.json` verifies all thirteen remaining native source/licence files against
  the device export. Existing unrelated Rust test relocation and parent work were preserved.
* The PNG figures are locally generated plots. The tank projections use retained raw snapshots;
  the density-cost plot uses the retained health summaries. They are not hosted rendering evidence.

The missing raw states limit independent re-auditing of most health summaries. The retained
observations, successful reference fixtures and verified inputs support the reported bounded
conclusions, but do not justify a production change or a claim of complete raw-data preservation.

## Reproduction

The numerical source is Maelstrom `250932784790ba26cdc55fc38a877ccefacbf054`. Export its native
sources into a disposable directory and overlay the relevant retained `control/driver.cu`,
`clamp/driver.cu` or `refresh/driver.cu`. The compression-only variant additionally inserts
`constraint=fmaxf(0.0f,constraint);` immediately after the single signed constraint calculation in
`solver.cu`. The refresh driver rebuilds rows between iterations and resets `b.first_operation=0`
before search. It retains the device search, sorting and numerical algorithms and precise flags.

Build each private driver with:

```sh
/usr/local/cuda/bin/nvcc --std=c++17 --ftz=false --prec-div=true --prec-sqrt=true \
  -O3 --gpu-architecture=compute_89 --fmad=false driver.cu -o driver
```

The command format is:

```text
driver INPUT STEPS ITERATIONS checked OUTPUT_PREFIX 1 0
```

The last two arguments enable observation files and disable velocity effects. The exact encoded
inputs are retained in the archive. These commands start new simulations from those encoded initial
states. They do not resume observations. `control/trace.cu` records each iteration at step 240.

The reusable parameter encoders, oracle and campaign descriptions are
[physical_accuracy.py](/tools/performance/physical_accuracy.py),
[physical_reference.py](/tools/performance/physical_reference.py) and
[physical_followup.py](/tools/performance/physical_followup.py). Run modules from the repository
root using `python3 -m tools.performance.NAME`. The campaign expects base inputs and already built
drivers under its disposable root. Its screen was executed before the encoder's one-ULP baseline
preservation fix; the exact screen inputs are hash-verified in the retained archive. Rerunning the
current encoder uses the corrected baseline, not precisely those older screen bytes.

The health-reader CLI is the one documented by
[architecture_quality.cpp](/tools/performance/architecture_quality.cpp), reused from the preceding
study's `quality-v2` executable. Audits run outside solver timing. For the tank, the expected depth
uses actual mass and tank area, independently of measured kernel density.

Local checks:

```sh
python3 -m unittest tests.performance.test_physical_accuracy \
  tests.performance.test_architecture_quality.DensityOracleTests -v
```

All nine passed. To regenerate figures, extract the retained archive into a disposable directory
and run the plotting script with this evidence directory and its extracted `states` directory:

```text
uv run tools/performance/physical_plot.py EVIDENCE_DIRECTORY STATES_DIRECTORY
```

No full Rust suite, fresh effects-enabled accuracy campaign, new backend comparison, device
memcheck or hosted verification was performed. `SHA256SUMS` covers this retained package, not
the lost full archive or the earlier architecture evidence package.
