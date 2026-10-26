namespace Backend.DTOs;

public record SeccionItemDto(string Question, List<string> Options, int Selected);
public record SeccionDto(string Name, List<SeccionItemDto> Items);
public record ChecklistItemDto(string Question, bool Si, bool No, string? Comentario);
public record ObservadorDto(string? Nombre, string? Gerencia, string? Superintendencia, string? Sap, string? Email, string? Posicion);
public record FeedbackDto(string? Fortalezas, string? Oportunidades, string? Plan);
public record CompromisoInDto(string Area, string Accion, string Responsable, string Fecha, string Estado, string? Evidencia, string? ThreadId);
public record ParticipanteInDto(string? Area, string Responsable, string? Email, string? Asistio, string? Conforme);

public record PrioritizacionGenerarRequest(
    string Fecha,
    string Hora,
    string? Gerencia,
    string? Superintendencia,
    string? Area,
    List<ObservadorDto>? Observadores,
    List<SeccionDto> Sections,
    List<ChecklistItemDto>? Checklist,
    FeedbackDto? Feedback,
    List<CompromisoInDto>? Commitments,
    List<ParticipanteInDto>? Participants
);

public record CompromisoAbiertoDto(string ThreadId, string Accion, string Responsable, string Fecha, string Estado, bool Vencido);