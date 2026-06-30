import { Component, inject, signal, computed } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { JvPageComponent, JvCardComponent, JvSectionComponent, JvButtonComponent, JvIconButtonComponent, JvSelectComponent, JvSwitchComponent, JvTextareaComponent, JvDialogComponent, JvInputComponent, JvAlertComponent, JvToastService, JvSelectOption, JvBreadcrumbItem } from '@devjuliovilla/jv-ui';
import { BuildsService } from '../../services/builds.service';
import { ComponentsService } from '../../services/components.service';
import { Build } from '../../models/build.model';
import { Component as ComponentModel } from '../../models/component.model';

@Component({
  selector: 'app-build-editor',
  standalone: true,
  imports: [JvPageComponent, JvCardComponent, JvSectionComponent, JvButtonComponent, JvIconButtonComponent, JvSelectComponent, JvSwitchComponent, JvTextareaComponent, JvDialogComponent, JvInputComponent, JvAlertComponent, FormsModule],
  template: `
    <jv-page [title]="'Editar: ' + (build()?.name ?? '')" [breadcrumbs]="breadcrumbs">
      <div page-actions>
        <jv-button (click)="showEditDialog.set(true)">Editar Build</jv-button>
      </div>

      @if (build(); as b) {
        <div class="slots-grid">
          @for (slot of slotKeys; track slot) {
            <jv-card>
              <jv-section [title]="slot">
                <jv-select
                  [options]="optionsBySlot()[slot]"
                  placeholder="Seleccionar componente..."
                  [modelValue]="getSelectedComponentId(slot)"
                  (selectionChange)="onSlotChange(slot, $event)"
                />
                @if (getSelectedComponentId(slot)) {
                  <div class="slot-extra">
                    <div class="slot-extra-row">
                      <jv-switch
                        label="Fijo"
                        inputId="lock-{{slot}}"
                        [(ngModel)]="lockStates[slot]"
                        (ngModelChange)="toggleLock(slot, $event)"
                      />
                      <jv-icon-button
                        icon="trash-2"
                        ariaLabel="Quitar componente"
                        variant="ghost"
                        (click)="removeSlot(slot)"
                      />
                    </div>
                    <jv-textarea
                      placeholder="Notas..."
                      [(ngModel)]="notesStates[slot]"
                      (ngModelChange)="updateNotes(slot, $event)"
                    />
                  </div>
                }
              </jv-section>
            </jv-card>
          }
        </div>

        <div class="actions">
          <jv-button (click)="cancel()">Volver</jv-button>
          <jv-button variant="outline" (click)="showBulk.set(!showBulk())">{{ showBulk() ? 'Ocultar' : 'Carga Masiva' }}</jv-button>
        </div>

        @if (showBulk()) {
          <jv-section title="Carga Masiva">
            @if (bulkError(); as err) {
              <jv-alert tone="danger" title="Error">{{ err }}</jv-alert>
            }
            @if (bulkSuccess(); as msg) {
              <jv-alert tone="success" title="OK">{{ msg }}</jv-alert>
            }
            <jv-textarea
              placeholder='{"CPU": "id-del-componente", "GPU": "otro-id"}'
              [(ngModel)]="bulkJson"
              (focus)="onBulkFocus()"
              [rows]="6"
            />
            <div class="bulk-actions">
              <jv-button variant="primary" (click)="applyBulk()">Aplicar</jv-button>
            </div>
          </jv-section>
        }
      }
    </jv-page>

    <jv-dialog [open]="showEditDialog()" title="Editar Build" (closed)="showEditDialog.set(false)">
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
        <jv-button (click)="showEditDialog.set(false)">Cancelar</jv-button>
        <jv-button variant="primary" (click)="saveMetadata()">Guardar</jv-button>
      </div>
    </jv-dialog>
  `,
  styles: [`
    .slots-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 1rem;
      margin-bottom: 1.5rem;
    }
    .slot-extra {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      margin-top: 0.75rem;
      padding-top: 0.75rem;
      border-top: 1px solid var(--jv-color-border, #e5e7eb);
    }
    .slot-extra-row {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .actions {
      display: flex;
      gap: 0.5rem;
    }
    .bulk-actions {
      margin-top: 0.5rem;
    }
  `],
})
export default class BuildEditorPage {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private buildsService = inject(BuildsService);
  private componentsService = inject(ComponentsService);
  private toastService = inject(JvToastService);

  protected build = signal<Build | null>(null);
  protected componentsByCategory = signal<Record<string, ComponentModel[]>>({});
  protected showEditDialog = signal(false);
  protected editName = signal('');
  protected editDescription = signal('');

  protected showBulk = signal(false);
  protected bulkJson = signal('{\n  "CPU": "id-del-procesador",\n  "GPU": "id-de-la-tarjeta-de-video"\n}');
  protected bulkTemplateCleared = signal(false);
  protected bulkError = signal<string | null>(null);
  protected bulkSuccess = signal<string | null>(null);

  protected lockStates: Record<string, boolean> = {};
  protected notesStates: Record<string, string> = {};

  protected slotKeys = ['CPU', 'GPU', 'RAM', 'Motherboard', 'Storage', 'PSU', 'Case', 'Cooler'];
  protected breadcrumbs: JvBreadcrumbItem[] = [];

  protected optionsBySlot = computed(() => {
    const components = this.componentsByCategory();
    const categoryMap: Record<string, string> = {
      CPU: 'Procesadores',
      GPU: 'Tarjetas de Video',
      RAM: 'Memorias RAM',
      Motherboard: 'Tarjetas Madre',
      Storage: 'Almacenamiento (SSD)',
      PSU: 'Fuentes de Poder',
      Case: 'Gabinetes',
      Cooler: 'Disipadores CPU',
    };

    const result: Record<string, JvSelectOption<string>[]> = {};
    for (const slot of this.slotKeys) {
      const cat = categoryMap[slot];
      const items = components[cat] ?? [];
      result[slot] = items.map(c => ({
        label: `${c.name} — $${c.price?.toLocaleString('es-MX') ?? 'N/A'}`,
        value: c.id,
      }));
    }
    return result;
  });

  constructor() {
    const id = Number(this.route.snapshot.paramMap.get('id')!);
    this.breadcrumbs = [
      { label: 'Builds', href: '/builds' },
      { label: `Build #${id}`, href: `/builds/${id}` },
      { label: 'Editar', active: true },
    ];

    this.buildsService.get(id).subscribe({
      next: (res) => {
        this.build.set(res);
        for (const s of res.slots) {
          this.lockStates[s.slot] = s.is_locked;
          this.notesStates[s.slot] = s.notes ?? '';
        }
      },
    });

    this.loadComponents();
  }

  private loadComponents() {
    this.componentsService.list().subscribe({
      next: (res) => {
        const grouped: Record<string, ComponentModel[]> = {};
        for (const c of res) {
          const cat = c.category;
          if (!grouped[cat]) grouped[cat] = [];
          grouped[cat].push(c);
        }
        this.componentsByCategory.set(grouped);
      },
    });
  }

  protected getSelectedComponentId(slot: string): string {
    return this.build()?.slots.find(s => s.slot === slot)?.component_id ?? '';
  }

  protected onSlotChange(slot: string, componentId: string) {
    const buildId = this.build()?.id;
    if (!buildId || !componentId) return;
    this.buildsService.createSlot(buildId, slot, componentId).subscribe({
      next: (res) => {
        this.build.update(b => {
          if (!b) return b;
          const slots = b.slots.filter(s => s.slot !== slot);
          return { ...b, slots: [...slots, res] };
        });
        this.lockStates[slot] = res.is_locked;
        this.notesStates[slot] = res.notes ?? '';
        this.toastService.show(`Slot ${slot} actualizado`, 'success');
      },
    });
  }

  protected removeSlot(slot: string) {
    const buildId = this.build()?.id;
    if (!buildId) return;
    this.buildsService.deleteSlot(buildId, slot).subscribe({
      next: () => {
        this.build.update(b => {
          if (!b) return b;
          return { ...b, slots: b.slots.filter(s => s.slot !== slot) };
        });
        delete this.lockStates[slot];
        delete this.notesStates[slot];
        this.toastService.show(`Slot ${slot} eliminado`, 'success');
      },
    });
  }

  protected toggleLock(slot: string, isLocked: boolean) {
    const buildId = this.build()?.id;
    const componentId = this.getSelectedComponentId(slot);
    if (!buildId || !componentId) return;
    this.buildsService.updateSlot(buildId, slot, componentId, isLocked).subscribe({
      next: () => this.toastService.show(`Slot ${slot} ${isLocked ? 'bloqueado' : 'desbloqueado'}`, 'info'),
    });
  }

  protected updateNotes(slot: string, notes: string) {
    const buildId = this.build()?.id;
    const componentId = this.getSelectedComponentId(slot);
    if (!buildId || !componentId) return;
    const isLocked = this.lockStates[slot] ?? false;
    this.buildsService.updateSlot(buildId, slot, componentId, isLocked, notes || null).subscribe({
      next: () => this.toastService.show(`Notas de ${slot} guardadas`, 'info'),
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
        this.showEditDialog.set(false);
        this.toastService.show('Build actualizado', 'success');
      },
    });
  }

  protected onBulkFocus() {
    if (!this.bulkTemplateCleared()) {
      this.bulkJson.set('');
      this.bulkTemplateCleared.set(true);
    }
  }

  protected applyBulk() {
    this.bulkError.set(null);
    this.bulkSuccess.set(null);
    const buildId = this.build()?.id;
    if (!buildId) return;

    try {
      const parsed = JSON.parse(this.bulkJson());
      if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
        this.bulkError.set('El JSON debe ser un objeto con slots como llaves y component IDs como valores.');
        return;
      }
      const count = Object.keys(parsed).length;
      if (count === 0) {
        this.bulkError.set('Debes incluir al menos un slot.');
        return;
      }
      this.buildsService.bulkSlots(buildId, parsed).subscribe({
        next: (res) => {
          this.build.update(b => {
            if (!b) return b;
            const kept = b.slots.filter(s => !(s.slot in parsed));
            return { ...b, slots: [...kept, ...res] };
          });
          for (const s of res) {
            this.lockStates[s.slot] = s.is_locked;
            this.notesStates[s.slot] = s.notes ?? '';
          }
          this.toastService.show(`${res.length} slot(es) actualizado(s)`, 'success');
      this.bulkSuccess.set(`${res.length} slot(es) actualizado(s).`);
        },
        error: (err) => {
          this.bulkError.set(err.message ?? 'Error al aplicar carga masiva');
        },
      });
    } catch {
      this.bulkError.set('JSON inválido. Revisa el formato.');
    }
  }

  protected save() {
    const id = this.build()?.id;
    if (id) this.router.navigate(['/builds', id]);
  }

  protected cancel() {
    const id = this.build()?.id;
    if (id) this.router.navigate(['/builds', id]);
  }
}
