# S024 — Microsoft (2025)

## Full reference:

Microsoft (2025) ‘Accessing network applications with WSL’, *Microsoft Learn*.

#### https://learn.microsoft.com/en-us/windows/wsl/networking

## Relevance:

Directly documents the initial Windows-to-WSL 2 forwarding design, including WSL’s NAT networking, changing instance IP addresses, `netsh interface portproxy`, IPv4/IPv6 and firewall considerations.

## Reliability:

Microsoft develops WSL and publishes Microsoft Learn, so this is an authoritative primary source for WSL networking behaviour and supported Windows commands. The page was last updated on 6 August 2025.

## Tags

`wsl2`, `nat`, `portproxy`, `firewall`

## Reading notes

- WSL uses NAT-based networking by default.
- A WSL 2 instance has its own IP address under the default networking mode.
- Windows can forward a host port to WSL with `netsh interface portproxy`.

#### Date added

15/07/26
