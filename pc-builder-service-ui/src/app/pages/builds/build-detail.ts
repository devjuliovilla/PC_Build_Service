import { Component, inject, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { DatePipe } from '@angular/common';
import { JvPageComponent, JvCardComponent, JvSectionComponent, JvListComponent, JvListItemComponent, JvBadgeComponent, JvButtonComponent, JvIconButtonComponent, JvDialogComponent, JvDialogService, JvInputComponent, JvTextareaComponent, JvToastService, JvBreadcrumbItem } from '@devjuliovilla/jv-ui';
import { BuildsService } from '../../services/builds.service';
import { Build, BuildTotal, BuildComparison, BuildDecision } from '../../models/build.model';

@Component({
  selector: 'app-build-detail',
  standalone: true,
  imports: [JvPageComponent, JvCardComponent, JvSectionComponent, JvListComponent, JvListItemComponent, JvBadgeComponent, JvButtonComponent, JvIconButtonComponent, JvDialogComponent, JvInputComponent, JvTextareaComponent, FormsModule, DatePipe],
  template: `
    <jv-page [title]="build()?.name ?? 'Cargando...'" [breadcrumbs]="breadcrumbs">
      <div page-actions>
        <jv-button variant="primary" (click)="editBuild()">Editar Slots</jv-button>
        <jv-button variant="ghost" (click)="showEditMetaDialog.set(true)">Editar Info</jv-button>
        <jv-button (click)="takeSnapshot()">Tomar Snapshot</jv-button>
        <jv-button variant="outline" (click)="toggleCompare()">{{ showComparison() ? 'Ocultar' : 'Comparar Precios' }}</jv-button>
        <jv-button variant="outline" (click)="exportMarkdown()">Exportar Markdown</jv-button>
      </div>

      @if (build(); as b) {
        <div class="info-row">
          <jv-card>
            <div class="stat">
              <span class="stat-label">Slots</span>
              <span class="stat-value">{{ b.slots.length }}/8</span>
            </div>
          </jv-card>
          <jv-card>
            <div class="stat">
              <span class="stat-label">Total</span>
              <span class="stat-value price">{{ total()?.total != null ? '$' + total()!.total.toLocaleString('es-MX') : '—' }}</span>
            </div>
          </jv-card>
          <jv-card>
            <div class="stat">
              <span class="stat-label">Activo</span>
              <jv-badge [tone]="b.is_active ? 'success' : 'neutral'">{{ b.is_active ? 'Sí' : 'No' }}</jv-badge>
            </div>
          </jv-card>
        </div>

        @if (b.description) {
          <jv-section title="Descripción" [description]="b.description" />
        }

        @if (b.slots.length > 0) {
          <jv-section title="Componentes">
            <jv-list>
              @for (slot of b.slots; track slot.id) {
                <jv-list-item
                  [title]="slot.slot"
                  [description]="slot.component_name + ' (' + slot.component_category + ')'"
                  [leadingIcon]="getSlotIcon(slot.slot)"
                >
                  <jv-badge meta [tone]="slot.is_locked ? 'primary' : 'neutral'">{{ slot.is_locked ? 'Fijo' : 'Libre' }}</jv-badge>
                  <jv-icon-button
                    meta
                    icon="file-text"
                    ariaLabel="Decisiones"
                    variant="ghost"
                    (click)="openDecisionDialog(slot.slot)"
                  />
                </jv-list-item>
              }
            </jv-list>
          </jv-section>
        }

        @if (showComparison() && comparisonData(); as cd) {
          <jv-section title="Comparación de Precios">
            <jv-list variant="bordered">
              @for (item of cd; track item.slot) {
                <jv-list-item
                  [title]="item.slot"
                  [description]="item.component_name"
                >
                  <div meta class="compare-meta">
                    <span class="compare-snap">Snapshot: {{ item.snapshot ? '$' + item.snapshot.price.toLocaleString('es-MX') : '—' }}</span>
                    <span class="compare-latest">Actual: {{ item.latest.price != null ? '$' + item.latest.price.toLocaleString('es-MX') : '—' }}</span>
                    @if (item.price_delta != null) {
                      <span class="compare-delta" [class.delta-up]="item.price_delta > 0" [class.delta-down]="item.price_delta < 0">
                        {{ item.price_delta > 0 ? '+' : '' }}{{ item.price_delta.toLocaleString('es-MX') }}
                      </span>
                    }
                  </div>
                </jv-list-item>
              }
            </jv-list>
          </jv-section>
        }

        @if (total(); as t) {
          <jv-section title="Resumen de precios">
            <jv-list variant="bordered">
              @for (item of t.items; track item.slot) {
                <jv-list-item [title]="item.slot" [description]="item.component_name">
                  <span meta>{{ item.price > 0 ? '$' + item.price.toLocaleString('es-MX') : '—' }}</span>
                </jv-list-item>
              }
            </jv-list>
          </jv-section>
        }
      }
    </jv-page>

    <jv-dialog [open]="showEditMetaDialog()" title="Editar Build" (closed)="showEditMetaDialog.set(false)">
      <jv-input
        inputId="edit-name"
        placeholder="Nombre del build"
        [(ngModel)]="editName"
      />
      <jv-textarea
        placeholder="Descripción"
        [(ngModel)]="editDescription"
        style="margin-top: 0.5rem;"
      />
      <div dialog-actions>
        <jv-button (click)="showEditMetaDialog.set(false)">Cancelar</jv-button>
        <jv-button variant="primary" (click)="saveMetadata()">Guardar</jv-button>
      </div>
    </jv-dialog>

    <jv-dialog [open]="showDecisionDialog()" [title]="'Decisiones — ' + decisionSlot()" (closed)="showDecisionDialog.set(false)">
      @if (decisions(); as ds) {
        @if (ds.length > 0) {
          <jv-list>
            @for (d of ds; track d.id) {
              <jv-list-item [description]="d.reason" [title]="(d.created_at | date:'short') ?? ''" />
            }
          </jv-list>
        }
        @if (ds.length === 0) {
          <p class="empty-text">Sin decisiones registradas</p>
        }
      }
      <jv-textarea
        placeholder="Razón de la decisión..."
        [(ngModel)]="decisionReason"
        style="margin-top: 0.5rem;"
      />
      <div dialog-actions>
        <jv-button (click)="showDecisionDialog.set(false)">Cerrar</jv-button>
        <jv-button variant="primary" (click)="addDecision()">Agregar</jv-button>
      </div>
    </jv-dialog>
  `,
  styles: [`
    .info-row {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 1rem;
      margin-bottom: 1.5rem;
    }
    .stat {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 1rem;
      text-align: center;
      gap: 0.25rem;
    }
    .stat-label {
      font-size: 0.75rem;
      opacity: 0.6;
      text-transform: uppercase;
    }
    .stat-value {
      font-size: 1.5rem;
      font-weight: 700;
    }
    .price {
      color: var(--jv-color-primary);
    }
    .compare-meta {
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 0.15rem;
      font-size: 0.8rem;
    }
    .compare-snap {
      opacity: 0.6;
    }
    .compare-latest {
      font-weight: 600;
    }
    .compare-delta {
      font-weight: 700;
    }
    .delta-up {
      color: var(--jv-color-danger, #ef4444);
    }
    .delta-down {
      color: var(--jv-color-success, #10b981);
    }
    .empty-text {
      opacity: 0.5;
      text-align: center;
      padding: 1rem;
    }
  `],
})
export default class BuildDetailPage {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private buildsService = inject(BuildsService);
  private dialogService = inject(JvDialogService);
  private toastService = inject(JvToastService);

  protected build = signal<Build | null>(null);
  protected total = signal<BuildTotal | null>(null);
  protected comparisonData = signal<BuildComparison[] | null>(null);
  protected showComparison = signal(false);
  protected showEditMetaDialog = signal(false);
  protected editName = signal('');
  protected editDescription = signal('');
  protected showDecisionDialog = signal(false);
  protected decisionSlot = signal('');
  protected decisions = signal<BuildDecision[]>([]);
  protected decisionReason = signal('');

  protected breadcrumbs: JvBreadcrumbItem[] = [
    { label: 'Builds', href: '/builds' },
    { label: 'Detalle', active: true },
  ];

  constructor() {
    const id = Number(this.route.snapshot.paramMap.get('id')!);
    this.loadBuild(id);
  }

  private loadBuild(id: number) {
    this.buildsService.get(id).subscribe({
      next: (res) => {
        this.build.set(res);
        this.editName.set(res.name);
        this.editDescription.set(res.description ?? '');
      },
    });
    this.buildsService.total(id).subscribe({
      next: (res) => this.total.set(res),
    });
  }

  getSlotIcon(slot: string): string {
    const icons: Record<string, string> = {
      CPU: 'cpu',
      GPU: 'monitor',
      RAM: 'memory-stick',
      Motherboard: 'circuit-board',
      Storage: 'hard-drive',
      PSU: 'battery-charging',
      Case: 'box',
      Cooler: 'fan',
    };
    return icons[slot] ?? 'cpu';
  }

  editBuild() {
    const id = this.build()?.id;
    if (id) this.router.navigate(['/builds', id, 'edit']);
  }

  takeSnapshot() {
    const id = this.build()?.id;
    if (!id) return;
    this.buildsService.createSnapshot(id).subscribe({
      next: () => {
        this.toastService.show('Snapshot tomado correctamente', 'success');
      },
    });
  }

  toggleCompare() {
    const id = this.build()?.id;
    if (!id) return;
    if (this.showComparison()) {
      this.showComparison.set(false);
      return;
    }
    this.buildsService.compare(id).subscribe({
      next: (res) => {
        this.comparisonData.set(res);
        this.showComparison.set(true);
      },
    });
  }

  protected saveMetadata() {
    const buildId = this.build()?.id;
    if (!buildId) return;
    const name = this.editName().trim();
    if (!name) return;
      this.buildsService.update(buildId, { name, description: this.editDescription() || undefined }).subscribe({
      next: (res) => {
        this.build.set(res);
        this.showEditMetaDialog.set(false);
        this.toastService.show('Build actualizado', 'success');
      },
    });
  }

  protected openDecisionDialog(slot: string) {
    this.decisionSlot.set(slot);
    this.decisionReason.set('');
    const buildId = this.build()?.id;
    if (!buildId) return;
    this.buildsService.listDecisions(buildId, slot).subscribe({
      next: (res) => {
        this.decisions.set(res);
        this.showDecisionDialog.set(true);
      },
    });
  }

  protected addDecision() {
    const buildId = this.build()?.id;
    const slot = this.decisionSlot();
    const reason = this.decisionReason().trim();
    if (!buildId || !reason) return;
    this.buildsService.createDecision(buildId, slot, reason).subscribe({
      next: (res) => {
        this.decisionReason.set('');
        this.decisions.update(ds => [...ds, res]);
        this.toastService.show('Decisión agregada', 'success');
      },
    });
  }

  protected exportMarkdown() {
    const b = this.build();
    const t = this.total();
    if (!b || b.slots.length === 0) {
      this.toastService.show('No hay slots para exportar', 'warning');
      return;
    }

    const today = new Date().toLocaleDateString('es-MX', { year: 'numeric', month: 'long', day: 'numeric' });
    const link = `http://localhost:8080/builds/${b.id}`;
    const lines: string[] = [];

    // Title
    lines.push(`# ${b.name}`);
    lines.push('');

    // Meta
    lines.push(`> **Fecha:** ${today}  `);
    lines.push(`> **Enlace:** [${link}](${link})  `);
    if (b.description) {
      lines.push(`> **Descripción:** ${b.description}  `);
    }
    lines.push('');

    // Separator
    lines.push('---');
    lines.push('');

    // Group by category
    const grouped: Record<string, typeof b.slots> = {};
    for (const slot of b.slots) {
      const cat = slot.component_category || 'Sin categoría';
      if (!grouped[cat]) grouped[cat] = [];
      grouped[cat].push(slot);
    }

    const catOrder = [
      'Procesadores', 'Tarjetas de Video', 'Memorias RAM', 'Tarjetas Madre',
      'Almacenamiento (SSD)', 'Almacenamiento (HDD)', 'Fuentes de Poder', 'Gabinetes',
      'Disipadores CPU', 'Enfriamiento', 'Ventilación',
    ];

    let globalIdx = 0;
    const allRows: string[][] = [];

    for (const cat of catOrder) {
      const items = grouped[cat];
      if (!items || items.length === 0) continue;

      lines.push(`## ${cat}`);
      lines.push('');

      for (const slot of items) {
        globalIdx++;
        const priceItem = t?.items.find(pi => pi.slot === slot.slot);
        const price = priceItem?.price ?? 0;
        const priceStr = price > 0 ? `$${price.toLocaleString('es-MX')}` : '—';
        const locked = slot.is_locked ? '🔒' : '';

        allRows.push([
          `**${globalIdx}.**`,
          `**${slot.slot}** ${locked}`,
          slot.component_name,
          `\`${slot.component_id}\``,
          priceStr,
        ]);
      }
    }

    // Table header
    lines.push('| # | Slot | Componente | SKU | Precio |');
    lines.push('|---|------|------------|-----|--------|');

    // Table body
    for (const row of allRows) {
      lines.push(`| ${row[0]} | ${row[1]} | ${row[2]} | ${row[3]} | ${row[4]} |`);
    }

    lines.push('');

    // Total
    if (t && t.total > 0) {
      lines.push('---');
      lines.push('');
      lines.push(`## Total Estimado`);
      lines.push('');
      lines.push(`| | | | **$${t.total.toLocaleString('es-MX')}** |`);
      lines.push('');
    }

    // Footer
    lines.push('---');
    lines.push(`_Generado por PC Builder — ${today}_`);

    const md = lines.join('\n');
    const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `build-${b.id}-${b.name.replace(/[^a-zA-Z0-9]/g, '_')}.md`;
    a.click();
    URL.revokeObjectURL(url);
    this.toastService.show('Markdown descargado', 'success');
  }
}
