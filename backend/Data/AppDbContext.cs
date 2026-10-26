using Microsoft.AspNetCore.Identity.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore;
using Backend.Models;

namespace Backend.Data;

public class AppDbContext : IdentityDbContext<ApplicationUser>
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }

    public DbSet<RevokedToken> RevokedTokens => Set<RevokedToken>();
    public DbSet<Gerencia> Gerencias => Set<Gerencia>();
    public DbSet<Superintendencia> Superintendencias => Set<Superintendencia>();
    public DbSet<AreaTrabajo> AreasTrabajo => Set<AreaTrabajo>();
    public DbSet<Reunion> Reuniones => Set<Reunion>();
    public DbSet<Compromiso> Compromisos => Set<Compromiso>();
    public DbSet<Participante> Participantes => Set<Participante>();

    protected override void OnModelCreating(ModelBuilder builder)
    {
        base.OnModelCreating(builder);
        builder.Entity<RevokedToken>().HasIndex(r => r.Jti).IsUnique();
    }
}