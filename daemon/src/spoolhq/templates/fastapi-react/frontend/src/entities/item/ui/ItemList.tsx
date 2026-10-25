import type { Item } from "../model/types";

export function ItemList({ items }: { items: Item[] }) {
  if (items.length === 0) return <p>No items yet.</p>;
  return (
    <ul>
      {items.map((item) => (
        <li key={item.id}>{item.name}</li>
      ))}
    </ul>
  );
}
