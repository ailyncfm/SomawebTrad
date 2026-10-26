import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface AdminReunion {
  id: number;
  docType: string;
  docTypeLabel: string;
  titulo: string;
  fecha: string;
  area: string | null;
  usuarioNombre: string | null;
  usuarioEmail: string | null;
  createdAt: string;
  hasPdf: boolean;
}

export interface UsuarioFiltro { id: string; nombre: string; email: string; }

const API_BASE = 'http://localhost:5058/api/admin/reuniones';

@Injectable({ providedIn: 'root' })
export class AdminReunionesService {
  constructor(private http: HttpClient) {}

  list(tipo?: string, usuarioId?: string): Observable<AdminReunion[]> {
    const params: Record<string, string> = {};
    if (tipo) params['tipo'] = tipo;
    if (usuarioId) params['usuarioId'] = usuarioId;
    return this.http.get<AdminReunion[]>(API_BASE, { withCredentials: true, params });
  }

  usuarios(): Observable<UsuarioFiltro[]> {
    return this.http.get<UsuarioFiltro[]>(`${API_BASE}/usuarios`, { withCredentials: true });
  }

  downloadUrl(id: number): string {
    return `${API_BASE}/${id}/descargar`;
  }
}