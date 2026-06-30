import { Component, inject, signal } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { JvPageComponent, JvCardComponent, JvSectionComponent, JvListComponent, JvListItemComponent, JvBadgeComponent, JvBreadcrumbItem } from '@devjuliovilla/jv-ui';
import { ChairsService } from '../../services/chairs.service';
import { Chair } from '../../models/chair.model';

@Component({
  selector: 'app-chair-detail',
  standalone: true,
  imports: [JvPageComponent, JvCardComponent, JvSectionComponent, JvListComponent, JvListItemComponent, JvBadgeComponent],
  template: `
    <jv-page [title]="chair()?.name ?? 'Cargando...'" [breadcrumbs]="breadcrumbs">
      @if (chair(); as c) {
        <div class="detail-grid">
          @if (c.image_url) {
            <jv-card>
              <img [src]="c.image_url" [alt]="c.name" class="product-image" />
            </jv-card>
          }
          <jv-card>
            <div class="info-grid">
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
  `],
})
export default class ChairDetailPage {
  private route = inject(ActivatedRoute);
  private chairsService = inject(ChairsService);

  protected chair = signal<Chair | null>(null);
  protected specKeys = signal<string[]>([]);
  protected breadcrumbs: JvBreadcrumbItem[] = [
    { label: 'Sillas Gamer', href: '/chairs' },
    { label: 'Detalle', active: true },
  ];

  constructor() {
    const id = this.route.snapshot.paramMap.get('id')!;
    this.chairsService.get(id).subscribe({
      next: (res) => {
        this.chair.set(res);
        this.specKeys.set(Object.keys(res.specifications || {}));
      },
    });
  }
}
