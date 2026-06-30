import { inject, Injectable } from '@angular/core';
import { ApiService } from './api.service';
import { Build, BuildDecision, BuildSlot, BuildSnapshot, BuildComparison, BuildTotal } from '../models/build.model';

@Injectable({ providedIn: 'root' })
export class BuildsService {
  private api = inject(ApiService);

  list() {
    return this.api.get<Build[]>('/builds');
  }

  get(id: number) {
    return this.api.get<Build>(`/builds/${id}`);
  }

  create(name: string, description?: string | null) {
    return this.api.post<Build>('/builds', { name, description });
  }

  update(id: number, body: { name?: string; description?: string; is_active?: boolean }) {
    return this.api.put<Build>(`/builds/${id}`, body);
  }

  delete(id: number) {
    return this.api.delete(`/builds/${id}`);
  }

  // Slots
  createSlot(buildId: number, slot: string, componentId: string, isLocked = false, notes?: string | null) {
    return this.api.post<BuildSlot>(`/builds/${buildId}/slots`, { slot, component_id: componentId, is_locked: isLocked, notes });
  }

  updateSlot(buildId: number, slot: string, componentId: string, isLocked?: boolean, notes?: string | null) {
    return this.api.put<BuildSlot>(`/builds/${buildId}/slots/${slot}`, { component_id: componentId, is_locked: isLocked, notes });
  }

  deleteSlot(buildId: number, slot: string) {
    return this.api.delete(`/builds/${buildId}/slots/${slot}`);
  }

  // Bulk
  bulkSlots(buildId: number, slots: Record<string, string>) {
    return this.api.put<BuildSlot[]>(`/builds/${buildId}/slots/bulk`, { slots });
  }

  // Decisions
  createDecision(buildId: number, slot: string, reason: string) {
    return this.api.post<BuildDecision>(`/builds/${buildId}/slots/${slot}/decisions`, { reason });
  }

  listDecisions(buildId: number, slot: string) {
    return this.api.get<BuildDecision[]>(`/builds/${buildId}/slots/${slot}/decisions`);
  }

  // Snapshot / Compare / Total
  createSnapshot(buildId: number) {
    return this.api.post<BuildSnapshot[]>(`/builds/${buildId}/snapshot`);
  }

  compare(buildId: number) {
    return this.api.get<BuildComparison[]>(`/builds/${buildId}/compare`);
  }

  total(buildId: number) {
    return this.api.get<BuildTotal>(`/builds/${buildId}/total`);
  }
}
