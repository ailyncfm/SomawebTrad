import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../core/auth.service';

@Component({
  selector: 'app-registro',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './registro.component.html',
  styleUrl: '../login/login.component.css'
})
export class RegistroComponent {
  nombre = '';
  email = '';
  password = '';
  password2 = '';
  error = signal<string | null>(null);
  loading = signal(false);

  constructor(private auth: AuthService, private router: Router) {}

  private extractErrorMessage(err: any): string {
    const body = err?.error;
    if (!body) return 'No se pudo crear la cuenta.';
    if (typeof body === 'string') return body;
    if (body.error) return body.error;
    if (body.errors) {
      const msgs: string[] = [];
      for (const key of Object.keys(body.errors)) msgs.push(...body.errors[key]);
      if (msgs.length) return msgs.join(' ');
    }
    return body.title || 'No se pudo crear la cuenta.';
  }

  submit() {
    this.error.set(null);
    this.loading.set(true);
    this.auth.registro(this.nombre, this.email, this.password, this.password2).subscribe({
      next: () => { this.loading.set(false); this.router.navigateByUrl('/'); },
      error: (err) => {
        this.loading.set(false);
        this.error.set(this.extractErrorMessage(err));
      }
    });
  }
}