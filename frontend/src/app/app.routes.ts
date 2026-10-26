import { Routes } from '@angular/router';
import { authGuard } from './core/auth.guard';
import { adminGuard } from './core/admin.guard';

export const routes: Routes = [
  { path: 'login', loadComponent: () => import('./pages/login/login.component').then(m => m.LoginComponent) },
  { path: 'registro', loadComponent: () => import('./pages/registro/registro.component').then(m => m.RegistroComponent) },
  { path: '', pathMatch: 'full', loadComponent: () => import('./pages/home/home.component').then(m => m.HomeComponent), canActivate: [authGuard] },
  { path: 'priorizacion', loadComponent: () => import('./pages/priorizacion/priorizacion.component').then(m => m.PriorizacionComponent), canActivate: [authGuard] },
  { path: 'admin', loadComponent: () => import('./pages/admin-usuarios/admin-usuarios.component').then(m => m.AdminUsuariosComponent), canActivate: [authGuard, adminGuard] },
  { path: 'admin/reuniones', loadComponent: () => import('./pages/admin-reuniones/admin-reuniones.component').then(m => m.AdminReunionesComponent), canActivate: [authGuard, adminGuard] },
  { path: 'admin/organizacion', loadComponent: () => import('./pages/admin-organizacion/admin-organizacion.component').then(m => m.AdminOrganizacionComponent), canActivate: [authGuard, adminGuard] },  
  { path: '**', redirectTo: '' },
];