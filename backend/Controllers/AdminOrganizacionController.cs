using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Backend.Data;
using Backend.DTOs;
using Backend.Models;

namespace Backend.Controllers;

[ApiController]
[Route("api/admin/organizacion")]
[Authorize]
public class AdminOrganizacionController : ControllerBase
{
    private readonly AppDbContext _db;
    public AdminOrganizacionController(AppDbContext db) { _db = db; }

    private bool CurrentIsAdmin() =>
        User.FindFirst(System.Security.Claims.ClaimTypes.Role)?.Value == "admin";

    [HttpGet]
    public IActionResult GetTree()
    {
        if (!CurrentIsAdmin()) return Forbid();

        var gerencias = _db.Gerencias
            .Include(g => g.Superintendencias).ThenInclude(s => s.Areas)
            .OrderBy(g => g.Codigo)
            .Select(g => new
            {
                id = g.Id,
                codigo = g.Codigo,
                nombre = g.Nombre,
                nombreCompleto = g.NombreCompleto,
                superintendencias = g.Superintendencias
                    .OrderBy(s => s.Codigo)
                    .Select(s => new
                    {
                        id = s.Id,
                        codigo = s.Codigo,
                        nombre = s.Nombre,
                        nombreCompleto = s.NombreCompleto,
                        areas = s.Areas.OrderBy(a => a.Nombre).Select(a => new
                        {
                            id = a.Id,
                            nombre = a.Nombre,
                            codigoPdf = a.CodigoPdf,
                        }),
                    }),
            })
            .ToList();

        return Ok(gerencias);
    }

    [HttpPost("gerencias")]
    public IActionResult CrearGerencia([FromBody] CrearGerenciaRequest req)
    {
        if (!CurrentIsAdmin()) return Forbid();
        if (string.IsNullOrWhiteSpace(req.Codigo) || string.IsNullOrWhiteSpace(req.Nombre))
            return BadRequest(new { error = "Código y nombre son obligatorios." });

        _db.Gerencias.Add(new Gerencia { Codigo = req.Codigo.Trim(), Nombre = req.Nombre.Trim() });
        _db.SaveChanges();
        return Ok();
    }

    [HttpDelete("gerencias/{id}")]
    public IActionResult EliminarGerencia(int id)
    {
        if (!CurrentIsAdmin()) return Forbid();
        var g = _db.Gerencias.Find(id);
        if (g == null) return NotFound();
        _db.Gerencias.Remove(g);
        _db.SaveChanges();
        return Ok();
    }

    [HttpPost("superintendencias")]
    public IActionResult CrearSuperintendencia([FromBody] CrearSuperintendenciaRequest req)
    {
        if (!CurrentIsAdmin()) return Forbid();
        if (string.IsNullOrWhiteSpace(req.Codigo) || string.IsNullOrWhiteSpace(req.Nombre))
            return BadRequest(new { error = "Código y nombre son obligatorios." });

        _db.Superintendencias.Add(new Superintendencia
        {
            GerenciaId = req.GerenciaId,
            Codigo = req.Codigo.Trim(),
            Nombre = req.Nombre.Trim(),
        });
        _db.SaveChanges();
        return Ok();
    }

    [HttpDelete("superintendencias/{id}")]
    public IActionResult EliminarSuperintendencia(int id)
    {
        if (!CurrentIsAdmin()) return Forbid();
        var s = _db.Superintendencias.Find(id);
        if (s == null) return NotFound();
        _db.Superintendencias.Remove(s);
        _db.SaveChanges();
        return Ok();
    }

    [HttpPost("areas")]
    public IActionResult CrearArea([FromBody] CrearAreaRequest req)
    {
        if (!CurrentIsAdmin()) return Forbid();
        if (string.IsNullOrWhiteSpace(req.Nombre))
            return BadRequest(new { error = "El nombre del área es obligatorio." });

        _db.AreasTrabajo.Add(new AreaTrabajo
        {
            SuperintendenciaId = req.SuperintendenciaId,
            Nombre = req.Nombre.Trim(),
            CodigoPdf = string.IsNullOrWhiteSpace(req.CodigoPdf) ? null : req.CodigoPdf.Trim(),
        });
        _db.SaveChanges();
        return Ok();
    }

    [HttpDelete("areas/{id}")]
    public IActionResult EliminarArea(int id)
    {
        if (!CurrentIsAdmin()) return Forbid();
        var a = _db.AreasTrabajo.Find(id);
        if (a == null) return NotFound();
        _db.AreasTrabajo.Remove(a);
        _db.SaveChanges();
        return Ok();
    }
}