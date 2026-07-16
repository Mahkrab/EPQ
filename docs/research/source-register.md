# Source Register

## Fluid simulation and graphics

| ID | Source | Type | Planned use | Link |
|---|---|---|---|---|
| [S001](sources/001-bridson-fluid-simulation-for-computer-graphics.md) | Bridson (2015) | Textbook | Primary practical reference for the continuum-fluid background, grid-based methods, pressure projection, advection, incompressibility and numerical trade-offs in graphics-oriented simulation. | [Official / DOI](https://doi.org/10.1201/9781315266008) |
| [S002](sources/002-stam-stable-fluids.md) | Stam (1999) | Peer-reviewed conference paper | Background comparison source for stable Eulerian, grid-based fluid simulation and the relationship between numerical stability, timestep selection and interactive performance. | [Official / DOI](https://doi.org/10.1145/311535.311548) |
| [S003](sources/003-muller-charypar-gross-particle-based-fluid-simulation.md) | Müller, Charypar and Gross (2003) | Peer-reviewed conference paper | Foundational source for particle-based, Smoothed Particle Hydrodynamics-style fluid simulation and neighbour interactions. | [Official / DOI](https://doi.org/10.5555/846276.846298) |
| [S004](sources/004-macklin-muller-position-based-fluids.md) | Macklin and Müller (2013) | Peer-reviewed journal paper | Core design reference for a position-based fluid constraint solver, density correction, solver iteration count and the trade-off between visual plausibility, stability and speed. | [Official / DOI](https://doi.org/10.1145/2461912.2461984) |
| [S014](sources/014-witkin-particle-system-dynamics.md) | Witkin (1997) | University course notes | Foundational explanation of particle state, phase space, force accumulation and integration structure for interactive physically based simulation. | [Official / PDF](https://www.cs.cmu.edu/~baraff/pbm/particles.pdf) |

## Computational fluid dynamics

| ID | Source | Type | Planned use | Link |
|---|---|---|---|---|
| [S005](sources/005-ferziger-peric-street-computational-methods-for-fluid-dynamics.md) | Ferziger, Perić and Street (2020) | Advanced textbook | Theoretical reference for numerical discretisation, error, stability, convergence, boundary conditions and validation language in the report. | [Official / DOI](https://doi.org/10.1007/978-3-319-99693-6) |
| [S006](sources/006-versteeg-malalasekera-introduction-to-cfd.md) | Versteeg and Malalasekera (2007) | Textbook | Supporting background source for continuum governing equations, finite-volume concepts and the distinction between grid-based engineering CFD and Maelstrom’s particle-focused simulation. | [Official / DOI](https://books.google.com/books?id=RvBZ-UMpGzIC) |
| [S007](sources/007-nasa-glenn-navier-stokes-equation.md) | NASA Glenn Research Center (2024) | Official educational web resource | Plain-language introductory explanation of the variables represented in the three-dimensional unsteady Navier–Stokes equations. | [Official / DOI](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/navier-strokes-equation/) |

## Collisions and physics simulation

| ID | Source | Type | Planned use | Link |
|---|---|---|---|---|
| [S008](sources/008-ericson-real-time-collision-detection.md) | Ericson (2005) | Professional technical textbook | Practical reference for broad-phase versus narrow-phase collision detection, bounding volumes, robustness and real-time algorithm choices. | [Official / DOI](https://realtimecollisiondetection.net/) |
| [S009](sources/009-gilbert-johnson-keerthi-gjk.md) | Gilbert, Johnson and Keerthi (1988) | Peer-reviewed journal paper | Theoretical source for GJK distance and intersection queries between convex objects; useful as future collision-system context. | [Official / DOI](https://doi.org/10.1109/56.2083) |
| [S010](sources/010-baraff-non-penetrating-rigid-bodies.md) | Baraff (1989) | Peer-reviewed conference paper | Theoretical background for non-penetration constraints, rigid-body contact and the limitations of simple collision responses. | [Official / DOI](https://doi.org/10.1145/74334.74356) |

## Implementations and tools

| ID | Source | Type | Planned use | Link |
|---|---|---|---|---|
| [S011](sources/011-openfoam-v2606-user-guide.md) | OpenCFD (2026) | Official software documentation | Industry context and comparison point for case setup, mesh-based CFD workflows, parallel execution and validation expectations. | [Official / DOI](https://www.openfoam.com/documentation/user-guide) |
| [S012](sources/012-nvidia-cuda-programming-guide-release-13-2.md) | NVIDIA (2026) | Official technical documentation | Primary implementation reference for CUDA’s execution model, memory hierarchy, kernel launches, synchronisation and host–device data management. | [Official / DOI](https://docs.nvidia.com/cuda/archive/13.2.0/pdf/CUDA_C_Programming_Guide.pdf) |
| [S013](sources/013-macklin-muller-chentanez-kim-unified-particle-physics.md) | Macklin et al. (2014) | Peer-reviewed journal paper | Design and industry-context source for unified particle representations, position-based constraints, collisions and GPU-parallel real-time simulation. | [Official / DOI](https://doi.org/10.1145/2601097.2601152) |

## Documentation standards

| ID | Source | Type | Planned use | Link |
|---|---|---|---|---|
| [S015](sources/015-wikipedia-iso-8601.md) | Wikipedia contributors (2026) | Online encyclopedia article | Supporting reference for using ISO 8601-style year-week labels to classify weekly logbook entries consistently. | [Web article](https://en.wikipedia.org/wiki/ISO_8601) |

## Networking and remote access

| ID | Source | Type | Planned use | Link |
|---|---|---|---|---|
| [S016](sources/016-tailscale-what-is-tailscale.md) | Tailscale Inc. (2025) | Official software documentation | Technical background for explaining the secure private network used to connect development devices remotely. | [Official documentation](https://tailscale.com/docs/concepts/what-is-tailscale) |
| [S017](sources/017-cloudflare-what-is-ssh.md) | Cloudflare Inc. (n.d.) | Technical educational web resource | Introductory explanation of encrypted remote command-line access, authentication and SSH tunnelling. | [Web article](https://www.cloudflare.com/learning/security/what-is-ssh/) |
| [S018](sources/018-openbsd-openssh.md) | OpenBSD Project (n.d.) | Official software documentation | Primary product reference for the OpenSSH client, server, authentication and tunnelling tools used in the remote-development setup. | [Official website](https://www.openssh.org/) |
| [S021](sources/021-cloudflare-what-is-a-lan.md) | Cloudflare Inc. (n.d.) | Technical educational web resource | Introductory reference for LANs, home routers and Wi-Fi connectivity. | [Web article](https://www.cloudflare.com/en-gb/learning/network-layer/what-is-a-lan/) |
| [S022](sources/022-cloudflare-computer-ports.md) | Cloudflare Inc. (n.d.) | Technical educational web resource | Explanation of TCP ports, firewalls and SSH’s conventional use of port 22. | [Web article](https://www.cloudflare.com/en-gb/learning/network-layer/what-is-a-computer-port/) |
| [S023](sources/023-microsoft-dhcp-basics.md) | Microsoft (2022) | Official technical documentation | Background for DHCP assignment and changes to a device’s LAN IP address. | [Official documentation](https://learn.microsoft.com/en-us/windows-server/troubleshoot/dynamic-host-configuration-protocol-basics) |
| [S024](sources/024-microsoft-wsl-networking.md) | Microsoft (2025) | Official software documentation | Primary reference for WSL NAT, instance addresses, Windows port proxying and firewall behaviour. | [Official documentation](https://learn.microsoft.com/en-us/windows/wsl/networking) |
| [S028](sources/028-openbsd-sshd-config.md) | OpenBSD Project (n.d.) | Official manual page | Configuration reference for OpenSSH authentication, keys, negotiation and forwarding. | [Official manual](https://man.openbsd.org/sshd_config) |
| [S029](sources/029-cloudflare-ip-addresses.md) | Cloudflare Inc. (n.d.) | Technical educational web resource | Introductory reference for IP addresses, IPv4, IPv6 and dynamic addressing. | [Web article](https://www.cloudflare.com/learning/dns/glossary/what-is-my-ip-address/) |
| [S030](sources/030-cloudflare-brute-force-attacks.md) | Cloudflare Inc. (n.d.) | Technical educational web resource | Security background for brute-force password attacks against SSH logins. | [Web article](https://www.cloudflare.com/learning/bots/brute-force-attack/) |
| [S032](sources/032-rfc-2923-path-mtu-discovery.md) | Lahey (2000) | IETF informational RFC | Technical basis for identifying a Path MTU Discovery black hole when established TCP sessions hang on larger packets. | [RFC Editor](https://www.rfc-editor.org/info/rfc2923/) |
| [S033](sources/033-openbsd-ssh-config.md) | OpenBSD Project (n.d.) | Official manual page | Client configuration reference for address-family selection, key exchange, identities, host keys and keepalives. | [Official manual](https://man.openbsd.org/ssh_config) |
| [S034](sources/034-openssh-release-notes.md) | OpenSSH Project (2026) | Official release notes | Primary reference for OpenSSH post-quantum key exchange and the `sntrup761` algorithm observed during negotiation. | [Official release notes](https://www.openssh.org/releasenotes.html) |
| [S035](sources/035-tailscale-acls.md) | Tailscale Inc. (2026) | Official software documentation | Product reference for checking whether Tailscale ACLs permit the intended connection. | [Official documentation](https://tailscale.com/docs/features/access-control/acls) |
| [S036](sources/036-tailscale-cli.md) | Tailscale Inc. (2026) | Official software documentation | Command reference for the `tailscale status` and `tailscale ping` diagnostic tests. | [Official documentation](https://tailscale.com/docs/reference/tailscale-cli) |
| [S037](sources/037-proton-vpn-split-tunneling.md) | Proton AG (n.d.) | Official software documentation | Product reference for Proton VPN application and IP-address split-tunnelling rules. | [Official documentation](https://protonvpn.com/support/protonvpn-split-tunneling) |
| [S038](sources/038-cloudflare-what-is-dns.md) | Cloudflare Inc. (n.d.) | Technical educational web resource | Introductory explanation of DNS lookups and their role in locating named services. | [Web article](https://www.cloudflare.com/learning/dns/what-is-dns/) |
| [S039](sources/039-cloudflare-what-is-tls.md) | Cloudflare Inc. (n.d.) | Technical educational web resource | Introductory explanation of TLS, service authentication and certificates. | [Web article](https://www.cloudflare.com/learning/ssl/transport-layer-security-tls/) |
| [S040](sources/040-rfc-8731-curve25519-ssh.md) | Adamantiadis, Josefsson and Baushke (2020) | IETF Standards Track RFC | Primary specification for Curve25519 key exchange in SSH. | [RFC Editor](https://www.rfc-editor.org/info/rfc8731/) |
| [S041](sources/041-rfc-8709-ed25519-ssh.md) | Harris and Velvindron (2020) | IETF Standards Track RFC | Primary specification for Ed25519 public-key authentication in SSH. | [RFC Editor](https://www.rfc-editor.org/info/rfc8709/) |
| [S042](sources/042-tailscale-magicdns.md) | Tailscale Inc. (2026) | Official software documentation | Product reference for using stable machine names instead of literal Tailscale IP addresses. | [Official documentation](https://tailscale.com/docs/features/magicdns) |

## Development environment

| ID | Source | Type | Planned use | Link |
|---|---|---|---|---|
| [S019](sources/019-microsoft-what-is-wsl.md) | Microsoft (2025) | Official software documentation | Architectural background for the WSL 2 virtualised Linux environment hosted on the Windows development computer. | [Official documentation](https://learn.microsoft.com/en-us/windows/wsl/about) |
| [S020](sources/020-canonical-ubuntu-on-wsl.md) | Canonical Ltd. (2026) | Official software documentation | Supporting reference for Ubuntu as the Linux distribution used for development and remote access within WSL 2. | [Official documentation](https://documentation.ubuntu.com/wsl/latest/) |
| [S025](sources/025-microsoft-vscode-remote-ssh.md) | Microsoft (2026) | Official software documentation | Primary reference for VS Code Remote-SSH and reusable SSH host configuration. | [Official documentation](https://code.visualstudio.com/docs/remote/ssh) |
| [S026](sources/026-microsoft-what-is-powershell.md) | Microsoft (2025) | Official software documentation | Introductory reference for PowerShell as a command-line shell and automation tool. | [Official documentation](https://learn.microsoft.com/en-us/powershell/scripting/overview?view=powershell-7.5) |
| [S027](sources/027-raspberry-pi-about.md) | Raspberry Pi Ltd. (n.d.) | Official product website | Product context for the Raspberry Pi used in the first local SSH test. | [Official website](https://www.raspberrypi.com/about/) |
| [S031](sources/031-microsoft-windows-documentation.md) | Microsoft (n.d.) | Official software documentation | Official documentation entry point for the Windows host platform. | [Official documentation](https://learn.microsoft.com/en-us/windows/) |
