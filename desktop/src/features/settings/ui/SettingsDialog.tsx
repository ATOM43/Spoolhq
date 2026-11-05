import { Check, Settings, X } from "lucide-react";
import { useCallback, useState } from "react";

import {
  Button,
  Dialog,
  ReasonButton,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/shared/ui";

import { useOpenRequests, type SettingsTab } from "../model/open";
import { SET_UP_FIRST, useAgentBlocker } from "../model/queries";
import { AccountsTab } from "./AccountsTab";
import { AgentsTab } from "./AgentsTab";
import { AboutTab, GeneralTab } from "./GeneralTab";

export { SET_UP_FIRST };

const TAB_LIST =
  "-mx-6 h-auto w-auto justify-start gap-5 rounded-none border-b bg-transparent px-6 py-0";
const TAB =
  "h-9 flex-none rounded-none border-0 border-b-2 border-transparent px-1 data-[state=active]:border-accent data-[state=active]:bg-transparent data-[state=active]:shadow-none";
const TOOLTIP =
  "pointer-events-none absolute top-full right-0 z-50 mt-1 hidden rounded-md bg-ink px-2 py-1 text-xs font-medium whitespace-nowrap text-surface group-hover:block group-focus-visible:block";

/** The trigger: "Settings" on Home's top bar, a gear in the project panel's header. */
function Trigger({ icon, onOpen }: { icon: boolean; onOpen: () => void }) {
  if (!icon) {
    return (
      <Button variant="outline" onClick={onOpen}>
        <Settings aria-hidden />
        Settings
      </Button>
    );
  }
  return (
    <Button
      variant="ghost"
      size="icon-sm"
      aria-label="Settings"
      className="group relative"
      onClick={onOpen}
    >
      <Settings aria-hidden />
      <span aria-hidden className={TOOLTIP}>
        Settings
      </span>
    </Button>
  );
}

/**
 * D2 · Settings: a button and its dialog, also opened by `openSettings` (the "Open
 * Settings" links). With `firstRun` (Home), it opens by itself on Agents when no
 * backend is ready, and ✕ and Done stay disabled until one is.
 */
export function SettingsDialog({
  firstRun = false,
  icon = false,
}: {
  firstRun?: boolean;
  icon?: boolean;
}) {
  const blocker = useAgentBlocker();
  const [open, setOpen] = useState(false);
  const [tab, setTab] = useState<SettingsTab>("agents");
  const [autoOpened, setAutoOpened] = useState(false);

  const blocking = firstRun && blocker !== null;
  if (blocking && !autoOpened) {
    // Adjusting state while rendering, as React documents: no effect, no flicker.
    setAutoOpened(true);
    setOpen(true);
    setTab("agents");
  }
  useOpenRequests(
    useCallback((asked: SettingsTab) => {
      setTab(asked);
      setOpen(true);
    }, []),
  );
  const close = () => {
    if (!blocking) {
      setOpen(false);
    }
  };
  const reason = blocking ? SET_UP_FIRST : null;

  return (
    <>
      <Trigger
        icon={icon}
        onOpen={() => {
          setOpen(true);
        }}
      />
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
        <div className="absolute top-4 right-4">
          <ReasonButton
            variant="ghost"
            size="icon-sm"
            aria-label="Close"
            reason={reason}
            onClick={close}
          >
            <X aria-hidden />
          </ReasonButton>
        </div>
        <Tabs
          value={tab}
          onValueChange={(value) => {
            setTab(value as SettingsTab);
          }}
          className="-mt-2 gap-0"
        >
          <TabsList className={TAB_LIST}>
            <TabsTrigger value="agents" className={TAB}>
              Agents
            </TabsTrigger>
            <TabsTrigger value="accounts" className={TAB}>
              Accounts
            </TabsTrigger>
            <TabsTrigger value="general" className={TAB}>
              General
            </TabsTrigger>
            <TabsTrigger value="about" className={TAB}>
              About
            </TabsTrigger>
          </TabsList>
          <div className="max-h-[60vh] overflow-y-auto pt-4">
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
        <div className="-mx-6 mt-4 -mb-6 flex items-center justify-between gap-4 border-t px-6 py-3">
          <p className="text-sm text-ink-muted">
            {reason ?? "You can change these any time from Settings"}
          </p>
          <ReasonButton reason={reason} onClick={close}>
            <Check aria-hidden />
            Done
          </ReasonButton>
        </div>
      </Dialog>
    </>
  );
}
