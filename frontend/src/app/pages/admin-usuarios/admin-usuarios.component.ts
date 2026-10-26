import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AdminUsuariosService, AdminUsuario } from '../../core/admin-usuarios.service';
import { AuthService } from '../../core/auth.service';

@Component({
  selector: 'app-admin-usuarios',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './admin-usuarios.component.html',
  styleUrl: './admin-usuarios.component.css'
})
export class AdminUsuariosComponent implements OnInit {
  usuarios = signal<AdminUsuario[]>([]);
  loading = signal(true);
  errorMsg = signal<string | null>(null);
  q = '';

  constructor(private api: AdminUsuariosService, public auth: AuthService) {}

  ngOnInit(): void { this.load(); }

  load() {
    this.loading.set(true);
    this.api.list(this.q || undefined).subscribe({
      next: (list) => { this.usuarios.set(list); this.loading.set(false); },
      error: () => { this.errorMsg.set('No se pudo cargar la lista de usuarios.'); this.loading.set(false); }
    });
  }

  isSelf(u: AdminUsuario): boolean {
    return u.email === this.auth.user()?.email;
  }

  toggleActive(u: AdminUsuario) {
    this.api.toggleActive(u.id).subscribe({
      next: (res) => { u.isActiveAccount = res.isActiveAccount; },
      error: () => { this.errorMsg.set('No se pudo cambiar el estado de la cuenta.'); }
    });
  }

  toggleRole(u: AdminUsuario) {
    this.api.toggleRole(u.id).subscribe({
      next: (res) => { u.rol = res.rol; },
      error: () => { this.errorMsg.set('No se pudo cambiar el rol de la cuenta.'); }
    });
  }

  eliminar(u: AdminUsuario) {
    const ok = window.confirm('¿Eliminar definitivamente esta cuenta? Esta acción no se puede deshacer.');
    if (!ok) return;
    this.api.delete(u.id).subscribe({
      next: () => { this.usuarios.set(this.usuarios().filter(x => x.id !== u.id)); },
      error: () => { this.errorMsg.set('No se pudo eliminar la cuenta.'); }
    });
  }
}