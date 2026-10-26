using Microsoft.AspNetCore.Identity;

namespace Backend.Models;

public class ApplicationUser : IdentityUser
{
    public string? Nombre { get; set; }
    public string Rol { get; set; } = "usuario";
    public bool IsActiveAccount { get; set; } = true;
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public bool IsAdmin => Rol == "admin";
}

public class RevokedToken
{
    public int Id { get; set; }
    public string Jti { get; set; } = "";
    public DateTime ExpiresAt { get; set; }
}

