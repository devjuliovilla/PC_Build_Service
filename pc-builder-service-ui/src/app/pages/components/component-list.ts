import { Component, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { JvPageComponent, JvGridComponent, JvGridColumn, JvGridOptions } from '@devjuliovilla/jv-ui';
import { ComponentsService } from '../../services/components.service';
import { Component as ComponentModel } from '../../models/component.model';

@Component({
  selector: 'app-component-list',
  standalone: true,
  imports: [JvPageComponent, JvGridComponent],
  template: `
    <jv-page title="Componentes" description="Catálogo de componentes para PC">
      <jv-grid
        [data]="components()"
        [columns]="columns"
        [options]="options"
        [trackBy]="'id'"
        (rowClick)="onRowClick($event)"
      />
    </jv-page>
  `,
})
export default class ComponentListPage {
  private componentsService = inject(ComponentsService);
  private router = inject(Router);

  protected components = signal<ComponentModel[]>([]);

  protected columns: JvGridColumn<ComponentModel>[] = [
    { key: 'id', header: 'ID', width: '10rem', searchable: true },
    { key: 'name', header: 'Nombre', sortable: true, searchable: true },
    { key: 'category', header: 'Categoría', sortable: true, searchable: true, width: '12rem' },
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

  protected options: JvGridOptions = {
    searchable: true,
    sortable: true,
    pageable: true,
    pageSize: 20,
    pageSizeOptions: [10, 20, 50, 100],
    exportable: true,
    density: 'normal',
    emptyMessage: 'No se encontraron componentes',
  };

  constructor() {
    this.componentsService.list().subscribe({
      next: (res) => this.components.set(res),
    });
  }

  onRowClick(component: ComponentModel) {
    this.router.navigate(['/components', component.id]);
  }
}
