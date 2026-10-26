import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface SchemaItem { question: string; options: string[]; }
export interface SchemaSection { name: string; items: SchemaItem[]; }
export interface Schema {
  title: string;
  sections: SchemaSection[];
  participantAreas: string[];
  checklist: string[];
}

export interface OrganizacionMap {
  [gerencia: string]: { [superintendencia: string]: string[] };
}

export interface CompromisoAbierto {
  threadId: string;
  accion: string;
  responsable: string;
  fecha: string;
  estado: string;
  vencido: boolean;
}

const API_BASE = 'http://localhost:5058/api';

@Injectable({ providedIn: 'root' })
export class PrioritizacionService {
  constructor(private http: HttpClient) {}

  getSchema(): Observable<Schema> {
    return this.http.get<Schema>(`${API_BASE}/prioritizacion/schema`, { withCredentials: true });
  }

  getOrganizacion(): Observable<OrganizacionMap> {
    return this.http.get<OrganizacionMap>(`${API_BASE}/organizacion`, { withCredentials: true });
  }

  getCompromisosAbiertos(docType: string, area: string): Observable<{ compromisos: CompromisoAbierto[] }> {
    return this.http.get<{ compromisos: CompromisoAbierto[] }>(
      `${API_BASE}/compromisos/abiertos`,
      { params: { docType, area }, withCredentials: true }
    );
  }

  generar(payload: unknown): Observable<any> {
    return this.http.post(`${API_BASE}/prioritizacion/generar`, payload, {
      withCredentials: true,
      responseType: 'blob',
      observe: 'response',
    });
  }
}