import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  PrioritizacionService, Schema, OrganizacionMap, CompromisoAbierto
} from '../../core/prioritizacion.service';

interface SectionAnswerItem { question: string; options: string[]; selected: number; }
interface SectionAnswer { name: string; items: SectionAnswerItem[]; }
interface ChecklistAnswer { question: string; si: boolean; no: boolean; comentario: string; }
interface ObservadorForm {
  nombre: string; gerencia: string; superintendencia: string; sap: string; email: string; posicion: string;
}
interface CommitmentRow {
  area: string; threadId: string; accion: string; responsable: string;
  fecha: string; estado: string; evidencia: string; abiertos: CompromisoAbierto[];
}
interface ParticipantRow {
  area: string; responsable: string; email: string;
  asistio: '' | 'si' | 'no'; conforme: '' | 'si' | 'no';
  isExtra: boolean; areaEditable: boolean;
}

const ESTADOS = ['NO INICIADO', 'EN CURSO', 'ATRASADO', 'COMPLETADO', 'CANCELADO'];

@Component({
  selector: 'app-priorizacion',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './priorizacion.component.html',
  styleUrl: './priorizacion.component.css'
})
export class PriorizacionComponent implements OnInit {
  estados = ESTADOS;

  loading = signal(true);
  submitting = signal(false);
  errorMsg = signal<string | null>(null);
  okMsg = signal<string | null>(null);

  schema: Schema | null = null;
  organizacion: OrganizacionMap = {};

  fecha = '';
  hora = '';
  gerencia = '';
  superintendencia = '';
  area = '';

  gerencias: string[] = [];
  superintendencias: string[] = [];
  areas: string[] = [];

  obs1: ObservadorForm = { nombre: '', gerencia: '', superintendencia: '', sap: '', email: '', posicion: '' };
  showObs2 = signal(false);
  obs2: ObservadorForm = { nombre: '', gerencia: '', superintendencia: '', sap: '', email: '', posicion: '' };

  sections: SectionAnswer[] = [];
  checklist: ChecklistAnswer[] = [];
  checklistTouched = signal(false);

  fortalezas = '';
  oportunidades = '';
  plan = '';

  commitments: CommitmentRow[] = [];
  participants: ParticipantRow[] = [];

  constructor(private api: PrioritizacionService) {}

  ngOnInit(): void {
    this.autofillFechaHora();

    this.api.getSchema().subscribe({
      next: (schema) => {
        this.schema = schema;
        this.sections = schema.sections.map(sec => ({
          name: sec.name,
          items: sec.items.map(it => ({ question: it.question, options: it.options, selected: 0 })),
        }));
        this.checklist = schema.checklist.map(q => ({ question: q, si: false, no: false, comentario: '' }));
        this.participants = schema.participantAreas.map(a => ({
          area: a, responsable: '', email: '', asistio: '', conforme: '', isExtra: false, areaEditable: false,
        }));
        this.addCommitmentRow();
        this.loading.set(false);
      },
      error: () => { this.errorMsg.set('No se pudo cargar el formulario.'); this.loading.set(false); }
    });

    this.api.getOrganizacion().subscribe({
      next: (org) => { this.organizacion = org; this.gerencias = Object.keys(org); },
      error: () => {}
    });
  }

  private autofillFechaHora() {
    const now = new Date();
    const dd = String(now.getDate()).padStart(2, '0');
    const mm = String(now.getMonth() + 1).padStart(2, '0');
    this.fecha = `${dd}/${mm}/${now.getFullYear()}`;
    this.hora = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
  }

  onGerenciaChange() {
    this.superintendencia = '';
    this.area = '';
    this.superintendencias = Object.keys(this.organizacion[this.gerencia] || {});
    this.areas = [];
  }

  onSuperintendenciaChange() {
    this.area = '';
    this.areas = (this.organizacion[this.gerencia] || {})[this.superintendencia] || [];
  }

  toggleObs2() { this.showObs2.set(!this.showObs2()); }

  selectOption(item: SectionAnswerItem, idx: number) { item.selected = idx + 1; }

  setChecklist(row: ChecklistAnswer, val: 'si' | 'no') {
    row.si = val === 'si';
    row.no = val === 'no';
  }

  addCommitmentRow() {
    this.commitments.push({
      area: '', threadId: '', accion: '', responsable: '', fecha: '', estado: '', evidencia: '', abiertos: [],
    });
  }

  removeCommitmentRow(i: number) { this.commitments.splice(i, 1); }

  onCommitmentAreaChange(row: CommitmentRow) {
    row.threadId = '';
    row.abiertos = [];
    if (!row.area) return;
    this.api.getCompromisosAbiertos('prioritization', row.area).subscribe({
      next: (res) => { row.abiertos = res.compromisos || []; },
      error: () => {}
    });
  }

  onExistingCompromisoChange(row: CommitmentRow) {
    if (!row.threadId) return;
    const found = row.abiertos.find(c => c.threadId === row.threadId);
    if (found) {
      row.accion = found.accion;
      row.responsable = found.responsable;
      row.fecha = found.fecha;
    }
  }

  addParticipantRow(afterIndex: number, area: string) {
    const isOtro = area.trim().toUpperCase() === 'OTRO';
    this.participants.splice(afterIndex + 1, 0, {
      area: isOtro ? '' : area, responsable: '', email: '', asistio: '', conforme: '',
      isExtra: true, areaEditable: isOtro,
    });
  }

  removeParticipantRow(i: number) { this.participants.splice(i, 1); }
  attemptedSubmit = signal(false);
  onAsistioChange(row: ParticipantRow) {
    if (row.asistio === 'no') row.conforme = '';
  }

  private allQuestionsAnswered(): boolean {
    return this.sections.every(sec => sec.items.every(it => it.selected > 0));
  }

  private allChecklistAnswered(): boolean {
    this.checklistTouched.set(true);
    return this.checklist.every(c => c.si || c.no);
  }

  private hasAnyParticipant(): boolean {
    return this.participants.some(p => p.responsable.trim() !== '');
  }

  private scrollToFirstInvalid(selector: string) {
    setTimeout(() => {
      document.querySelector(selector)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 0);
  }

    hasAnyParticipantFilled(): boolean {
    return this.participants.some(p => p.responsable.trim() !== '');
  }

  hasChecklistInvalid(): boolean {
    return this.checklist.some(c => !c.si && !c.no);
  }
    


  submit() {
    this.errorMsg.set(null);
    this.okMsg.set(null);
    this.attemptedSubmit.set(true);

    if (!this.fecha || !this.hora) {
      this.errorMsg.set('Completa fecha y hora.');
      this.scrollToFirstInvalid('.alert-error');
      return;
    }
    if (!this.allQuestionsAnswered()) {
      this.errorMsg.set('Debes responder todas las preguntas de las secciones.');
      this.scrollToFirstInvalid('.qblock--invalid');
      return;
    }
    if (!this.allChecklistAnswered()) {
      this.errorMsg.set('Hay requisitos del checklist sin responder.');
      this.scrollToFirstInvalid('.checklist-row--invalid');
      return;
    }
    if (!this.hasAnyParticipant()) {
      this.errorMsg.set('Debes agregar al menos un participante.');
      this.scrollToFirstInvalid('#participantsSection');
      return;
    }

    const observadores = [this.obs1, ...(this.showObs2() ? [this.obs2] : [])]
      .filter(o => o.nombre.trim() !== '')
      .map(o => ({
        nombre: o.nombre, gerencia: o.gerencia, superintendencia: o.superintendencia,
        sap: o.sap, email: o.email, posicion: o.posicion,
      }));

    const payload = {
      fecha: this.fecha,
      hora: this.hora,
      gerencia: this.gerencia,
      superintendencia: this.superintendencia,
      area: this.area,
      observadores,
      sections: this.sections.map(sec => ({
        name: sec.name,
        items: sec.items.map(it => ({ question: it.question, options: it.options, selected: it.selected })),
      })),
      checklist: this.checklist.map(c => ({
        question: c.question, si: c.si, no: c.no, comentario: c.comentario || null,
      })),
      feedback: { fortalezas: this.fortalezas, oportunidades: this.oportunidades, plan: this.plan },
      commitments: this.commitments
        .filter(c => c.accion.trim() || c.responsable.trim())
        .map(c => ({
          area: c.area, accion: c.accion, responsable: c.responsable, fecha: c.fecha,
          estado: c.estado, evidencia: c.evidencia || null,
          threadId: c.threadId || null,
        })),
      participants: this.participants
        .filter(p => p.responsable.trim())
        .map(p => ({
          area: p.area, responsable: p.responsable, email: p.email,
          asistio: p.asistio || null, conforme: p.conforme || null,
        })),
    };

    this.submitting.set(true);
    this.api.generar(payload).subscribe({
      next: (resp) => {
        this.submitting.set(false);
        const blob = resp.body as Blob;
        const cd = resp.headers.get('Content-Disposition') || '';
        const match = cd.match(/filename="?([^"]+)"?/);
        const filename = match ? match[1] : 'documento.pdf';
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = filename;
        document.body.appendChild(a); a.click(); a.remove();
        window.URL.revokeObjectURL(url);
        this.okMsg.set('PDF generado y descargado correctamente.');
      },
      error: () => {
        this.submitting.set(false);
        this.errorMsg.set('Ocurrió un error al generar el PDF. Intenta nuevamente.');
        this.scrollToFirstInvalid('.alert-error');
      }
    });
  }
}