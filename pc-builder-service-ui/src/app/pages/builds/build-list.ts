import { Component, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { JvPageComponent, JvGridComponent, JvGridColumn, JvGridOptions, JvGridAction, JvButtonComponent, JvDialogComponent, JvDialogService, JvInputComponent, JvToastService } from '@devjuliovilla/jv-ui';
import { BuildsService } from '../../services/builds.service';
import { Build } from '../../models/build.model';

@Component({
  selector: 'app-build-list',
  standalone: true,
  imports: [JvPageComponent, JvGridComponent, JvButtonComponent, JvDialogComponent, JvInputComponent, FormsModule],
  template: `
    <jv-page title="Builds" description="Armados de PC">
      <div page-actions>
        <jv-button variant="primary" (click)="showCreateDialog.set(true)">Nuevo Build</jv-button>
      </div>
      <jv-grid
        [data]="builds()"
        [columns]="columns"
        [actions]="actions"
        [options]="options"
        [trackBy]="'id'"
        (rowClick)="onRowClick($event)"
        (actionClick)="onAction($event)"
      />
    </jv-page>

    <jv-dialog [open]="showCreateDialog()" title="Nuevo Build" (closed)="showCreateDialog.set(false)">
      <jv-input
        inputId="build-name"
        placeholder="Nombre del build"
        [(ngModel)]="newBuildName"
        (keydown.enter)="confirmCreate()"
      />
      <div dialog-actions>
        <jv-button (click)="showCreateDialog.set(false)">Cancelar</jv-button>
        <jv-button variant="primary" (click)="confirmCreate()">Crear</jv-button>
      </div>
    </jv-dialog>
  `,
  styles: [`
    .active-badge {
      font-size: 0.875rem;
    }
  `],
})
export default class BuildListPage {
  private buildsService = inject(BuildsService);
  private dialogService = inject(JvDialogService);
  private toastService = inject(JvToastService);
  private router = inject(Router);

  protected builds = signal<Build[]>([]);
  protected showCreateDialog = signal(false);
  protected newBuildName = signal('');

  protected columns: JvGridColumn<Build>[] = [
    { key: 'id', header: 'ID', width: '4rem' },
    { key: 'name', header: 'Nombre', sortable: true, searchable: true },
    { key: 'description', header: 'Descripción', searchable: true },
    { key: 'is_active', header: 'Activo', width: '6rem', format: (v) => v ? 'Sí' : 'No' },
    { key: 'created_at', header: 'Creado', sortable: true },
    { key: 'updated_at', header: 'Actualizado', sortable: true },
  ];

  protected actions: JvGridAction<Build>[] = [
    { id: 'delete', label: 'Eliminar', icon: 'trash-2', variant: 'danger' },
  ];

  protected options: JvGridOptions = {
    sortable: true,
    pageable: true,
    pageSize: 20,
    exportable: true,
    emptyMessage: 'No hay builds aún',
  };

  constructor() {
    this.loadBuilds();
  }

  private loadBuilds() {
    this.buildsService.list().subscribe({
      next: (res) => this.builds.set(res),
    });
  }

  onRowClick(build: Build) {
    this.router.navigate(['/builds', build.id]);
  }

  onAction(event: { actionId: string; row: Build }) {
    if (event.actionId === 'delete') {
      this.dialogService.confirm({
        title: 'Eliminar Build',
        message: '¿Eliminar este build?',
        confirmLabel: 'Eliminar',
        tone: 'danger',
      }).then(result => {
        if (!result) return;
        this.buildsService.delete(event.row.id).subscribe({
          next: () => {
            this.loadBuilds();
            this.toastService.show('Build eliminado', 'success');
          },
        });
      });
    }
  }

  protected confirmCreate() {
    const name = this.newBuildName().trim();
    if (!name) return;
    this.showCreateDialog.set(false);
    this.newBuildName.set('');
    this.buildsService.create(name).subscribe({
      next: (build) => {
        this.loadBuilds();
        this.toastService.show('Build creado', 'success');
        this.router.navigate(['/builds', build.id]);
      },
    });
  }
}
