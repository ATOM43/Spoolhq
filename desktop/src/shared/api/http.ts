/**
 * The typed API client, generated from the daemon's OpenAPI schema (`just gen-api`).
 *
 * `openapi-fetch` builds each request; {@link daemonFetch} hands it to the Rust command
 * `daemon_request`, which adds the token, so the token stays out of the webview. A
 * non-2xx answer or a missing daemon rejects with a {@link DaemonError}, as the other
 * daemon calls do; a 412 carries the file's current ETag and content.
 */
import createClient from "openapi-fetch";

import { call, replyError, type DaemonReply } from "./client";
import type { components, paths } from "./schema.gen";

export type Schemas = components["schemas"];

/** Any origin works: only the path and query reach the Rust side. */
const BASE_URL = "http://daemon.invalid";

export async function daemonFetch(request: Request): Promise<Response> {
  const url = new URL(request.url);
  const body = request.body === null ? null : await request.text();
  const reply = await call<DaemonReply>("daemon_request", {
    method: request.method,
    path: url.pathname + url.search,
    body: body === "" ? null : body,
    ifMatch: request.headers.get("If-Match"),
  });
  const error = replyError(reply);
  if (error) {
    throw error;
  }
  const headers = new Headers({ "Content-Type": "application/json" });
  if (reply.etag) {
    headers.set("ETag", reply.etag);
  }
  const empty = reply.status === 204 || reply.body === "";
  return new Response(empty ? null : reply.body, {
    status: reply.status,
    headers,
  });
}

export const api = createClient<paths>({
  baseUrl: BASE_URL,
  fetch: daemonFetch,
});
