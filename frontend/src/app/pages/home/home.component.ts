import { Component } from '@angular/core';
import { AuthService } from '../../core/auth.service';

@Component({
  selector: 'app-home',
  standalone: true,
  template: `<h2>Hola, {{ auth.user()?.nombre }} 👋</h2><p>Próximo: formularios de priorización, planning, etc.</p>`
})
export class HomeComponent {
  constructor(public auth: AuthService) {}
}