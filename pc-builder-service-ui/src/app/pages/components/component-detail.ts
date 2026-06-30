import { Component, inject, signal, computed } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { JvPageComponent, JvCardComponent, JvSectionComponent, JvListComponent, JvListItemComponent, JvBadgeComponent, JvButtonComponent, JvSelectComponent, JvSelectOption, JvDialogService, JvToastService, JvBreadcrumbItem } from '@devjuliovilla/jv-ui';
import { ComponentsService } from '../../services/components.service';
import { BuildsService } from '../../services/builds.service';
import { Component as ComponentModel } from '../../models/component.model';
import { Build } from '../../models/build.model';

@Component({
  selector: 'app-component-detail',
  standalone: true,
  imports: [JvPageComponent, JvCardComponent, JvSectionComponent, JvListComponent, JvListItemComponent, JvBadgeComponent, JvButtonComponent, JvSelectComponent],
  template: `
    <jv-page [title]="component()?.name ?? 'Cargando...'" [breadcrumbs]="breadcrumbs">
      @if (component(); as c) {
        <div class="detail-grid">
          @if (c.image_url) {
            <jv-card>
              <img [src]="c.image_url" [alt]="c.name" class="product-image" />
            </jv-card>
          }
          <jv-card>
            <div class="info-grid">
              <div class="info-item">
                <span class="info-label">Categoría</span>
                <span class="info-value">{{ c.category }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">Precio</span>
                <span class="info-value price">{{ c.price != null ? '$' + c.price.toLocaleString('es-MX') : '—' }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">Stock</span>
                <jv-badge [tone]="c.in_stock ? 'success' : 'danger'">{{ c.in_stock ? 'En stock' : 'Agotado' }}</jv-badge>
              </div>
            </div>
          </jv-card>
        </div>

        @if (c.category) {
          <jv-section title="Agregar a Build">
            <div class="add-to-build">
              <jv-select
                placeholder="Seleccionar build..."
                [options]="buildOptions()"
                [modelValue]="selectedBuildId()"
                (selectionChange)="selectedBuildId.set($event)"
              />
              <jv-button
                variant="primary"
                [disabled]="!selectedBuildId()"
                (click)="addToBuild()"
              >
                Agregar como {{ detectedSlot() || '—' }}
              </jv-button>
            </div>
          </jv-section>
        }

        @if (specKeys().length > 0) {
          <jv-section title="Especificaciones">
            <jv-list>
              @for (key of specKeys(); track key) {
                <jv-list-item [title]="key" [description]="c.specifications[key]" />
              }
            </jv-list>
          </jv-section>
        }
      }
    </jv-page>
  `,
  styles: [`
    .detail-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1rem;
      margin-bottom: 1.5rem;
    }
    .product-image {
      max-width: 100%;
      height: auto;
      border-radius: var(--jv-radius-md, 0.5rem);
    }
    .info-grid {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }
    .info-item {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
    }
    .info-label {
      font-size: 0.75rem;
      opacity: 0.6;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .info-value {
      font-size: 1rem;
    }
    .price {
      font-size: 1.5rem;
      font-weight: 700;
    }
    .add-to-build {
      display: flex;
      gap: 0.5rem;
      align-items: end;
    }
  `],
})
export default class ComponentDetailPage {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private componentsService = inject(ComponentsService);
  private buildsService = inject(BuildsService);
  private dialogService = inject(JvDialogService);
  private toastService = inject(JvToastService);

  protected component = signal<ComponentModel | null>(null);
  protected specKeys = signal<string[]>([]);
  protected builds = signal<Build[]>([]);
  protected selectedBuildId = signal<string>('');

  protected breadcrumbs: JvBreadcrumbItem[] = [
    { label: 'Componentes', href: '/components' },
    { label: 'Detalle', active: true },
  ];

  private categoryToSlot: Record<string, string> = {
    'Procesadores': 'CPU',
    'Tarjetas de Video': 'GPU',
    'Memorias RAM': 'RAM',
    'Tarjetas Madre': 'Motherboard',
    'Almacenamiento (SSD)': 'Storage',
    'Almacenamiento (HDD)': 'Storage',
    'Fuentes de Poder': 'PSU',
    'Gabinetes': 'Case',
    'Disipadores CPU': 'Cooler',
    'Enfriamiento': 'Cooler',
    'Ventilación': 'Cooler',
  };

  protected detectedSlot = computed(() => {
    const cat = this.component()?.category;
    return cat ? (this.categoryToSlot[cat] ?? '—') : '—';
  });

  protected buildOptions = computed<JvSelectOption<string>[]>(() =>
    this.builds().map(b => ({
      label: `${b.name} (${b.slots.length}/8 slots)`,
      value: String(b.id),
    }))
  );

  constructor() {
    const id = this.route.snapshot.paramMap.get('id')!;
    this.componentsService.get(id).subscribe({
      next: (res) => {
        this.component.set(res);
        this.specKeys.set(Object.keys(res.specifications || {}));
      },
    });
    this.buildsService.list().subscribe({
      next: (res) => this.builds.set(res),
    });
  }

  protected addToBuild() {
    const component = this.component();
    const buildId = this.selectedBuildId();
    if (!component || !buildId) return;
    const slot = this.detectedSlot();
    if (slot === '—') return;

    this.buildsService.createSlot(Number(buildId), slot, component.id).subscribe({
      next: () => {
        this.toastService.show(`${component.name} agregado como ${slot}`, 'success');
        this.dialogService.confirm({
          title: 'Agregado',
          message: `${component.name} agregado como ${slot}`,
          confirmLabel: 'Ir al build',
          cancelLabel: 'Seguir aquí',
          tone: 'primary',
        }).then(result => {
          if (result) {
            this.router.navigate(['/builds', Number(buildId)]);
          }
        });
      },
    });
  }
}
