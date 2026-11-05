/** "github.com" for https://github.com/a/b.git or git@github.com:a/b.git. */
export function remoteHost(remote: string): string {
  try {
    return new URL(remote).host || remote;
  } catch {
    return /@([^:/]+)[:/]/.exec(remote)?.[1] ?? remote;
  }
}
