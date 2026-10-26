using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Mvc;
using Backend.Data;
using Backend.Models;

namespace Backend.Controllers;

[ApiController]
[Route("api/admin/reuniones")]
[Authorize]
public class AdminReunionesController : ControllerBase
{
    private readonly AppDbContext _db;
    private readonly UserManager<ApplicationUser> _userManager;

    private static readonly Dictionary<string, string> DocLabels = new()
    {
        ["prioritization"] = "Priorización",
        ["planning"] = "Planificación",
        ["scheduling"] = "Programación",
        ["post"] = "Post Mantención",
        ["process_5s"] = "Conciliación SEP4",
    };

    public AdminReunionesController(AppDbContext db, UserManager<ApplicationUser> userManager)
    {
        _db = db; _userManager = userManager;
    }

    private bool CurrentIsAdmin() =>
        User.FindFirst(System.Security.Claims.ClaimTypes.Role)?.Value == "admin";

    [HttpGet]
    public IActionResult List([FromQuery] string? tipo, [FromQuery] string? usuarioId)
    {
        if (!CurrentIsAdmin()) return Forbid();

        var query = _db.Reuniones.AsQueryable();
        if (!string.IsNullOrWhiteSpace(tipo)) query = query.Where(r => r.DocType == tipo);
        if (!string.IsNullOrWhiteSpace(usuarioId)) query = query.Where(r => r.UsuarioId == usuarioId);

        var reuniones = query.OrderByDescending(r => r.CreatedAt).ToList();
        var userIds = reuniones.Where(r => r.UsuarioId != null).Select(r => r.UsuarioId!).Distinct().ToList();
        var usuarios = _userManager.Users.Where(u => userIds.Contains(u.Id))
            .ToDictionary(u => u.Id, u => new { u.Nombre, u.Email });

        var result = reuniones.Select(r => new
        {
            id = r.Id,
            docType = r.DocType,
            docTypeLabel = DocLabels.TryGetValue(r.DocType, out var lbl) ? lbl : r.DocType,
            titulo = r.Titulo,
            fecha = r.Fecha,
            area = r.Area,
            usuarioNombre = (r.UsuarioId != null && usuarios.ContainsKey(r.UsuarioId)) ? usuarios[r.UsuarioId].Nombre : null,
            usuarioEmail = (r.UsuarioId != null && usuarios.ContainsKey(r.UsuarioId)) ? usuarios[r.UsuarioId].Email : null,
            createdAt = r.CreatedAt,
            hasPdf = !string.IsNullOrEmpty(r.PdfPath),
        });

        return Ok(result);
    }

    [HttpGet("usuarios")]
    public IActionResult UsuariosFiltro()
    {
        if (!CurrentIsAdmin()) return Forbid();
        var usuarios = _userManager.Users
            .OrderBy(u => u.Nombre)
            .Select(u => new { id = u.Id, nombre = u.Nombre, email = u.Email })
            .ToList();
        return Ok(usuarios);
    }

    [HttpGet("{id}/descargar")]
    public IActionResult Descargar(int id)
    {
        if (!CurrentIsAdmin()) return Forbid();

        var reunion = _db.Reuniones.Find(id);
        if (reunion == null || string.IsNullOrEmpty(reunion.PdfPath) || !System.IO.File.Exists(reunion.PdfPath))
            return NotFound();

        var bytes = System.IO.File.ReadAllBytes(reunion.PdfPath);
        var filename = reunion.PdfFilename ?? Path.GetFileName(reunion.PdfPath);
        return File(bytes, "application/pdf", filename);
    }
}