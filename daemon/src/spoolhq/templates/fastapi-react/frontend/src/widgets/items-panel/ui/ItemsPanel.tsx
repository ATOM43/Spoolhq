import { useEffect, useState } from "react";

import { type Item, ItemList, listItems } from "@/entities/item";
import { CreateItemForm } from "@/features/create-item";

/** The item list with the form that adds to it. */
export function ItemsPanel() {
  const [items, setItems] = useState<Item[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listItems().then(setItems, (reason: unknown) => {
      setError(String(reason));
    });
  }, []);

  return (
    <section>
      <CreateItemForm
        onCreated={(item) => {
          setItems((current) => [...(current ?? []), item]);
        }}
      />
      {error !== null && <p role="alert">{error}</p>}
      {items === null ? <p>Loading…</p> : <ItemList items={items} />}
    </section>
  );
}
