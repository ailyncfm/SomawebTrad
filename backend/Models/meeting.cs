namespace Backend.Models;

public class Reunion
{
    public int Id { get; set; }
    public string DocType { get; set; } = "";
    public string Titulo { get; set; } = "";
    public string Fecha { get; set; } = "";   // DD/MM/AAAA, igual que en Python
    public string Hora { get; set; } = "";
    public string? Area { get; set; }
    public string? Gerencia { get; set; }
    public string? Superintendencia { get; set; }
    public string? UsuarioId { get; set; }
    public string? PdfPath { get; set; }
    public string? PdfFilename { get; set; }
    public double? Nota { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public List<Compromiso> Compromisos { get; set; } = new();
    public List<Participante> Participantes { get; set; } = new();
}

public class Compromiso
{
    public int Id { get; set; }
    public int ReunionId { get; set; }
    public string Accion { get; set; } = "";
    public string Responsable { get; set; } = "";
    public string FechaCompromiso { get; set; } = "";
    public string Estado { get; set; } = "";
    public string? Evidencia { get; set; }
    public string? Area { get; set; }
    public string? ThreadId { get; set; } // agrupa el mismo compromiso entre reuniones

    public bool IsVencido
    {
        get
        {
            var estado = (Estado ?? "").Trim().ToUpperInvariant();
            if (estado is "CERRADO" or "CANCELADO" or "COMPLETADO") return false;
            if (!DateTime.TryParseExact(FechaCompromiso, "dd/MM/yyyy",
                    System.Globalization.CultureInfo.InvariantCulture,
                    System.Globalization.DateTimeStyles.None, out var d)) return false;
            return d.Date < DateTime.Today;
        }
    }
}

public class Participante
{
    public int Id { get; set; }
    public int ReunionId { get; set; }
    public string? Area { get; set; }
    public string Nombre { get; set; } = "";
    public string? Email { get; set; }
    public bool? Asistio { get; set; }
    public bool? Conforme { get; set; }
    public string Origen { get; set; } = "manual";
}