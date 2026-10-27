"""Add disjoint host clocks to an isolated solver export, retaining its call order.

Anchors fail closed when the implementation changes. The normal source tree is
never a target; collection uses a separately hashed diagnostic export.
"""

HEAD = '''        let _coord_enabled = self.coordination_probe;
        let _coord_now = || _coord_enabled.then(std::time::Instant::now);
        let _coord_seconds = |start: Option<std::time::Instant>| {
            start.map_or(0.0, |value| value.elapsed().as_secs_f64())
        };
'''
TICK = '        let _coord_clock = _coord_now();\n'


def instrument(source: str) -> str:
    """Return a diagnostic-only Rust overlay or reject a mismatching source."""
    if "coordination_probe:" in source:
        raise ValueError("solver is already instrumented")
    def replace(old: str, new: str) -> None:
        nonlocal source
        if source.count(old) != 1:
            raise ValueError("coordination overlay anchor changed: " + old.splitlines()[0])
        source = source.replace(old, new, 1)

    replace('    neighbour_capacity: usize,', '    neighbour_capacity: usize,\n    coordination_probe: bool,\n    coordination_step: u64,')
    replace('            neighbour_capacity: 0,', '''            neighbour_capacity: 0,
            coordination_probe: std::env::var_os("MAELSTROM_COORDINATION_PROBE").is_some(),
            coordination_step: 0,''')
    replace('        for (slot, size) in storage_sizes(s)?.into_iter().enumerate() {',
            HEAD + TICK + '        for (slot, size) in storage_sizes(s)?.into_iter().enumerate() {')
    replace('''            self.context.inner.reserve(slot as u32, size)?;
        }
        let positions''', '''            self.context.inner.reserve(slot as u32, size)?;
        }
        let _coord_reserve = _coord_seconds(_coord_clock);
''' + TICK + '        let positions')
    replace('''        self.context.inner.upload(0, &positions)?;''',
            '        let _coord_pack = _coord_seconds(_coord_clock);\n' + TICK + '        self.context.inner.upload(0, &positions)?;')
    replace('''        self.context.inner.begin_attempt()
    }''', '''        self.context.inner.begin_attempt()?;
        let _coord_upload = _coord_seconds(_coord_clock);
        if _coord_enabled {
            eprintln!("COORD_PREP,{},{},{:.9},{:.9},{:.9}", s.count, self.coordination_step, _coord_reserve, _coord_pack, _coord_upload);
        }
        Ok(())
    }''')

    replace('''        s.entries = 0;
        if s.count == 0''', HEAD + TICK + '''        s.entries = 0;
        if s.count == 0''')
    replace('        self.operation(*s, 2)?;',
            '        let _coord_bounds = _coord_seconds(_coord_clock);\n        self.operation(*s, 2)?;')
    replace('''        let mut offsets: Vec<u64> = self.context.inner.download(13, s.count as usize + 1)?;
        s.entries = prefix_offsets(&mut offsets, s.count)?;''', TICK + '''        let mut offsets: Vec<u64> = self.context.inner.download(13, s.count as usize + 1)?;
        let _coord_counts_download = _coord_seconds(_coord_clock);
''' + TICK + '''        s.entries = prefix_offsets(&mut offsets, s.count)?;
        let _coord_prefix = _coord_seconds(_coord_clock);
''' + TICK)
    replace('''        self.context.inner.upload(13, &offsets)?;
        self.operation(*s, 12)''', '''        let _coord_reserve = _coord_seconds(_coord_clock);
''' + TICK + '''        self.context.inner.upload(13, &offsets)?;
        let _coord_upload = _coord_seconds(_coord_clock);
        self.operation(*s, 12)?;
        if _coord_enabled {
            eprintln!("COORD_ROWS,{},{},{:.9},{:.9},{:.9},{:.9},{:.9}", s.count, self.coordination_step, _coord_bounds, _coord_counts_download, _coord_prefix, _coord_reserve, _coord_upload);
        }
        Ok(())''')

    replace('''        let mut s = settings(configuration, particles.len(), planes.len())?;''',
            HEAD + '''        if _coord_enabled {
            self.coordination_step = self.coordination_step.checked_add(1).ok_or(CudaError::Capacity)?;
        }
        let mut s = settings(configuration, particles.len(), planes.len())?;''')
    replace('''        let velocities = host_values(
            self.context
                .inner
                .download(3, particles.len())?
                .into_iter()
                .map(vector),
        )?;''', TICK + '''        let _coord_raw = self.context.inner.download(3, particles.len())?;
        let _coord_cfl_download = _coord_seconds(_coord_clock);
''' + TICK + '''        let velocities = host_values(_coord_raw.into_iter().map(vector))?;
        let _coord_cfl_repack = _coord_seconds(_coord_clock);
''' + TICK)
    replace('''        check_cancellation(cancelled)?;
        clock.mark(Stage::ValidationAndAcceleration);''', '''        let _coord_cfl = _coord_seconds(_coord_clock);
        check_cancellation(cancelled)?;
        clock.mark(Stage::ValidationAndAcceleration);''')
    replace('''        let positions = host_values(
            self.context
                .inner
                .download(2, particles.len())?
                .into_iter()
                .map(vector),
        )?;''', TICK + '''        let _coord_raw = self.context.inner.download(2, particles.len())?;
        let _coord_prediction_download = _coord_seconds(_coord_clock);
''' + TICK + '''        let positions = host_values(_coord_raw.into_iter().map(vector))?;
        let _coord_prediction_repack = _coord_seconds(_coord_clock);''')
    replace('''        Ok((output, cfl))''', '''        if _coord_enabled {
            eprintln!("COORD_STEP,{},{},{:.9},{:.9},{:.9},{:.9},{:.9}", particles.len(), self.coordination_step, _coord_cfl_download, _coord_cfl_repack, _coord_cfl, _coord_prediction_download, _coord_prediction_repack);
        }
        Ok((output, cfl))''')
    return source
