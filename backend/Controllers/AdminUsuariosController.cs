using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Mvc;
using Backend.Data;
using Backend.Models;

namespace Backend.Controllers;

[ApiController]
[Route("api/admin/usuarios")]
[Authorize]
public class AdminUsuariosController : ControllerBase
{
    private readonly UserManager<ApplicationUser> _userManager;
    private readonly AppDbContext _db;

    public AdminUsuariosController(UserManager<ApplicationUser> userManager, AppDbContext db)
    {
        _userManager = userManager;
        _db = db;
    }

    private bool CurrentIsAdmin() =>
        User.FindFirst(System.Security.Claims.ClaimTypes.Role)?.Value == "admin";

    private string? CurrentUserId() =>
        User.FindFirst(System.Security.Claims.ClaimTypes.NameIdentifier)?.Value
        ?? User.FindFirst("sub")?.Value;

    [HttpGet]
    public IActionResult List([FromQuery] string? q)
    {
        if (!CurrentIsAdmin()) return Forbid();

        var query = _userManager.Users.AsQueryable();
        if (!string.IsNullOrWhiteSpace(q))
        {
            var term = q.Trim().ToLower();
            query = query.Where(u =>
                (u.Nombre ?? "").ToLower().Contains(term) ||
                (u.Email ?? "").ToLower().Contains(term));
        }

        var usuarios = query.OrderBy(u => u.Nombre).ToList();
        var idsConReuniones = _db.Reuniones.Select(r => r.UsuarioId).Distinct().ToHashSet();

        var result = usuarios.Select(u => new
        {
            id = u.Id,
            nombre = u.Nombre,
            email = u.Email,
            rol = u.Rol,
            isActiveAccount = u.IsActiveAccount,
            createdAt = u.CreatedAt,
            hasReuniones = idsConReuniones.Contains(u.Id),
        });

        return Ok(result);
    }

    [HttpPost("{id}/toggle-active")]
    public async Task<IActionResult> ToggleActive(string id)
    {
        if (!CurrentIsAdmin()) return Forbid();
        if (id == CurrentUserId()) return BadRequest(new { error = "No puedes modificar tu propia cuenta." });

        var user = await _userManager.FindByIdAsync(id);
        if (user == null) return NotFound();

        user.IsActiveAccount = !user.IsActiveAccount;
        await _userManager.UpdateAsync(user);
        return Ok(new { isActiveAccount = user.IsActiveAccount });
    }

    [HttpPost("{id}/toggle-role")]
    public async Task<IActionResult> ToggleRole(string id)
    {
        if (!CurrentIsAdmin()) return Forbid();
        if (id == CurrentUserId()) return BadRequest(new { error = "No puedes modificar tu propia cuenta." });

        var user = await _userManager.FindByIdAsync(id);
        if (user == null) return NotFound();

        user.Rol = user.Rol == "admin" ? "usuario" : "admin";
        await _userManager.UpdateAsync(user);
        return Ok(new { rol = user.Rol });
    }

    [HttpDelete("{id}")]
    public async Task<IActionResult> Delete(string id)
    {
        if (!CurrentIsAdmin()) return Forbid();
        if (id == CurrentUserId()) return BadRequest(new { error = "No puedes eliminar tu propia cuenta." });

        if (_db.Reuniones.Any(r => r.UsuarioId == id))
            return BadRequest(new { error = "No se puede eliminar: el usuario tiene reuniones asociadas." });

        var user = await _userManager.FindByIdAsync(id);
        if (user == null) return NotFound();

        await _userManager.DeleteAsync(user);
        return Ok();
    }
}