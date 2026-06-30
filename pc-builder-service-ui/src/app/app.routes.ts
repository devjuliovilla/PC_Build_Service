import { Routes } from '@angular/router';
import { DashboardLayout } from './pages/dashboard-layout/dashboard-layout';

export const routes: Routes = [
  {
    path: '',
    component: DashboardLayout,
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      {
        path: 'dashboard',
        loadComponent: () => import('./pages/dashboard/dashboard'),
      },
      {
        path: 'components',
        loadComponent: () => import('./pages/components/category-page'),
      },
      {
        path: 'components/category/:category',
        loadComponent: () => import('./pages/components/category-page'),
      },
      {
        path: 'components/:id',
        loadComponent: () => import('./pages/components/component-detail'),
      },
      {
        path: 'chairs',
        loadComponent: () => import('./pages/chairs/chair-list'),
      },
      {
        path: 'chairs/:id',
        loadComponent: () => import('./pages/chairs/chair-detail'),
      },
      {
        path: 'builds',
        loadComponent: () => import('./pages/builds/build-list'),
      },
      {
        path: 'builds/:id',
        loadComponent: () => import('./pages/builds/build-detail'),
      },
      {
        path: 'builds/:id/edit',
        loadComponent: () => import('./pages/builds/build-editor'),
      },
      {
        path: 'status',
        loadComponent: () => import('./pages/status/status'),
      },
    ],
  },
];
