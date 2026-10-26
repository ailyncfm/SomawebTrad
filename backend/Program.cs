using System.Text;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.RateLimiting;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;
using System.IdentityModel.Tokens.Jwt;
using System.Threading.RateLimiting;
using Backend.Data;
using Backend.Models;
using Backend.Services;

var builder = WebApplication.CreateBuilder(args);

// --- Base de datos ---
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseSqlite(builder.Configuration.GetConnectionString("DefaultConnection")
        ?? "Data Source=somaweb.db"));

// --- Identity (hashing, lockout, politica de password) ---
builder.Services.AddIdentity<ApplicationUser, IdentityRole>(options =>
{
    options.Password.RequiredLength = 10;          // norma IT-TI-001_REV03
    options.Password.RequireDigit = false;
    options.Password.RequireLowercase = false;
    options.Password.RequireUppercase = false;
    options.Password.RequireNonAlphanumeric = false; // no restringe caracteres especiales (control #2)

    options.Lockout.MaxFailedAccessAttempts = 5;
    options.Lockout.DefaultLockoutTimeSpan = TimeSpan.FromMinutes(15); // control #28

    options.User.RequireUniqueEmail = true;
})
    .AddEntityFrameworkStores<AppDbContext>()
    .AddDefaultTokenProviders();

// --- JWT en cookie (control #9) ---
var jwtKey = builder.Configuration["Jwt:Key"]!;
builder.Services.AddAuthentication(options =>
{
    options.DefaultAuthenticateScheme = JwtBearerDefaults.AuthenticationScheme;
    options.DefaultChallengeScheme = JwtBearerDefaults.AuthenticationScheme;
})
.AddJwtBearer(options =>
{
    options.TokenValidationParameters = new TokenValidationParameters
    {
        ValidateIssuer = true,
        ValidateAudience = true,
        ValidateLifetime = true,
        ValidateIssuerSigningKey = true,
        ValidIssuer = builder.Configuration["Jwt:Issuer"],
        ValidAudience = builder.Configuration["Jwt:Audience"],
        IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(jwtKey)),
        ClockSkew = TimeSpan.Zero,
    };

    options.Events = new JwtBearerEvents
    {
        // Lee el JWT desde la cookie httpOnly en vez del header Authorization
        OnMessageReceived = context =>
        {
            if (context.Request.Cookies.TryGetValue("access_token", out var token))
                context.Token = token;
            return Task.CompletedTask;
        },
        // Verifica que el token no haya sido invalidado por logout (control #13)
        OnTokenValidated = async context =>
        {
            var jti = context.Principal?.FindFirst(JwtRegisteredClaimNames.Jti)?.Value;
            if (jti == null) { context.Fail("Token inválido."); return; }

            var db = context.HttpContext.RequestServices.GetRequiredService<AppDbContext>();
            var revoked = await db.RevokedTokens.AnyAsync(r => r.Jti == jti);
            if (revoked) context.Fail("Token invalidado (sesión cerrada).");
        },
    };
});

builder.Services.AddAuthorization();
builder.Services.AddScoped<TokenService>();

// --- Rate limiting nativo (controles #26, #27, #28) ---
builder.Services.AddRateLimiter(options =>
{
    options.OnRejected = async (context, token) =>
    {
        context.HttpContext.Response.StatusCode = 429; // control #27
        await context.HttpContext.Response.WriteAsJsonAsync(
            new { error = "Demasiados intentos. Espera unos minutos antes de volver a intentar." }, token);
    };

    options.AddFixedWindowLimiter("login", o =>
    {
        o.PermitLimit = 5;
        o.Window = TimeSpan.FromMinutes(15); // 5 intentos / 15 min
        o.QueueLimit = 0;
    });

    options.AddFixedWindowLimiter("register", o =>
    {
        o.PermitLimit = 10;
        o.Window = TimeSpan.FromHours(1); // 10 / hora
        o.QueueLimit = 0;
    });
});

// --- CORS para Angular (dev server) ---
var angularOrigin = builder.Configuration["AngularOrigin"] ?? "http://localhost:4200";
builder.Services.AddCors(options =>
{
    options.AddPolicy("Angular", policy =>
    {
        policy.WithOrigins(angularOrigin)
              .AllowAnyHeader()
              .AllowAnyMethod()
              .AllowCredentials()
              .WithExposedHeaders("Content-Disposition"); // para que el navegador deje leer el nombre del archivo
    });
});

builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

builder.Services.AddSingleton<PdfService>();

var app = builder.Build();

// --- Migraciones automáticas al iniciar (hasta que definamos pipeline propio) ---
using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
    db.Database.Migrate();
    OrganizacionSeed.Seed(db); // equivalente a tu flask seed-organizacion, pero automático al iniciar
}

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}
else
{
    app.UseHsts(); // control #44
}

// --- Headers de seguridad (controles #40-#47) ---
app.Use(async (context, next) =>
{
    context.Response.Headers.Remove("Server");
    context.Response.Headers["X-Content-Type-Options"] = "nosniff";
    context.Response.Headers["X-Frame-Options"] = "SAMEORIGIN";
    context.Response.Headers["Referrer-Policy"] = "same-origin";
    context.Response.Headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()";
    await next();
});

app.UseHttpsRedirection();
app.UseCors("Angular");
app.UseRateLimiter();
app.UseAuthentication();
app.UseAuthorization();
app.MapControllers();

app.Run();