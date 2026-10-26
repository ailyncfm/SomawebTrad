import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface AreaNode { id: number; nombre: string; codigoPdf: string | null; }
export interface SuperintendenciaNode { id: number; codigo: string; nombre: string; nombreCompleto: string; areas: AreaNode[]; }
export interface GerenciaNode { id: number; codigo: string; nombre: string; nombreCompleto: string; superintendencias: SuperintendenciaNode[]; }

const API_BASE = 'http://localhost:5058/api/admin/organizacion';

@Injectable({ providedIn: 'root' })
export class AdminOrganizacionService {
  constructor(private http: HttpClient) {}

  getTree(): Observable<GerenciaNode[]> {
    return this.http.get<GerenciaNode[]>(API_BASE, { withCredentials: true });
  }

  crearGerencia(codigo: string, nombre: string): Observable<object> {
    return this.http.post(`${API_BASE}/gerencias`, { codigo, nombre }, { withCredentials: true });
  }
  eliminarGerencia(id: number): Observable<object> {
    return this.http.delete(`${API_BASE}/gerencias/${id}`, { withCredentials: true });
  }

  crearSuperintendencia(gerenciaId: number, codigo: string, nombre: string): Observable<object> {
    return this.http.post(`${API_BASE}/superintendencias`, { gerenciaId, codigo, nombre }, { withCredentials: true });
  }
  eliminarSuperintendencia(id: number): Observable<object> {
    return this.http.delete(`${API_BASE}/superintendencias/${id}`, { withCredentials: true });
  }

  crearArea(superintendenciaId: number, nombre: string, codigoPdf: string): Observable<object> {
    return this.http.post(`${API_BASE}/areas`, { superintendenciaId, nombre, codigoPdf }, { withCredentials: true });
  }
  eliminarArea(id: number): Observable<object> {
    return this.http.delete(`${API_BASE}/areas/${id}`, { withCredentials: true });
  }
}