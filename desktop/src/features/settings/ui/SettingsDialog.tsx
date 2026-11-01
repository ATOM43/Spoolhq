import { Settings } from "lucide-react";
import { useState } from "react";

import { useAgents } from "@/entities/agent";
import {
  Button,
  Dialog,
  ReasonButton,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/shared/ui";

import { backendReady, useDaemonSettings } from "../model/queries";
import { AccountsTab } from "./AccountsTab";
import { AgentsTab } from "./AgentsTab";
import { AboutTab, GeneralTab } from "./GeneralTab";

export const SET_UP_FIRST =
  "Set up an agent first: log in to a coding CLI or add an API key";

/**
 * D2 · Settings: a button and its dialog. With `firstRun` (Home), it opens by itself
 * on Agents when no backend is ready, and can't be closed until one is.
 */
export function SettingsDialog({ firstRun = false }: { firstRun?: boolean }) {
  const agents = useAgents();
  const settings = useDaemonSettings();
  const [open, setOpen] = useState(false);
  const [tab, setTab] = useState("agents");
  const [autoOpened, setAutoOpened] = useState(false);

  const known = agents.isSuccess && settings.isSuccess;
  const ready = backendReady(agents.data, settings.data);
  const blocking = firstRun && known && !ready;
  if (blocking && !autoOpened) {
    // Adjusting state while rendering, as React documents: no effect, no flicker.
    setAutoOpened(true);
    setOpen(true);
    setTab("agents");
  }
  const close = () => {
    if (!blocking) {
      setOpen(false);
    }
  };

  return (
    <>
      <Button
        variant="outline"
        onClick={() => {
          setOpen(true);
        }}
      >
        <Settings aria-hidden />
        Settings
      </Button>
      <Dialog
        open={open}
        onClose={close}
        closable={!blocking}
        title="Settings"
        description={
          blocking
            ? "SpoolHQ needs one coding agent: a CLI you're logged into, or an Anthropic API key."
            : undefined
        }
      >
        <Tabs value={tab} onValueChange={setTab}>
          <TabsList>
            <TabsTrigger value="agents">Agents</TabsTrigger>
            <TabsTrigger value="accounts">Accounts</TabsTrigger>
            <TabsTrigger value="general">General</TabsTrigger>
            <TabsTrigger value="about">About</TabsTrigger>
          </TabsList>
          <div className="mt-4 max-h-[60vh] overflow-y-auto">
            <TabsContent value="agents">
              <AgentsTab />
            </TabsContent>
            <TabsContent value="accounts">
              <AccountsTab />
            </TabsContent>
            <TabsContent value="general">
              <GeneralTab />
            </TabsContent>
            <TabsContent value="about">
              <AboutTab />
            </TabsContent>
          </div>
        </Tabs>
        <div className="mt-6 flex justify-end">
          <ReasonButton reason={blocking ? SET_UP_FIRST : null} onClick={close}>
            Close
          </ReasonButton>
        </div>
      </Dialog>
    </>
  );
}
