export interface Component {
  id: string;
  category: string;
  name: string;
  url: string;
  image_url: string | null;
  specifications: Record<string, string>;
  price: number | null;
  in_stock: boolean | null;
  scraped_at: string | null;
  last_scraped: string | null;
}
