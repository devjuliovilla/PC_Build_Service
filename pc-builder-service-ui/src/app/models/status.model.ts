export interface StatusResponse {
  components_count: number;
  categories_count: number;
  builds_count: number;
  last_update: string | null;
  scraper_status: string;
  version: string;
}
