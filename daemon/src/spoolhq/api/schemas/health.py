from typing import Literal

from pydantic import BaseModel


class Health(BaseModel):
    status: Literal["ok"] = "ok"
    service: Literal["spoolhq"] = "spoolhq"
    """Tells SpoolHQ apart from another program answering on the port (the desktop app)."""
