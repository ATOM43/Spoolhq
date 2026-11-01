# @spoolhq/desktop

The SpoolHQ desktop app: Tauri 2 (`src-tauri/`, Rust) around a React + Vite UI (`src/`). Prerequisites and how to run it are in the repository [README](../README.md#run-the-desktop-app).

- `src/` follows Feature-Sliced Design; see [docs/architecture.md](../docs/architecture.md) for the layers and rules.
- `src/shared/api/` — typed daemon client. Every call goes through the Rust commands `daemon_info`, `daemon_get` and `daemon_request`, which add the token; failures are `DaemonError`s. Live run events come through `events_subscribe`.
- `src/features/daemon-status/` — the 3-second status poll behind the top-bar pill and Home.
- `src/shared/ui/` — shadcn/ui components, restyled with the design tokens in `src/shared/styles/tokens.css`.
- `src-tauri/src/daemon.rs` — reading the port and token, and the only HTTP the app does.
- `src-tauri/src/events.rs` — the daemon's event WebSocket, forwarded to the webview over a Tauri channel.

```sh
pnpm install
pnpm tauri dev     # Vite dev server + app window (start the daemon separately)
pnpm test
pnpm lint
```
