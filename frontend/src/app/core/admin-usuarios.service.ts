import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface AdminUsuario {
  id: string;
  nombre: string;
  email: string;
  rol: string;
  isActiveAccount: boolean;
  createdAt: string;
  hasReuniones: boolean;
}

const API_BASE = 'http://localhost:5058/api/admin/usuarios';

@Injectable({ providedIn: 'root' })
export class AdminUsuariosService {
  constructor(private http: HttpClient) {}

  list(q?: string): Observable<AdminUsuario[]> {
    return this.http.get<AdminUsuario[]>(API_BASE, {
      withCredentials: true,
      params: q ? { q } : {},
    });
  }

  toggleActive(id: string): Observable<{ isActiveAccount: boolean }> {
    return this.http.post<{ isActiveAccount: boolean }>(`${API_BASE}/${id}/toggle-active`, {}, { withCredentials: true });
  }

  toggleRole(id: string): Observable<{ rol: string }> {
    return this.http.post<{ rol: string }>(`${API_BASE}/${id}/toggle-role`, {}, { withCredentials: true });
  }

  delete(id: string): Observable<object> {
    return this.http.delete(`${API_BASE}/${id}`, { withCredentials: true });
  }
}