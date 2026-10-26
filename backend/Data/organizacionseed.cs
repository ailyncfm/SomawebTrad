using Backend.Models;

namespace Backend.Data;

public static class OrganizacionSeed
{
    // Traducción directa de ORGANIZACION en app/data/organizacion.py
    public static readonly Dictionary<string, Dictionary<string, List<string>>> Data = new()
    {
        ["GFUN - Gerencia Fundición"] = new()
        {
            ["SFE - Suptcia. Planta de Flotación de Escoria"] = new() { "U. Planta Tratamiento de Escoria" },
            ["SPF - Suptcia. Procesos Fundición"] = new() { "U. Fusión Conversión", "U. Refinación y Moldeo" },
            ["SPLF - Suptcia. Plantas Fundición"] = new() { "U. Plantas Limpieza Gases", "U. Plantas Oxígeno y Nitrógeno" },
        },
        ["GMIN - Gerencia de Minas"] = new()
        {
            ["SMC - Suptcia. Mina Central"] = new() { "U. Esmeralda" },
            ["SMN - Suptcia. Mina Norte"] = new() { "U. Sub-6", "U. Teniente-7" },
            ["SMS - Suptcia. Mina Sur"] = new() { "Suptcia. Mina Sur", "U. Diablo Regimiento", "U. FFCC Teniente 5", "U. Operaciones Pacífico Superior" },
            ["STC - Suptcia. Transporte y Chancado"] = new() { "U. Chancado Primario", "U. FFCC Tte. 8" },
        },
        ["GPTA - Gerencia de Plantas"] = new()
        {
            ["SMP - Suptcia. de Mantenimiento Plantas"] = new() { "U. Mantención Chancado - GPTA", "U. Mantenimiento Filtros y Secado", "U. Mantenimiento Molibdeno", "U. Mantenimiento Planta Convencional", "U. Mantenimiento Planta SAG" },
            ["SPP - Suptcia. Productos Comerc"] = new() { "Suptcia. Productos Comerc" },
        },
        ["GRS - Gerencia Rajo - Sewell"] = new()
        {
            ["SMSS - Suptcia. Mantención y Servicios"] = new() { "U. Mantención Rajo-FFCC" },
            ["SOS - Suptcia. Operaciones Sewell"] = new() { "U. Mantención Sewell" },
        },
        ["GTRH - Gerencia Tranques Relaves y Rec. Hídricos"] = new()
        {
            ["SMRH - Supte. Mtto. Recursos Hídricos y Relaves"] = new() { "Supte. Mtto. Recursos Hídricos y Relaves" },
        },
    };

    public static readonly Dictionary<string, string> AreaCodes = new()
    {
        ["U. Planta Tratamiento de Escoria"] = "PTE",
        ["U. Fusión Conversión"] = "FUCO",
        ["U. Refinación y Moldeo"] = "REMO",
        ["U. Plantas Limpieza Gases"] = "PLG",
        ["U. Plantas Oxígeno y Nitrógeno"] = "POAN",
        ["U. Esmeralda"] = "ESM",
        ["U. Sub-6"] = "SUB6",
        ["U. Teniente-7"] = "TT7",
        ["Suptcia. Mina Sur"] = "MS",
        ["U. Diablo Regimiento"] = "DRG",
        ["U. FFCC Teniente 5"] = "TT5",
        ["U. Operaciones Pacífico Superior"] = "PS",
        ["U. Chancado Primario"] = "CHP",
        ["U. FFCC Tte. 8"] = "TT8",
        ["U. Mantención Chancado - GPTA"] = "CH",
        ["U. Mantenimiento Filtros y Secado"] = "FS",
        ["U. Mantenimiento Molibdeno"] = "MOLI",
        ["U. Mantenimiento Planta Convencional"] = "PMC",
        ["U. Mantenimiento Planta SAG"] = "SAG",
        ["Suptcia. Productos Comerc"] = "PCOM",
        ["U. Mantención Rajo-FFCC"] = "RFFCC",
        ["U. Mantención Sewell"] = "SW",
        ["Supte. Mtto. Recursos Hídricos y Relaves"] = "RHR",
    };

    public static void Seed(AppDbContext db)
    {
        if (db.Gerencias.Any()) return; // idempotente, igual que tu seed_organizacion.py

        foreach (var (gerenciaFull, supers) in Data)
        {
            var parts = gerenciaFull.Split(" - ", 2);
            var g = new Gerencia { Codigo = parts[0].Trim(), Nombre = parts[1].Trim() };
            db.Gerencias.Add(g);
            db.SaveChanges();

            foreach (var (superFull, areas) in supers)
            {
                var sParts = superFull.Split(" - ", 2);
                var s = new Superintendencia { GerenciaId = g.Id, Codigo = sParts[0].Trim(), Nombre = sParts[1].Trim() };
                db.Superintendencias.Add(s);
                db.SaveChanges();

                foreach (var areaNombre in areas)
                {
                    db.AreasTrabajo.Add(new AreaTrabajo
                    {
                        SuperintendenciaId = s.Id,
                        Nombre = areaNombre,
                        CodigoPdf = AreaCodes.GetValueOrDefault(areaNombre),
                    });
                }
                db.SaveChanges();
            }
        }
    }
}