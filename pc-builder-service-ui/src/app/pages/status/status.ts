import { Component, inject, signal } from '@angular/core';
import { JvPageComponent, JvCardComponent, JvSectionComponent, JvButtonComponent } from '@devjuliovilla/jv-ui';
import { StatusService } from '../../services/status.service';
import { StatusResponse } from '../../models/status.model';

@Component({
  selector: 'app-status',
  standalone: true,
  imports: [JvPageComponent, JvCardComponent, JvSectionComponent, JvButtonComponent],
  template: `
    <jv-page title="Estado del Sistema" description="Monitoreo y control del scraper">
      @if (status(); as s) {
        <div class="stats-grid">
          <jv-card>
            <div class="stat">
              <span class="stat-label">API Version</span>
              <span class="stat-value">{{ s.version }}</span>
            </div>
          </jv-card>
          <jv-card>
            <div class="stat">
              <span class="stat-label">Scraper</span>
              <span class="stat-value">{{ s.scraper_status }}</span>
            </div>
          </jv-card>
          <jv-card>
            <div class="stat">
              <span class="stat-label">Última actualización</span>
              <span class="stat-value date">{{ formatDate(s.last_update) }}</span>
            </div>
          </jv-card>
        </div>

        <jv-section title="Acciones">
          <div class="actions">
            <jv-button (click)="updateComponents()" [disabled]="loading()">Actualizar Componentes</jv-button>
            <jv-button (click)="updateChairs()" [disabled]="loading()">Actualizar Sillas</jv-button>
          </div>
        </jv-section>
      }
    </jv-page>
  `,
  styles: [`
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1rem;
      margin-bottom: 1.5rem;
    }
    .stat {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 1.5rem;
      text-align: center;
      gap: 0.25rem;
    }
    .stat-label {
      font-size: 0.75rem;
      opacity: 0.6;
      text-transform: uppercase;
    }
    .stat-value {
      font-size: 1.25rem;
      font-weight: 600;
    }
    .date {
      font-size: 0.875rem;
    }
    .actions {
      display: flex;
      gap: 0.5rem;
    }
  `],
})
export default class StatusPage {
  private statusService = inject(StatusService);

  protected status = signal<StatusResponse | null>(null);
  protected loading = signal(false);

  constructor() {
    this.loadStatus();
  }

  protected formatDate(dateStr: string | null): string {
    if (!dateStr) return '—';
    const d = new Date(dateStr.includes('T') ? dateStr : dateStr.replace(' ', 'T'));
    return d.toLocaleString('es-MX', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  private loadStatus() {
    this.statusService.getStatus().subscribe({
      next: (res) => this.status.set(res),
    });
  }

  updateComponents() {
    this.loading.set(true);
    this.statusService.triggerScraperUpdate().subscribe({
      next: (job) => {
        alert(`Job iniciado: ${job.jobId}`);
        this.loading.set(false);
        this.loadStatus();
      },
      error: () => this.loading.set(false),
    });
  }

  updateChairs() {
    this.loading.set(true);
    this.statusService.triggerChairsUpdate().subscribe({
      next: (job) => {
        alert(`Job iniciado: ${job.jobId}`);
        this.loading.set(false);
        this.loadStatus();
      },
      error: () => this.loading.set(false),
    });
  }
}
