# S016 — Tailscale Inc. (2025)

## Full reference:

Tailscale Inc. (2025) ‘What is Tailscale?’, *Tailscale Docs*.

#### https://tailscale.com/docs/concepts/what-is-tailscale

## Relevance:

Provides technical background for describing Tailscale as a secure, identity-based mesh network used to connect development devices across different physical networks. It also explains its use of WireGuard, direct peer-to-peer connections and encrypted relays.

## Reliability:

This is the official Tailscale documentation and is therefore authoritative about the product’s design and operation. As a vendor-authored source it may emphasise benefits, so claims comparing Tailscale with other networking products should be supported independently.

## Tags

`networking`, `tailscale`, `wireguard`, `remote-access`

## Reading notes

- Tailscale creates a private mesh network, called a tailnet, between authenticated devices.
- Connections are end-to-end encrypted using WireGuard and are direct where network conditions allow.
- Relays can carry encrypted traffic when a direct connection cannot be established.

#### Date added

13/07/26
