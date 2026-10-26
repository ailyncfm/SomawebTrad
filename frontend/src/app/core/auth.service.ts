import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

export interface AuthResponse {
  email: string;
  nombre: string;
  rol: string;
}

const API_BASE = 'http://localhost:5058/api';

@Injectable({ providedIn: 'root' })
export class AuthService {
  user = signal<AuthResponse | null>(null);

  constructor(private http: HttpClient) {}

  login(email: string, password: string): Observable<AuthResponse> {
    return this.http
      .post<AuthResponse>(`${API_BASE}/auth/login`, { email, password }, { withCredentials: true })
      .pipe(tap(u => this.user.set(u)));
  }

  registro(nombre: string, email: string, password: string, password2: string): Observable<AuthResponse> {
    return this.http
      .post<AuthResponse>(`${API_BASE}/auth/registro`, { nombre, email, password, password2 }, { withCredentials: true })
      .pipe(tap(u => this.user.set(u)));
  }

  logout(): Observable<object> {
    return this.http
      .post(`${API_BASE}/auth/logout`, {}, { withCredentials: true })
      .pipe(tap(() => this.user.set(null)));
  }

  me(): Observable<AuthResponse> {
    return this.http
      .get<AuthResponse>(`${API_BASE}/auth/me`, { withCredentials: true })
      .pipe(tap(u => this.user.set(u)));
  }

  isLoggedIn(): boolean {
    return this.user() !== null;
  }

  isAdmin(): boolean {
    return this.user()?.rol === 'admin';
  }
}