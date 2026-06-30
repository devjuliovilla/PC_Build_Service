import { Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { JvDashboardShellComponent, JvToastComponent, JvThemeService, JvNavItem } from '@devjuliovilla/jv-ui';

@Component({
  selector: 'app-dashboard-layout',
  standalone: true,
  imports: [RouterOutlet, JvDashboardShellComponent, JvToastComponent],
  template: `
    <jv-dashboard-shell
      [title]="'PC Builder'"
      [sidebarSubtitle]="'Catálogo de componentes'"
      [brandIcon]="'monitor'"
      [navItems]="navItems"
      [showThemeSelector]="false"
    >
      <router-outlet />
    </jv-dashboard-shell>
    <jv-toast />
  `,
})
export class DashboardLayout {
  private themeService = inject(JvThemeService);

  protected navItems: JvNavItem[] = [
    { id: 'dashboard', label: 'Dashboard', icon: 'layout-dashboard', href: '/dashboard' },
    {
      id: 'components',
      label: 'Componentes',
      icon: 'cpu',
      children: [
        { id: 'cat-all', label: 'Todos', href: '/components' },
        { id: 'cat-procesadores', label: 'Procesadores', href: '/components/category/Procesadores' },
        { id: 'cat-gpu', label: 'Tarjetas de Video', href: '/components/category/Tarjetas de Video' },
        { id: 'cat-motherboards', label: 'Tarjetas Madre', href: '/components/category/Tarjetas Madre' },
        { id: 'cat-ram', label: 'Memorias RAM', href: '/components/category/Memorias RAM' },
        { id: 'cat-ssd', label: 'Almacenamiento (SSD)', href: '/components/category/Almacenamiento (SSD)' },
        { id: 'cat-hdd', label: 'Almacenamiento (HDD)', href: '/components/category/Almacenamiento (HDD)' },
        { id: 'cat-psu', label: 'Fuentes de Poder', href: '/components/category/Fuentes de Poder' },
        { id: 'cat-cases', label: 'Gabinetes', href: '/components/category/Gabinetes' },
        { id: 'cat-coolers', label: 'Disipadores CPU', href: '/components/category/Disipadores CPU' },
        { id: 'cat-cooling', label: 'Enfriamiento', href: '/components/category/Enfriamiento' },
        { id: 'cat-fans', label: 'Ventilación', href: '/components/category/Ventilación' },
      ],
    },
    { id: 'chairs', label: 'Sillas Gamer', icon: 'armchair', href: '/chairs' },
    { id: 'builds', label: 'Builds', icon: 'package', href: '/builds' },
    { id: 'status', label: 'Estado', icon: 'activity', href: '/status' },
  ];

  constructor() {
    this.themeService.setTheme('dark');
  }
}
