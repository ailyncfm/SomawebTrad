import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AdminReunionesService, AdminReunion, UsuarioFiltro } from '../../core/admin-reuniones.service';

const TIPOS = [
  { value: '', label: 'Todos los tipos' },
  { value: 'prioritization', label: 'Priorización' },
  { value: 'planning', label: 'Planificación' },
  { value: 'scheduling', label: 'Programación' },
  { value: 'post', label: 'Post Mantención' },
  { value: 'process_5s', label: 'Conciliación SEP4' },
];

@Component({
  selector: 'app-admin-reuniones',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './admin-reuniones.component.html',
  styleUrl: '../admin-usuarios/admin-usuarios.component.css'
})
export class AdminReunionesComponent implements OnInit {
  tipos = TIPOS;
  reuniones = signal<AdminReunion[]>([]);
  usuarios = signal<UsuarioFiltro[]>([]);
  loading = signal(true);
  errorMsg = signal<string | null>(null);

  tipoFiltro = '';
  usuarioFiltro = '';

  constructor(private api: AdminReunionesService) {}

  ngOnInit(): void {
    this.api.usuarios().subscribe({ next: (u) => this.usuarios.set(u), error: () => {} });
    this.load();
  }

  load() {
    this.loading.set(true);
    this.api.list(this.tipoFiltro || undefined, this.usuarioFiltro || undefined).subscribe({
      next: (list) => { this.reuniones.set(list); this.loading.set(false); },
      error: () => { this.errorMsg.set('No se pudo cargar el historial de reuniones.'); this.loading.set(false); }
    });
  }

  setTipo(t: string) { this.tipoFiltro = t; this.load(); }

  downloadUrl(id: number): string { return this.api.downloadUrl(id); }
}