using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Text;
using Microsoft.IdentityModel.Tokens;
using Backend.Models;

namespace Backend.Services;

public class TokenService
{
    private readonly IConfiguration _config;
    public TokenService(IConfiguration config) => _config = config;

    public (string token, string jti, DateTime expires) GenerateToken(ApplicationUser user)
    {
        var jti = Guid.NewGuid().ToString();
        var expires = DateTime.UtcNow.AddMinutes(30); // mismo criterio que PERMANENT_SESSION_LIFETIME de Flask

        var claims = new List<Claim>
        {
            new(JwtRegisteredClaimNames.Sub, user.Id),
            new(JwtRegisteredClaimNames.Jti, jti),
            new(ClaimTypes.Email, user.Email ?? ""),
            new(ClaimTypes.Name, user.Nombre ?? ""),
            new(ClaimTypes.Role, user.Rol),
        };

        var key = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(_config["Jwt:Key"]!));
        var creds = new SigningCredentials(key, SecurityAlgorithms.HmacSha256);

        var token = new JwtSecurityToken(
            issuer: _config["Jwt:Issuer"],
            audience: _config["Jwt:Audience"],
            claims: claims,
            expires: expires,
            signingCredentials: creds
        );

        return (new JwtSecurityTokenHandler().WriteToken(token), jti, expires);
    }
}