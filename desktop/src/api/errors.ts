/** Every way a daemon call can fail. `kind` is what the UI switches on. */
export type DaemonErrorDetail =
  /** Nothing answered on 127.0.0.1:<port>. */
  | { kind: "not_running"; port: number | null; message: string }
  /** The call needs the token and the token file does not exist (or is empty). */
  | { kind: "token_missing"; tokenPath: string }
  /** The daemon rejected the token (HTTP 401). */
  | { kind: "unauthorized" }
  /** The daemon rejected the request's Host header (HTTP 400). */
  | { kind: "bad_host" }
  /** Any other non-2xx answer. */
  | { kind: "http"; status: number }
  /** The daemon answered 2xx with a body that is not what the client expects. */
  | { kind: "invalid_response"; message: string }
  /** config.toml or SPOOLHQ_PORT is invalid. */
  | { kind: "config"; message: string }
  /** The Tauri bridge failed (for example, the page is not running inside the app). */
  | { kind: "internal"; message: string };

export type DaemonErrorKind = DaemonErrorDetail["kind"];

export class DaemonError extends Error {
  readonly detail: DaemonErrorDetail;

  constructor(detail: DaemonErrorDetail) {
    super(describe(detail));
    this.name = "DaemonError";
    this.detail = detail;
  }

  get kind(): DaemonErrorKind {
    return this.detail.kind;
  }
}

function describe(detail: DaemonErrorDetail): string {
  switch (detail.kind) {
    case "not_running":
      return detail.port === null
        ? "The daemon isn't running."
        : `The daemon isn't running on 127.0.0.1:${String(detail.port)}.`;
    case "token_missing":
      return `The daemon's access token is missing: ${detail.tokenPath} does not exist.`;
    case "unauthorized":
      return "The daemon rejected the access token.";
    case "bad_host":
      return "The daemon rejected the request's Host header.";
    case "http":
      return `The daemon answered with HTTP ${String(detail.status)}.`;
    case "invalid_response":
      return `The daemon sent an unexpected response: ${detail.message}`;
    case "config":
      return detail.message;
    case "internal":
      return `Could not reach the app's backend: ${detail.message}`;
  }
}
