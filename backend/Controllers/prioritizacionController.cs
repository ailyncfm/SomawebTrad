using System.Globalization;
using System.Text.RegularExpressions;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Backend.Data;
using Backend.DTOs;
using Backend.Models;
using Backend.Services;

namespace Backend.Controllers;

[ApiController]
[Route("api/prioritizacion")]
[Authorize]
public class PrioritizacionController : ControllerBase
{
    private readonly AppDbContext _db;
    private readonly PdfService _pdf;
    private readonly IWebHostEnvironment _env;
    private readonly IConfiguration _config;

    public PrioritizacionController(AppDbContext db, PdfService pdf, IWebHostEnvironment env, IConfiguration config)
    {
        _db = db; _pdf = pdf; _env = env; _config = config;
    }

    [HttpGet("schema")]
    public IActionResult GetSchema()
    {
        return Ok(new
        {
            title = PrioritizacionSchema.Title,
            sections = PrioritizacionSchema.Sections,
            participantAreas = PrioritizacionSchema.ParticipantAreas,
            checklist = PrioritizacionSchema.ChecklistQuestions,
        });
    }

    [HttpGet("/api/organizacion")]
    public IActionResult GetOrganizacion()
    {
        var gerencias = _db.Gerencias
            .Include(g => g.Superintendencias).ThenInclude(s => s.Areas)
            .OrderBy(g => g.Codigo)
            .ToList();

        var result = gerencias.ToDictionary(
            g => g.NombreCompleto,
            g => g.Superintendencias.ToDictionary(
                s => s.NombreCompleto,
                s => s.Areas.Select(a => a.Nombre).ToList()));

        return Ok(result);
    }

    [HttpGet("/api/compromisos/abiertos")]
    public IActionResult CompromisosAbiertos([FromQuery] string docType, [FromQuery] string area)
    {
        if (string.IsNullOrWhiteSpace(docType) || string.IsNullOrWhiteSpace(area))
            return Ok(new { compromisos = Array.Empty<object>() });


        // Join manual porque Compromiso no tiene navegación directa a Reunion.DocType en este modelo simplificado
        var query = from c in _db.Compromisos
                     join r in _db.Reuniones on c.ReunionId equals r.Id
                     where r.DocType == docType && c.Area == area
                     orderby c.Id
                     select c;

        var latestByKey = new Dictionary<string, Compromiso>();
        foreach (var c in query.ToList())
            latestByKey[c.ThreadId ?? c.Id.ToString()] = c;

        var result = new List<CompromisoAbiertoDto>();
        foreach (var c in latestByKey.Values)
        {
            var estado = (c.Estado ?? "").Trim().ToUpperInvariant();
            if (estado is "COMPLETADO" or "CANCELADO") continue;

            if (c.ThreadId == null)
            {
                c.ThreadId = c.Id.ToString();
                _db.Compromisos.Update(c);
            }

            result.Add(new CompromisoAbiertoDto(
                c.ThreadId!, c.Accion ?? "", c.Responsable ?? "",
                c.FechaCompromiso ?? "", c.Estado ?? "", c.IsVencido));
        }
        _db.SaveChanges();

        return Ok(new { compromisos = result });
    }

    private static string WeekYearCode(string fechaDmy)
    {
        if (!DateTime.TryParseExact(fechaDmy, "dd/MM/yyyy", CultureInfo.InvariantCulture, DateTimeStyles.None, out var d))
            return "SS_AA";
        int week = ISOWeek.GetWeekOfYear(d);
        int year = ISOWeek.GetYear(d);
        return $"{week}_{year % 100:D2}";
    }

    private string BuildFilename(PrioritizacionGenerarRequest req)
    {
        string gerenciaCode = "SINGER";
        if (!string.IsNullOrWhiteSpace(req.Gerencia))
            gerenciaCode = req.Gerencia.Contains(" - ") ? req.Gerencia.Split(" - ")[0].Trim() : req.Gerencia;

        string areaCode = "SINAREA";
        if (!string.IsNullOrWhiteSpace(req.Area))
        {
            var areaRow = _db.AreasTrabajo.FirstOrDefault(a => a.Nombre == req.Area);
            areaCode = areaRow?.CodigoPdf
                ?? Regex.Replace(req.Area, "[^A-Za-z0-9]", "").ToUpperInvariant();
            if (areaCode.Length > 4) areaCode = areaCode[..4];
            if (string.IsNullOrEmpty(areaCode)) areaCode = "SINAREA";
        }

        var semana = WeekYearCode(req.Fecha);
        return $"{gerenciaCode}-{areaCode}-PRIO-{semana}.pdf";
    }

    [HttpPost("generar")]
    public IActionResult Generar([FromBody] PrioritizacionGenerarRequest req)
    {
        var sections = req.Sections ?? new();
        var (total, nota) = PdfService.CalcScore(sections);

        var pdfBytes = _pdf.GenerarPrioritizacionPdf(req, nota, total);
        var filename = BuildFilename(req);

        // --- Guardar en disco ---
        var storageDir = _config["PdfStorageDir"] ?? Path.Combine(_env.ContentRootPath, "Storage", "pdf");
        Directory.CreateDirectory(storageDir);
        var fullPath = Path.Combine(storageDir, filename);
        System.IO.File.WriteAllBytes(fullPath, pdfBytes);

        // --- Guardar en BD ---
        var usuarioId = User.FindFirst(System.Security.Claims.ClaimTypes.NameIdentifier)?.Value
            ?? User.FindFirst("sub")?.Value;

        var reunion = new Reunion
        {
            DocType = "prioritization",
            Titulo = PrioritizacionSchema.Title,
            Fecha = req.Fecha,
            Hora = req.Hora,
            Area = req.Area,
            Gerencia = req.Gerencia,
            Superintendencia = req.Superintendencia,
            UsuarioId = usuarioId,
            PdfPath = fullPath,
            PdfFilename = filename,
            Nota = nota,
        };
        _db.Reuniones.Add(reunion);
        _db.SaveChanges();

        foreach (var c in req.Commitments ?? new())
        {
            if (string.IsNullOrWhiteSpace(c.Accion) && string.IsNullOrWhiteSpace(c.Responsable)) continue;
            _db.Compromisos.Add(new Compromiso
            {
                ReunionId = reunion.Id,
                Accion = c.Accion ?? "",
                Responsable = c.Responsable ?? "",
                FechaCompromiso = c.Fecha ?? "",
                Estado = c.Estado ?? "",
                Evidencia = c.Evidencia,
                Area = c.Area,
                ThreadId = string.IsNullOrWhiteSpace(c.ThreadId) ? null : c.ThreadId,
            });
        }

        foreach (var p in req.Participants ?? new())
        {
            if (string.IsNullOrWhiteSpace(p.Responsable)) continue;
            _db.Participantes.Add(new Participante
            {
                ReunionId = reunion.Id,
                Area = p.Area,
                Nombre = p.Responsable,
                Email = p.Email,
                Asistio = p.Asistio == "si" ? true : p.Asistio == "no" ? false : null,
                Conforme = p.Conforme == "si" ? true : p.Conforme == "no" ? false : null,
            });
        }
        _db.SaveChanges();

        return File(pdfBytes, "application/pdf", filename);
    }
}