namespace Backend.Data;

public static class PrioritizacionSchema
{
    public record ItemDef(string Question, List<string> Options);
    public record SectionDef(string Name, List<ItemDef> Items);

    public static readonly List<SectionDef> Sections = new()
    {
        new("Aspectos generales", new()
        {
            new("Ejecución: La reunión…", new() {
                "No se realizó y/o se reagendó",
                "Se realizó, pero tarde o se extendió",
                "Se realizó de acuerdo con el horario y la duración planificada" }),
            new("Asistencia: A la reunión asisten... (planificación, confiabilidad, operación, ej. mantenimiento, abastecimiento, EECC y prevencionistas)", new() {
                "No se presentaron más de 3 participantes claves",
                "Faltaron 1 -2 participantes claves",
                "Estaban todos los relevantes" }),
        }),
        new("Inputs", new()
        {
            new("Propuesta de confiabilidad (plan matriz y MonCon): Los ingenieros de confiabilidad y planificación...", new() {
                "No presentan una lista de actividades pre-priorizadas",
                "Presentan una lista de actividades pre-priorizadas, pero no está hecha en SAP",
                "Presentan una lista de actividades pre-priorizadas e identificadas en la plataforma SAP" }),
            new("Actividades fuera del sistema SAP:", new() {
                "Las otras áreas traen solicitudes de las tareas del sistema y SIN priorización",
                "Las otras áreas traen una lista ya priorizada",
                "No hay actividades propuestas fuera del sistema SAP" }),
        }),
        new("Desarrollo", new()
        {
            new("Propuesta base de confiabilidad: El equipo…", new() {
                "No revisa en conjunto la propuesta base",
                "La revisa en conjunto, pero no se solicita validación",
                "Revisa en conjunto la propuesta base y se confirma el acuerdo" }),
            new("Inclusión de actividades no consideradas: Las actividades propuestas…", new() {
                "No son revisadas en conjunto y se incluyen directamente en el programa",
                "Son presentadas, pero no se valida la priorización",
                "Son revisadas en conjunto y se valida su priorización" }),
            new("Cambios en prioridad según nivel de riesgo discutido: El equipo…", new() {
                "No discute los niveles de riesgo de las actividades",
                "Discute niveles de riesgo, pero no son considerados para la priorización",
                "Discute niveles de riesgo y realiza cambios en las prioridades de acuerdo con ello" }),
            new("Cierre: Los ingenieros de confiabilidad y planificación…", new() {
                "No solicitan a los participantes la confirmación de la lista priorizada de tareas",
                "Solicitan a los participantes la validación de la lista priorizada de tareas, pero no formalmente",
                "Solicitan a los participantes la validación formal de la lista priorizada de tareas" }),
            new("Priorización de equipos críticos: Los asistentes…", new() {
                "No conocen los equipos críticos y no son priorizados",
                "Conocen los equipos críticos, pero no son priorizados",
                "Conocen los equipos críticos y velan por su priorización" }),
            new("Generación de avisos: Para los asistentes…", new() {
                "La mayor parte de las tareas fuera del plan matriz no tienen un aviso generado",
                "Sólo algunas tareas se solicitan sin aviso",
                "El ingreso de tareas sin aviso es muy excepcional" }),
        }),
        new("Mentalidades y comportamientos", new()
        {
            new("Respeto por las reglas de la reunión: Los asistentes…", new() {
                "No dan importancia al cumplimiento de las reglas",
                "Uno o más integrantes no respeta las reglas y refleja una falta de entendimiento de la importancia de la reunión",
                "El equipo completo respeta las reglas y es reflejo de la importancia que dan a la reunión" }),
            new("Preparación: La preparación de la información refleja la importancia que dan los participantes a la priorización", new() {
                "La preparación necesaria es nula y se le da poca importancia en todo el equipo",
                "Uno o más asistentes no prepara la información y no entiende su importancia",
                "Todos aportan la información necesaria y de la manera esperada" }),
            new("Motivación a la priorización: El equipo entiende que el principal objetivo es la priorización", new() {
                "Se discute poco o nada de priorización",
                "La priorización se discute parcialmente",
                "El equipo cuestiona y analiza la priorización en cada etapa de la reunión" }),
            new("La comunicación: ¿La comunicación de los participantes refleja entendimiento y convicción?", new() {
                "Se observa lenguaje de desaprobación en el equipo",
                "Uno o más integrantes muestran lenguaje de desaprobación",
                "El equipo muestra un lenguaje positivo, colaborativo y alineado con el objetivo de la reunión" }),
        }),
    };

    public static readonly List<string> ParticipantAreas = new()
    {
        "CONFIABILIDAD", "PLANIFICADOR", "PROGRAMADOR", "EJECUTOR",
        "OPERACIONES", "GSYS", "ELÉCTRICOS", "ABASTECIMIENTO", "EECC", "OTRO",
    };

    public static readonly List<string> ChecklistQuestions = new()
    {
        "Las actividades revisadas fueron evaluadas considerando riesgos para las personas, equipos e instalaciones.",
        "Las interferencias y restricciones relevantes fueron identificadas durante la priorización.",
        "Las actividades con requerimientos especiales de seguridad fueron identificadas oportunamente.",
        "La priorización realizada considera los riesgos operacionales y de seguridad asociados.",
    };

    public const string Title = "Confirmación de rol - Reunión de Priorización SOMA";
}