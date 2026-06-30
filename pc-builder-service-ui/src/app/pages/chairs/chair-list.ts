import { Component, inject, signal, computed } from '@angular/core';
import { Router } from '@angular/router';
import { JvPageComponent, JvCardComponent, JvBadgeComponent, JvIconButtonComponent, JvGridComponent, JvGridColumn, JvGridOptions, JvPaginationComponent, JvPaginationEvent } from '@devjuliovilla/jv-ui';
import { ChairsService } from '../../services/chairs.service';
import { Chair } from '../../models/chair.model';

type ViewMode = 'grid' | 'cards';

@Component({
  selector: 'app-chair-list',
  standalone: true,
  imports: [
    JvPageComponent, JvCardComponent,
    JvBadgeComponent, JvIconButtonComponent,
    JvGridComponent, JvPaginationComponent,
  ],
  template: `
    <jv-page title="Sillas Gamer" description="Catálogo de sillas gaming">
      <div page-actions>
        <jv-icon-button
          [icon]="viewMode() === 'grid' ? 'layout-grid' : 'table'"
          [ariaLabel]="viewMode() === 'grid' ? 'Vista cuadrícula' : 'Vista tabla'"
          (click)="toggleView()"
        />
      </div>

      @if (viewMode() === 'grid') {
        <jv-grid
          [data]="chairs()"
          [columns]="gridColumns"
          [options]="gridOptions"
          [trackBy]="'id'"
          (rowClick)="onRowClick($event)"
        />
      }

      @if (viewMode() === 'cards') {
        <div class="cards-grid">
          @for (item of visibleCards(); track item.id) {
            <jv-card class="product-card" (click)="onRowClick(item)">
              @if (item.image_url) {
                <img [src]="item.image_url" [alt]="item.name" class="card-image" loading="lazy" />
              }
              @if (!item.image_url) {
                <div class="card-image-placeholder">
                  <jv-icon-button icon="image-off" ariaLabel="Sin imagen" [disabled]="true" />
                </div>
              }
              <div class="card-body">
                <span class="card-name">{{ item.name }}</span>
                <span class="card-price">{{ item.price != null ? '$' + item.price.toLocaleString('es-MX') : '—' }}</span>
                <jv-badge [tone]="item.in_stock ? 'success' : 'danger'">{{ item.in_stock ? 'En stock' : 'Agotado' }}</jv-badge>
              </div>
            </jv-card>
          }
        </div>

        <jv-pagination
          [totalItems]="chairs().length"
          [pageSize]="cardPageSize()"
          [pageIndex]="cardPageIndex()"
          [pageSizeOptions]="[12, 24, 48, 96]"
          (pageChange)="onCardPageChange($event)"
        />
      }
    </jv-page>
  `,
  styles: [`
    .cards-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      gap: 1rem;
      margin-bottom: 1.5rem;
    }
    .product-card {
      cursor: pointer;
      overflow: hidden;
    }
    .card-image {
      width: 100%;
      height: 180px;
      object-fit: contain;
      background: var(--jv-color-surface, #fff);
      padding: 0.75rem;
    }
    .card-image-placeholder {
      height: 180px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: var(--jv-color-surface-alt, #f5f5f5);
    }
    .card-body {
      display: flex;
      flex-direction: column;
      gap: 0.4rem;
      padding: 0.75rem;
    }
    .card-name {
      font-size: 0.875rem;
      font-weight: 500;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }
    .card-price {
      font-size: 1.15rem;
      font-weight: 700;
    }
  `],
})
export default class ChairListPage {
  private chairsService = inject(ChairsService);
  private router = inject(Router);

  protected viewMode = signal<ViewMode>('grid');
  protected chairs = signal<Chair[]>([]);
  protected cardPageIndex = signal(0);
  protected cardPageSize = signal(24);

  protected visibleCards = computed(() => {
    const start = this.cardPageIndex() * this.cardPageSize();
    return this.chairs().slice(start, start + this.cardPageSize());
  });

  protected gridColumns: JvGridColumn<Chair>[] = [
    { key: 'id', header: 'ID', width: '10rem', searchable: true },
    { key: 'name', header: 'Nombre', sortable: true, searchable: true },
    {
      key: 'price',
      header: 'Precio',
      sortable: true,
      align: 'end',
      width: '10rem',
      format: (v) => v != null ? `$${(v as number).toLocaleString('es-MX')}` : '—',
    },
    { key: 'in_stock', header: 'Stock', width: '6rem', format: (v) => v ? 'Sí' : 'No' },
  ];

  protected gridOptions: JvGridOptions = {
    searchable: true,
    sortable: true,
    pageable: true,
    pageSize: 20,
    pageSizeOptions: [10, 20, 50, 100],
    exportable: true,
    emptyMessage: 'No se encontraron sillas',
  };

  constructor() {
    this.chairsService.list().subscribe({
      next: (res) => this.chairs.set(res),
    });
  }

  protected toggleView() {
    this.viewMode.update(m => m === 'grid' ? 'cards' : 'grid');
  }

  protected onRowClick(chair: Chair) {
    this.router.navigate(['/chairs', chair.id]);
  }

  protected onCardPageChange(event: JvPaginationEvent) {
    this.cardPageIndex.set(event.pageIndex);
    this.cardPageSize.set(event.pageSize);
  }
}
