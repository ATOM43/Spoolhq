import { FileText, ListTodo, Play } from "lucide-react";
import { useParams } from "react-router";

import {
  EmptyState,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/shared/ui";

export function ProjectPanelPage() {
  const { id = "" } = useParams();

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6 px-6 py-8">
      <h1 className="text-2xl font-semibold tracking-tight">
        Project <span className="font-mono">{id}</span>
      </h1>
      <Tabs defaultValue="spec">
        <TabsList>
          <TabsTrigger value="spec">Spec</TabsTrigger>
          <TabsTrigger value="tickets">Tickets</TabsTrigger>
          <TabsTrigger value="run">Run</TabsTrigger>
        </TabsList>
        <TabsContent value="spec">
          <EmptyState
            icon={<FileText aria-hidden />}
            title="No spec yet"
            description="The project's spec will appear here."
          />
        </TabsContent>
        <TabsContent value="tickets">
          <EmptyState
            icon={<ListTodo aria-hidden />}
            title="No tickets yet"
            description="Tickets planned from the spec will appear here."
          />
        </TabsContent>
        <TabsContent value="run">
          <EmptyState
            icon={<Play aria-hidden />}
            title="Nothing running"
            description="Runs of the coding agent will appear here."
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}
