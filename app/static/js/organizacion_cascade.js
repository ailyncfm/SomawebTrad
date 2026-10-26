// static/js/organizacion_cascade.js
// Desplegable en cascada Gerencia -> Superintendencia, usando
// window.ORGANIZACION (inyectado por base.html desde el servidor).

function initGerenciaSuperintendenciaSelects(gerenciaSelectId, superintendenciaSelectId){
  const gerSelect = document.getElementById(gerenciaSelectId);
  const superSelect = document.getElementById(superintendenciaSelectId);
  if(!gerSelect || !superSelect || !window.ORGANIZACION) return;

  function fillSuperintendencias(gerencia, preselect){
    superSelect.innerHTML = '<option value="">Selecciona...</option>';
    const supers = window.ORGANIZACION[gerencia] || {};
    Object.keys(supers).forEach(s => {
      const opt = document.createElement("option");
      opt.value = s;
      opt.textContent = s;
      if(s === preselect) opt.selected = true;
      superSelect.appendChild(opt);
    });
  }

  gerSelect.addEventListener("change", () => fillSuperintendencias(gerSelect.value, null));

  if(gerSelect.value){
    fillSuperintendencias(gerSelect.value, superSelect.dataset.preselect || "");
  }
}
function initGerenciaSuperintendenciaAreaSelects(gerenciaSelectId, superintendenciaSelectId, areaSelectId){
  const gerSelect = document.getElementById(gerenciaSelectId);
  const superSelect = document.getElementById(superintendenciaSelectId);
  const areaSelect = document.getElementById(areaSelectId);
  if(!gerSelect || !superSelect || !areaSelect || !window.ORGANIZACION) return;

  function fillAreas(gerencia, superintendencia, areaPreselect){
    areaSelect.innerHTML = '<option value="">Selecciona...</option>';
    const supers = window.ORGANIZACION[gerencia] || {};
    const areas = supers[superintendencia] || [];
    areas.forEach(a => {
      const opt = document.createElement("option");
      opt.value = a;
      opt.textContent = a;
      if(a === areaPreselect) opt.selected = true;
      areaSelect.appendChild(opt);
    });
  }

  function fillSuperintendencias(gerencia, superPreselect, areaPreselect){
    superSelect.innerHTML = '<option value="">Selecciona...</option>';
    const supers = window.ORGANIZACION[gerencia] || {};
    Object.keys(supers).forEach(s => {
      const opt = document.createElement("option");
      opt.value = s;
      opt.textContent = s;
      if(s === superPreselect) opt.selected = true;
      superSelect.appendChild(opt);
    });
    fillAreas(gerencia, superSelect.value, areaPreselect);
  }

  gerSelect.addEventListener("change", () => fillSuperintendencias(gerSelect.value, null, null));
  superSelect.addEventListener("change", () => fillAreas(gerSelect.value, superSelect.value, null));

  if(gerSelect.value){
    fillSuperintendencias(gerSelect.value, superSelect.dataset.preselect || "", areaSelect.dataset.preselect || "");
  }
}