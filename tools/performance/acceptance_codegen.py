"""Resolve direct and relocated calls to the checked plane helper.

Linux position-independent Rust binaries can call through a relative ELF slot,
so searching disassembly for a named call alone misses real call boundaries.
"""

import re


def inspect(assembly: str, relocations: str) -> dict:
    """Return plane-helper call sites, including indirect relative relocations."""
    headers = {}
    for line in assembly.splitlines():
        match = re.match(r"^([0-9a-f]+) <(.+)>:$", line)
        if match:
            headers[int(match[1], 16)] = match[2]
    targets = {address for address, name in headers.items() if name.endswith("::Plane::contains")}
    slots = set()
    for line in relocations.splitlines():
        fields = line.split()
        if "R_X86_64_RELATIVE" in fields:
            if int(fields[-1], 16) in targets:
                slots.add(int(fields[0], 16))
    sites = []
    caller = ""
    for line in assembly.splitlines():
        match = re.match(r"^[0-9a-f]+ <(.+)>:$", line)
        if match:
            caller = match[1]
        if not re.search(r"\bcallq?\s", line):
            continue
        indirect = re.search(r"#\s*([0-9a-f]+)", line)
        if "::Plane::contains>" in line or (indirect and int(indirect[1], 16) in slots):
            sites.append({"caller": caller, "instruction": line.strip()})
    return {"all_contains_call_sites": sites,
            "acceptance_contains_call_sites": [site for site in sites if "::Simulation::step" in site["caller"]],
            "relative_slots_resolved": len(slots)}
