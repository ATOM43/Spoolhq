import { Button } from "@/shared/ui";

import { openSettings } from "../model/open";
import { SET_UP_FIRST } from "../model/queries";

/** The "Open Settings" link that goes with a SET_UP_FIRST reason; nothing for others. */
export function OpenSettingsLink({ reason }: { reason: string | null }) {
  if (reason !== SET_UP_FIRST) {
    return null;
  }
  return (
    <Button
      variant="link"
      size="sm"
      className="px-0"
      onClick={() => {
        openSettings("agents");
      }}
    >
      Open Settings
    </Button>
  );
}
