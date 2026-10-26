namespace Backend.Models;

public class Gerencia
{
    public int Id { get; set; }
    public string Codigo { get; set; } = "";
    public string Nombre { get; set; } = "";
    public List<Superintendencia> Superintendencias { get; set; } = new();
    public string NombreCompleto => $"{Codigo} - {Nombre}";
}

public class Superintendencia
{
    public int Id { get; set; }
    public int GerenciaId { get; set; }
    public Gerencia? Gerencia { get; set; }
    public string Codigo { get; set; } = "";
    public string Nombre { get; set; } = "";
    public List<AreaTrabajo> Areas { get; set; } = new();
    public string NombreCompleto => $"{Codigo} - {Nombre}";
}

public class AreaTrabajo
{
    public int Id { get; set; }
    public int SuperintendenciaId { get; set; }
    public Superintendencia? Superintendencia { get; set; }
    public string Nombre { get; set; } = "";
    public string? CodigoPdf { get; set; }
}