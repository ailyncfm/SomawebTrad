using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.RateLimiting;
using System.IdentityModel.Tokens.Jwt;
using Backend.Data;
using Backend.DTOs;
using Backend.Models;
using Backend.Services;

namespace Backend.Controllers;

[ApiController]
[Route("api/auth")]
public class AuthController : ControllerBase
{
    private readonly UserManager<ApplicationUser> _userManager;
    private readonly SignInManager<ApplicationUser> _signInManager;
    private readonly TokenService _tokenService;
    private readonly AppDbContext _db;
    private readonly IWebHostEnvironment _env;

    public AuthController(
        UserManager<ApplicationUser> userManager,
        SignInManager<ApplicationUser> signInManager,
        TokenService tokenService,
        AppDbContext db,
        IWebHostEnvironment env)
    {
        _userManager = userManager;
        _signInManager = signInManager;
        _tokenService = tokenService;
        _db = db;
        _env = env;
    }

    private void SetAuthCookie(string token, DateTime expires)
    {
        Response.Cookies.Append("access_token", token, new CookieOptions
        {
            HttpOnly = true,
            Secure = !_env.IsDevelopment(), // true en producción (HTTPS real)
            SameSite = SameSiteMode.Lax,
            Expires = expires,
            Path = "/",
        });
    }

    [HttpPost("registro")]
    [EnableRateLimiting("register")]
    public async Task<IActionResult> Registro(RegisterRequest req)
    {
        var email = req.Email.Trim().ToLowerInvariant();

        if (req.Password != req.Password2)
            return BadRequest(new { error = "Las contraseñas no coinciden." });

        var existing = await _userManager.FindByEmailAsync(email);
        if (existing != null)
            return BadRequest(new { error = "Ya existe una cuenta con ese correo." });

        var user = new ApplicationUser
        {
            UserName = email,
            Email = email,
            Nombre = req.Nombre.Trim(),
            Rol = "usuario",
            IsActiveAccount = true,
        };

        var result = await _userManager.CreateAsync(user, req.Password);
        if (!result.Succeeded)
            return BadRequest(new { error = string.Join(" ", result.Errors.Select(e => e.Description)) });

        var (token, _, expires) = _tokenService.GenerateToken(user);
        SetAuthCookie(token, expires);

        return Ok(new AuthResponse(user.Email!, user.Nombre!, user.Rol));
    }

    [HttpPost("login")]
    [EnableRateLimiting("login")]
    public async Task<IActionResult> Login(LoginRequest req)
    {
        var email = req.Email.Trim().ToLowerInvariant();
        var user = await _userManager.FindByEmailAsync(email);

        // Mensaje genérico siempre, sin revelar si el correo existe (control #8)
        const string genericError = "Correo o contraseña incorrectos.";

        if (user == null)
            return Unauthorized(new { error = genericError });

        if (await _userManager.IsLockedOutAsync(user))
            return StatusCode(423, new { error = "Cuenta bloqueada temporalmente por intentos fallidos. Intenta en unos minutos." });

        var passwordOk = await _userManager.CheckPasswordAsync(user, req.Password);
        if (!passwordOk)
        {
            await _userManager.AccessFailedAsync(user); // cuenta para el lockout (5 intentos -> 15 min, control #28)
            return Unauthorized(new { error = genericError });
        }

        if (!user.IsActiveAccount)
            return StatusCode(403, new { error = "Esta cuenta está deshabilitada. Contacta a un administrador." });

        await _userManager.ResetAccessFailedCountAsync(user);

        var (token, _, expires) = _tokenService.GenerateToken(user);
        SetAuthCookie(token, expires);

        return Ok(new AuthResponse(user.Email!, user.Nombre!, user.Rol));
    }

    [HttpPost("logout")]
    [Authorize]
    public async Task<IActionResult> Logout()
    {
        // Invalidación real server-side (control #13): el jti del token actual
        // queda en lista negra hasta su expiración natural.
        var jti = User.FindFirst(JwtRegisteredClaimNames.Jti)?.Value;
        var expClaim = User.FindFirst(JwtRegisteredClaimNames.Exp)?.Value;

        if (jti != null && expClaim != null && long.TryParse(expClaim, out var expUnix))
        {
            _db.RevokedTokens.Add(new RevokedToken
            {
                Jti = jti,
                ExpiresAt = DateTimeOffset.FromUnixTimeSeconds(expUnix).UtcDateTime,
            });
            await _db.SaveChangesAsync();
        }

        Response.Cookies.Delete("access_token");
        return Ok();
    }

    [HttpGet("me")]
    [Authorize]
    public IActionResult Me()
    {
        var email = User.FindFirst(System.Security.Claims.ClaimTypes.Email)?.Value ?? "";
        var nombre = User.FindFirst(System.Security.Claims.ClaimTypes.Name)?.Value ?? "";
        var rol = User.FindFirst(System.Security.Claims.ClaimTypes.Role)?.Value ?? "usuario";
        return Ok(new AuthResponse(email, nombre, rol));
    }
}