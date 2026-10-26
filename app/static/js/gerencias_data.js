// Reemplazar con el listado real de gerencias/superintendencias.
const GERENCIAS_SUPERINTENDENCIAS = {
  "GERENCIA EJEMPLO 1": ["Superintendencia A", "Superintendencia B"],
  "GERENCIA EJEMPLO 2": ["Superintendencia C", "Superintendencia D", "Superintendencia E"],
};

function initGerenciaSuperintendenciaSelects(gerenciaSelectId, superintendenciaSelectId){
  const gerSelect = document.getElementById(gerenciaSelectId);
  const superSelect = document.getElementById(superintendenciaSelectId);
  if(!gerSelect || !superSelect) return;

  function fillSuperintendencias(gerencia, preselect){
    superSelect.innerHTML = '<option value="">Selecciona...</option>';
    (GERENCIAS_SUPERINTENDENCIAS[gerencia] || []).forEach(s => {
      const opt = document.createElement("option");
      opt.value = s;
      opt.textContent = s;
      if(s === preselect) opt.selected = true;
      superSelect.appendChild(opt);
    });
  }

  gerSelect.addEventListener("change", () => fillSuperintendencias(gerSelect.value, null));

  if(gerSelect.value){
    fillSuperintendencias(gerSelect.value, superSelect.dataset.preselect || null);
  }
}