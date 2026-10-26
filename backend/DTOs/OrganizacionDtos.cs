namespace Backend.DTOs;

public record CrearGerenciaRequest(string Codigo, string Nombre);
public record CrearSuperintendenciaRequest(int GerenciaId, string Codigo, string Nombre);
public record CrearAreaRequest(int SuperintendenciaId, string Nombre, string? CodigoPdf);