export interface Build {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  slots: BuildSlot[];
}

export interface BuildSlot {
  id: number;
  build_id: number;
  slot: string;
  component_id: string;
  component_name: string;
  component_category: string;
  is_locked: boolean;
  notes: string | null;
  selected_at: string;
}

export interface BuildDecision {
  id: number;
  build_slot_id: number;
  reason: string;
  created_at: string;
  slot?: string;
  build_id?: number;
}

export interface BuildSnapshot {
  component_id: string;
  price: number;
  in_stock: boolean;
  scraped_at: string;
}

export interface BuildComparison {
  slot: string;
  component_id: string;
  component_name: string;
  snapshot: { price: number; in_stock: number; scraped_at: string } | null;
  latest: { price: number | null; in_stock: boolean | null; scraped_at: string | null };
  price_delta: number | null;
}

export interface BuildTotal {
  build_id: number;
  total: number;
  currency: string;
  items: BuildTotalItem[];
}

export interface BuildTotalItem {
  slot: string;
  component_id: string;
  component_name: string;
  price: number;
  in_stock: boolean | null;
}
