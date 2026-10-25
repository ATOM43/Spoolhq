export interface Item {
  id: number;
  name: string;
  description: string;
}

export interface NewItem {
  name: string;
  description?: string;
}
