import { useQuery } from "@tanstack/react-query";

import { api, body, queryKeys, type Schemas } from "@/shared/api";

export type Agents = Schemas["AgentsView"];

/** The coding-agent backends the daemon found, as `spool agents` shows them. */
export function useAgents() {
  return useQuery({
    queryKey: queryKeys.agents,
    queryFn: () => body(api.GET("/api/agents")),
    retry: false,
  });
}
