using System.ComponentModel.DataAnnotations;

namespace Backend.DTOs;

public record RegisterRequest(
    [Required, EmailAddress] string Email,
    [Required] string Nombre,
    [Required, MinLength(10, ErrorMessage = "La contraseña debe tener al menos 10 caracteres.")] string Password,
    [Required] string Password2
);

public record LoginRequest(
    [Required, EmailAddress] string Email,
    [Required] string Password
);

public record AuthResponse(string Email, string Nombre, string Rol);