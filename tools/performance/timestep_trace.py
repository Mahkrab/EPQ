"""Add scoped CPU ranges to a disposable CUDA source export for Nsight analysis.

These builds deliberately observe the solver and worker. They must stay separate
from ordinary throughput samples; no instrumentation enters production source.
"""
from __future__ import annotations

import argparse
from pathlib import Path


RANGES = '''//! Scoped Nsight ranges for this disposable diagnostic build.
use std::{ffi::{CStr, c_char}, marker::PhantomData, rc::Rc};
unsafe extern "C" {
    fn critical_push(name: *const c_char);
    fn critical_pop();
}
pub(crate) struct Range(PhantomData<Rc<()>>);
impl Range {
    pub(crate) fn new(name: &'static CStr) -> Self {
        // SAFETY: NVTX consumes this permanent NUL-terminated string immediately.
        unsafe { critical_push(name.as_ptr()); }
        Self(PhantomData)
    }
}
impl Drop for Range {
    fn drop(&mut self) {
        // SAFETY: this non-Send guard balances its push on the same host thread.
        unsafe { critical_pop(); }
    }
}
'''


def prepare(root: Path) -> None:
    """Instrument only an explicit non-Git export, failing on source drift."""
    if (root / ".git").exists() or not (root / "native/bridge.cpp").is_file():
        raise ValueError("require a disposable Maelstrom source export without .git")
    if (root / "src/critical_trace.rs").exists():
        raise ValueError("diagnostic ranges already installed")
    changes: dict[Path, str] = {}

    def edit(relative: str, old: str, new: str) -> None:
        path = root / relative
        source = changes.get(path, path.read_text(encoding="utf-8"))
        if source.count(old) != 1:
            raise ValueError(f"expected one insertion in {relative}: {old!r}")
        changes[path] = source.replace(old, new)

    edit("src/lib.rs", "mod validation;", "mod validation;\nmod critical_trace;")
    edit("native/bridge.cpp", '#include "probe.h"', '''#include "probe.h"
#include <nvtx3/nvToolsExt.h>
extern "C" void critical_push(const char *name) { nvtxRangePushA(name); }
extern "C" void critical_pop() { nvtxRangePop(); }''')
    edit("src/simulation/mod.rs", '''        check_cancellation(cancelled)?;
        validate_particles(&self.accepted.particles)?;''', '''        let _step = crate::critical_trace::Range::new(c"complete timestep");
        check_cancellation(cancelled)?;
        let input = crate::critical_trace::Range::new(c"host input validation");
        validate_particles(&self.accepted.particles)?;
        drop(input);''')
    edit("src/simulation/mod.rs", "            validate_particles(&particles)?;", '''            let output = crate::critical_trace::Range::new(c"host output validation");
            validate_particles(&particles)?;''')
    # The output variable above shadows CudaStepOutput, so use a distinct guard.
    path = root / "src/simulation/mod.rs"
    changes[path] = changes[path].replace("let output = crate::critical_trace", "let output_range = crate::critical_trace")
    edit("src/simulation/mod.rs", "            cuda.accept()?;", '''            drop(output_range);
            let _accept = crate::critical_trace::Range::new(c"accepted state publication");
            cuda.accept()?;''')
    edit("src/cuda/solver.rs", "        let mut s = settings(configuration, particles.len(), planes.len())?;", '''        let _cuda = crate::critical_trace::Range::new(c"CUDA step");
        let mut s = settings(configuration, particles.len(), planes.len())?;''')
    edit("src/cuda/solver.rs", "        let positions: Vec<[f32; 3]> = self.context.inner.download(2, particles.len())?;", '''        let readback = crate::critical_trace::Range::new(c"final vector readback");
        let positions: Vec<[f32; 3]> = self.context.inner.download(2, particles.len())?;''')
    edit("src/cuda/solver.rs", "        let output = host_values(particles.iter().zip(positions).zip(velocities).map(", '''        drop(readback);
        let _materialise = crate::critical_trace::Range::new(c"particle materialisation");
        let output = host_values(particles.iter().zip(positions).zip(velocities).map(''')
    edit("src/cuda/solver.rs", "    fn group(&mut self, s: Settings, first_operation: u32) -> Result<(), StepError> {", '''    fn group(&mut self, s: Settings, first_operation: u32) -> Result<(), StepError> {
        let _group = crate::critical_trace::Range::new(if first_operation == 5 { c"Jacobi group" } else { c"projection group" });''')
    edit("src/application/worker.rs", "                let copy_start = Instant::now();", '''                let observation = crate::critical_trace::Range::new(c"worker observation publication");
                let copy_start = Instant::now();''')
    edit("src/application/worker.rs", "                if let Some((trace, at)) = self.acceptance_trace.as_mut().zip(accepted_at) {", '''                drop(observation);
                if let Some((trace, at)) = self.acceptance_trace.as_mut().zip(accepted_at) {''')
    for path, source in changes.items():
        path.write_text(source, encoding="utf-8")
    (root / "src/critical_trace.rs").write_text(RANGES, encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    try:
        prepare(args.source.resolve())
    except (OSError, ValueError) as error:
        parser.exit(1, f"timestep trace: {error}\n")
