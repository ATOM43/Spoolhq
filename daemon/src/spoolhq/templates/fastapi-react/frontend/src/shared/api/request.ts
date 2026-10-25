/** A non-2xx response from the backend. */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly body: string,
  ) {
    super(`request failed with status ${String(status)}`);
    this.name = "ApiError";
  }
}

/** `fetch` that parses JSON and throws `ApiError` on a non-2xx status. */
export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  if (!response.ok) throw new ApiError(response.status, await response.text());
  return (await response.json()) as T;
}
