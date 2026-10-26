import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AdminOrganizacionService, GerenciaNode } from '../../core/admin-organizacion.service';

@Component({
  selector: 'app-admin-organizacion',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './admin-organizacion.component.html',
  styleUrl: '../admin-usuarios/admin-usuarios.component.css'
})
export class AdminOrganizacionComponent implements OnInit {
  gerencias = signal<GerenciaNode[]>([]);
  loading = signal(true);
  errorMsg = signal<string | null>(null);

  nuevoGCodigo = ''; nuevoGNombre = '';
  nuevoSCodigo: Record<number, string> = {};
  nuevoSNombre: Record<number, string> = {};
  nuevoANombre: Record<number, string> = {};
  nuevoACodigoPdf: Record<number, string> = {};

  constructor(private api: AdminOrganizacionService) {}

  ngOnInit(): void { this.load(); }

  load() {
    this.loading.set(true);
    this.api.getTree().subscribe({
      next: (g) => { this.gerencias.set(g); this.loading.set(false); },
      error: () => { this.errorMsg.set('No se pudo cargar la estructura.'); this.loading.set(false); }
    });
  }

  crearGerencia() {
    if (!this.nuevoGCodigo.trim() || !this.nuevoGNombre.trim()) return;
    this.api.crearGerencia(this.nuevoGCodigo.trim(), this.nuevoGNombre.trim()).subscribe({
      next: () => { this.nuevoGCodigo = ''; this.nuevoGNombre = ''; this.load(); },
      error: () => this.errorMsg.set('No se pudo crear la gerencia.')
    });
  }

  eliminarGerencia(id: number) {
    if (!window.confirm('¿Eliminar esta gerencia y todo lo que contiene (superintendencias y áreas)? No se puede deshacer.')) return;
    this.api.eliminarGerencia(id).subscribe({
      next: () => this.load(),
      error: () => this.errorMsg.set('No se pudo eliminar la gerencia.')
    });
  }

  crearSuperintendencia(gerenciaId: number) {
    const codigo = (this.nuevoSCodigo[gerenciaId] || '').trim();
    const nombre = (this.nuevoSNombre[gerenciaId] || '').trim();
    if (!codigo || !nombre) return;
    this.api.crearSuperintendencia(gerenciaId, codigo, nombre).subscribe({
      next: () => { this.nuevoSCodigo[gerenciaId] = ''; this.nuevoSNombre[gerenciaId] = ''; this.load(); },
      error: () => this.errorMsg.set('No se pudo crear la superintendencia.')
    });
  }

  eliminarSuperintendencia(id: number) {
    if (!window.confirm('¿Eliminar esta superintendencia y sus áreas?')) return;
    this.api.eliminarSuperintendencia(id).subscribe({
      next: () => this.load(),
      error: () => this.errorMsg.set('No se pudo eliminar la superintendencia.')
    });
  }

  crearArea(superintendenciaId: number) {
    const nombre = (this.nuevoANombre[superintendenciaId] || '').trim();
    const codigoPdf = (this.nuevoACodigoPdf[superintendenciaId] || '').trim();
    if (!nombre) return;
    this.api.crearArea(superintendenciaId, nombre, codigoPdf).subscribe({
      next: () => { this.nuevoANombre[superintendenciaId] = ''; this.nuevoACodigoPdf[superintendenciaId] = ''; this.load(); },
      error: () => this.errorMsg.set('No se pudo crear el área.')
    });
  }

  eliminarArea(id: number) {
    if (!window.confirm('¿Eliminar esta área?')) return;
    this.api.eliminarArea(id).subscribe({
      next: () => this.load(),
      error: () => this.errorMsg.set('No se pudo eliminar el área.')
    });
  }
}