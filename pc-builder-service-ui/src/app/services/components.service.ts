import { inject, Injectable } from '@angular/core';
import { ApiService } from './api.service';
import { Component } from '../models/component.model';
import { Category } from '../models/category.model';
import { PriceRecord } from '../models/price-history.model';

@Injectable({ providedIn: 'root' })
export class ComponentsService {
  private api = inject(ApiService);

  list(category?: string, onlyInStock = false, limit = 9999) {
    const params = new URLSearchParams();
    if (category) params.set('category', category);
    if (onlyInStock) params.set('only_in_stock', 'true');
    params.set('limit', String(limit));
    return this.api.get<Component[]>(`/components?${params}`);
  }

  search(query: string, limit = 100) {
    const params = new URLSearchParams({ q: query, limit: String(limit) });
    return this.api.get<Component[]>(`/components/search?${params}`);
  }

  latest(onlyInStock = false, limit = 100) {
    const params = new URLSearchParams();
    if (onlyInStock) params.set('only_in_stock', 'true');
    params.set('limit', String(limit));
    return this.api.get<Component[]>(`/components/latest?${params}`);
  }

  byCategory(category: string, limit = 9999) {
    const params = new URLSearchParams({ limit: String(limit) });
    return this.api.get<Component[]>(`/components/category/${category}?${params}`);
  }

  get(id: string) {
    return this.api.get<Component>(`/components/${id}`);
  }

  getPriceHistory(componentId: string) {
    return this.api.get<PriceRecord[]>(`/price-history/${componentId}`);
  }

  getCategories() {
    return this.api.get<Category[]>('/categories');
  }
}
