import { request } from "@/shared/api";

import type { Item, NewItem } from "../model/types";

export function listItems(): Promise<Item[]> {
  return request<Item[]>("/api/items");
}

export function getItem(id: number): Promise<Item> {
  return request<Item>(`/api/items/${String(id)}`);
}

export function createItem(item: NewItem): Promise<Item> {
  return request<Item>("/api/items", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(item),
  });
}
