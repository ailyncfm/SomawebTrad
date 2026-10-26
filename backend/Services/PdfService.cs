using Backend.DTOs;

namespace Backend.Services;

public class PdfService
{
    public static (double total, double? nota) CalcScore(List<SeccionDto> sections)
    {
        int total = 0, maxTotal = 0;
        foreach (var sec in sections)
            foreach (var it in sec.Items)
            {
                var opts = it.Options?.Count ?? 3;
                total += it.Selected;
                maxTotal += opts;
            }
        if (maxTotal == 0) return (0, null);
        double pct = (double)total / maxTotal;
        return (total, Math.Round(1.0 + pct * 6.0, 1));
    }

    public static string NotaCalidad(double? nota)
    {
        if (nota == null) return "";
        if (nota < 5.0) return "Baja calidad";
        if (nota < 6.0) return "Aceptable";
        return "Buena calidad";
    }

    public byte[] GenerarPrioritizacionPdf(PrioritizacionGenerarRequest req, double? nota, double total)
    {
        var w = new PdfSimpleWriter();
        double x0 = 40;
        double y = PdfSimpleWriter.PageHeight - 50;
        const double margBottom = 50;

        void Ensure(double needed)
        {
            if (y - needed < margBottom)
            {
                w.NewPage();
                y = PdfSimpleWriter.PageHeight - 50;
            }
        }

        void Heading(string text)
        {
            Ensure(30);
            w.Text(x0, y, text, 12, true);
            y -= 16;
        }

        void Line(string text, double size = 9, bool bold = false, int wrapChars = 110)
        {
            foreach (var ln in PdfSimpleWriter.WrapText(text, wrapChars))
            {
                Ensure(14);
                w.Text(x0, y, ln, size, bold);
                y -= 13;
            }
        }

        w.Text(x0, y, Data.PrioritizacionSchema.Title, 15, true);
        y -= 20;
        Line($"Fecha: {req.Fecha}    Hora: {req.Hora}");
        Line($"Gerencia: {req.Gerencia}    Superintendencia: {req.Superintendencia}    Área: {req.Area}");
        y -= 6;

        if (req.Observadores != null)
        {
            foreach (var (obs, idx) in req.Observadores.Select((o, i) => (o, i + 1)))
            {
                if (string.IsNullOrWhiteSpace(obs.Nombre)) continue;
                Heading($"Observador {idx}");
                Line($"{obs.Nombre} — {obs.Gerencia} / {obs.Superintendencia} — {obs.Email}");
            }
        }

        foreach (var sec in req.Sections)
        {
            Heading(sec.Name);
            int idx = 1;
            foreach (var it in sec.Items)
            {
                Line($"{idx}. {it.Question}", bold: true);
                var opcionTexto = (it.Selected >= 1 && it.Selected <= it.Options.Count)
                    ? $"   -> Selección: {it.Selected}. {it.Options[it.Selected - 1]}"
                    : "   -> Sin responder";
                Line(opcionTexto);
                idx++;
            }
            y -= 4;
        }

        if (req.Checklist != null && req.Checklist.Count > 0)
        {
            Heading("Checklist de seguridad");
            int i = 1;
            foreach (var it in req.Checklist)
            {
                var resp = it.Si ? "SI" : it.No ? "NO" : "—";
                Line($"{i}. [{resp}] {it.Question}");
                if (!string.IsNullOrWhiteSpace(it.Comentario))
                    Line($"   Comentario: {it.Comentario}");
                i++;
            }
            y -= 4;
        }

        var fb = req.Feedback;
        if (fb != null)
        {
            Heading("Feedback");
            Line($"Fortalezas: {fb.Fortalezas}");
            Line($"Oportunidades: {fb.Oportunidades}");
            Line($"Plan: {fb.Plan}");
        }

        y -= 4;
        Line($"Puntaje total: {total}    Nota: {(nota.HasValue ? nota.Value.ToString("0.0") : "-")}    " +
             $"Calidad de la reunión: {NotaCalidad(nota)}", bold: true);
        y -= 6;

        if (req.Commitments != null && req.Commitments.Count > 0)
        {
            Heading("Compromisos");
            foreach (var c in req.Commitments)
            {
                Line($"[{c.Area}] {c.Accion} — Responsable: {c.Responsable} — Fecha: {c.Fecha} — Estado: {c.Estado}" +
                     (string.IsNullOrWhiteSpace(c.Evidencia) ? "" : $" — Evidencia: {c.Evidencia}"));
            }
        }

        if (req.Participants != null && req.Participants.Count > 0)
        {
            Heading("Participantes");
            foreach (var p in req.Participants)
            {
                if (string.IsNullOrWhiteSpace(p.Responsable)) continue;
                var asis = p.Asistio == "si" ? "Sí" : p.Asistio == "no" ? "No" : "—";
                var conf = p.Conforme == "si" ? "Sí" : p.Conforme == "no" ? "No" : "—";
                Line($"[{p.Area}] {p.Responsable} — {p.Email} — Asistió: {asis} — Conforme: {conf}");
            }
        }

        return w.Save();
    }
}