// Comportamento mínimo das telas (spec 002): adicionar linha em formset e mostrar seções
// conforme o rádio escolhido. Tudo funciona sem JavaScript, só com menos conforto.
document.addEventListener("click", (event) => {
  const button = event.target.closest("[data-formset-add]");
  if (!button) return;
  const prefix = button.dataset.formsetAdd;
  const total = document.getElementById(`id_${prefix}-TOTAL_FORMS`);
  const template = document.getElementById(`${prefix}-empty`);
  const row = template.innerHTML.replace(/__prefix__/g, total.value);
  document.getElementById(`${prefix}-rows`).insertAdjacentHTML("beforeend", row);
  total.value = Number(total.value) + 1;
});

function updateConditionalSections() {
  document.querySelectorAll("[data-show-if]").forEach((section) => {
    const [name, values] = section.dataset.showIf.split("=");
    const checked = document.querySelector(`input[name="${name}"]:checked`);
    const visible = checked && values.split("|").includes(checked.value);
    section.classList.toggle("d-none", !visible);
  });
}

document.addEventListener("change", updateConditionalSections);
document.addEventListener("DOMContentLoaded", updateConditionalSections);
