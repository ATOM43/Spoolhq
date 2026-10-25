import { type SubmitEvent, useState } from "react";

import { createItem, type Item } from "@/entities/item";

interface Props {
  onCreated: (item: Item) => void;
}

/** A name field and an Add button that creates an item through the API. */
export function CreateItemForm({ onCreated }: Props) {
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function submit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      onCreated(await createItem({ name: name.trim() }));
      setName("");
    } catch (reason) {
      setError(String(reason));
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={(event) => void submit(event)}>
      <label>
        Name{" "}
        <input
          value={name}
          onChange={(event) => {
            setName(event.target.value);
          }}
        />
      </label>{" "}
      <button type="submit" disabled={saving || name.trim() === ""}>
        Add
      </button>
      {error !== null && <p role="alert">{error}</p>}
    </form>
  );
}
