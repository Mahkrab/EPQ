# S033 — OpenBSD Project (n.d.)

## Full reference:

OpenBSD Project (n.d.) ‘ssh_config(5)’, *OpenBSD manual pages*.

#### https://man.openbsd.org/ssh_config

## Relevance:

Provides the client configuration reference for the `AddressFamily`, `KexAlgorithms`, identity, host-key and keepalive settings used to diagnose and stabilise the OpenSSH connection.

## Reliability:

This is the official manual maintained by the OpenBSD developers responsible for OpenSSH. It reflects the current development version, so installed-version manuals should be checked before applying exact defaults.

## Tags

`openssh`, `ssh-config`, `key-exchange`, `keepalive`

## Reading notes

- `AddressFamily` can restrict the client to IPv4 or IPv6.
- `KexAlgorithms` selects the permitted key-exchange algorithms.
- `ServerAliveInterval` and `ServerAliveCountMax` control client keepalive messages.

#### Date added

15/07/26
