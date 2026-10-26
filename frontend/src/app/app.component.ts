import { Component, signal } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from './core/auth.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent {
  menuOpen = signal(false);

  constructor(public auth: AuthService) {
    this.auth.me().subscribe({ error: () => {} });
  }

  logout() {
    this.auth.logout().subscribe(() => (window.location.href = '/login'));
  }
}
