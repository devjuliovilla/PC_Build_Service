import { inject, Injectable } from '@angular/core';
import { ApiService } from './api.service';
import { Chair } from '../models/chair.model';
import { PriceRecord } from '../models/price-history.model';

@Injectable({ providedIn: 'root' })
export class ChairsService {
  private api = inject(ApiService);

  list(onlyInStock = false, limit = 9999) {
    const params = new URLSearchParams();
    if (onlyInStock) params.set('only_in_stock', 'true');
    params.set('limit', String(limit));
    return this.api.get<Chair[]>(`/chairs?${params}`);
  }

  search(query: string, limit = 100) {
    const params = new URLSearchParams({ q: query, limit: String(limit) });
    return this.api.get<Chair[]>(`/chairs/search?${params}`);
  }

  latest(onlyInStock = false, limit = 100) {
    const params = new URLSearchParams();
    if (onlyInStock) params.set('only_in_stock', 'true');
    params.set('limit', String(limit));
    return this.api.get<Chair[]>(`/chairs/latest?${params}`);
  }

  get(id: string) {
    return this.api.get<Chair>(`/chairs/${id}`);
  }

  getPriceHistory(chairId: string) {
    return this.api.get<PriceRecord[]>(`/chair-price-history/${chairId}`);
  }
}
