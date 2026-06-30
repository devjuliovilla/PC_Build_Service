import { Component, inject, signal, OnDestroy } from '@angular/core';
import { JvPageComponent, JvCardComponent, JvSectionComponent, JvBadgeComponent, JvButtonComponent, JvLoaderComponent, JvAlertComponent } from '@devjuliovilla/jv-ui';
import { StatusService } from '../../services/status.service';
import { StatusResponse } from '../../models/status.model';

interface ActiveJob {
  jobId: string;
  type: string | null;
  status: string;
  componentsUpdated: number;
  error: string | null;
  duration: number | null;
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [JvPageComponent, JvCardComponent, JvSectionComponent, JvBadgeComponent, JvButtonComponent, JvLoaderComponent, JvAlertComponent],
  template: `
    <jv-page title="Dashboard" description="Resumen del catálogo y control del scraper">
      @if (status(); as s) {
        <div class="stats-grid">
          <jv-card>
            <div class="stat">
              <span class="stat-label">Componentes</span>
              <span class="stat-value">{{ s.components_count }}</span>
            </div>
          </jv-card>
          <jv-card>
            <div class="stat">
              <span class="stat-label">Categorías</span>
              <span class="stat-value">{{ s.categories_count }}</span>
            </div>
          </jv-card>
          <jv-card>
            <div class="stat">
              <span class="stat-label">Builds</span>
              <span class="stat-value">{{ s.builds_count }}</span>
            </div>
          </jv-card>
          <jv-card>
            <div class="stat">
              <span class="stat-label">Scraper</span>
              <jv-badge [tone]="s.scraper_status === 'Idle' ? 'neutral' : 'primary'" class="stat-badge">{{ s.scraper_status }}</jv-badge>
            </div>
          </jv-card>
        </div>
      }

      <jv-section title="Scraper">
        @if (activeJob(); as job) {
          <jv-card>
            <div class="job-card">
              <div class="job-header">
                <span class="job-title">{{ job.type === 'scraper.update' ? 'Componentes' : 'Sillas Gamer' }}</span>
                <jv-badge [tone]="job.status === 'Running' ? 'primary' : job.status === 'Completed' ? 'success' : job.status === 'Failed' ? 'danger' : 'neutral'">{{ job.status }}</jv-badge>
              </div>
              @if (job.status === 'Running') {
                <div class="job-progress">
                  <jv-loader />
                  <span class="job-progress-text">Ejecutando scraper…</span>
                </div>
              }
              @if (job.status === 'Completed') {
                <jv-alert tone="success" title="Completado">
                  {{ job.componentsUpdated }} producto(s) actualizados en {{ job.duration?.toFixed(1) ?? '?' }}s
                </jv-alert>
              }
              @if (job.status === 'Failed') {
                <jv-alert tone="danger" title="Error">
                  {{ job.error ?? 'Falló la ejecución del scraper' }}
                </jv-alert>
              }
            </div>
          </jv-card>
        }

        <div class="scraper-actions">
          <jv-button (click)="runScraper()" [disabled]="activeJob()?.status === 'Running'">Actualizar Componentes</jv-button>
          <jv-button (click)="runChairsScraper()" [disabled]="activeJob()?.status === 'Running'">Actualizar Sillas</jv-button>
        </div>

        @if (status(); as s) {
          <div class="last-update">
            Última actualización: <strong>{{ formatDate(s.last_update) }}</strong>
          </div>
        }
      </jv-section>

      @if (status(); as s) {
        <jv-section title="Versión" [description]="'API v' + s.version" />
      }
    </jv-page>
  `,
  styles: [`
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
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
      letter-spacing: 0.05em;
    }
    .stat-value {
      font-size: 2rem;
      font-weight: 700;
    }
    .stat-badge {
      font-size: 0.875rem;
    }
    .job-card {
      padding: 1rem;
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      margin-bottom: 1rem;
    }
    .job-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .job-title {
      font-weight: 600;
      font-size: 1rem;
    }
    .job-progress {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .job-progress-text {
      font-size: 0.875rem;
      opacity: 0.7;
    }
    .scraper-actions {
      display: flex;
      gap: 0.5rem;
      margin-bottom: 0.75rem;
    }
    .last-update {
      font-size: 0.8rem;
      opacity: 0.6;
    }
  `],
})
export default class DashboardPage implements OnDestroy {
  private statusService = inject(StatusService);

  protected status = signal<StatusResponse | null>(null);
  protected activeJob = signal<ActiveJob | null>(null);

  private pollTimer: ReturnType<typeof setInterval> | null = null;

  constructor() {
    this.loadStatus();
  }

  ngOnDestroy() {
    this.stopPolling();
  }

  private loadStatus() {
    this.statusService.getStatus().subscribe({
      next: (res) => this.status.set(res),
    });
  }

  private startPolling(jobId: string) {
    this.stopPolling();
    this.pollTimer = setInterval(() => {
      this.statusService.getJob(jobId).subscribe({
        next: (res) => {
          this.activeJob.set(res);
          if (res.status === 'Completed' || res.status === 'Failed') {
            this.stopPolling();
            this.loadStatus();
          }
        },
      });
    }, 2000);
  }

  private stopPolling() {
    if (this.pollTimer) {
      clearInterval(this.pollTimer);
      this.pollTimer = null;
    }
  }

  protected runScraper() {
    this.activeJob.set(null);
    this.statusService.triggerScraperUpdate().subscribe({
      next: (job) => {
        this.activeJob.set(job);
        this.startPolling(job.jobId);
      },
    });
  }

  protected formatDate(dateStr: string | null): string {
    if (!dateStr) return 'Nunca';
    const d = new Date(dateStr.includes('T') ? dateStr : dateStr.replace(' ', 'T'));
    return d.toLocaleString('es-MX', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  protected runChairsScraper() {
    this.activeJob.set(null);
    this.statusService.triggerChairsUpdate().subscribe({
      next: (job) => {
        this.activeJob.set(job);
        this.startPolling(job.jobId);
      },
    });
  }
}
