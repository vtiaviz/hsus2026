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

// data-show-if="nome=valor1|valor2&outro=valor": mostra quando todas as condições batem.
// data-hide-if: o contrário.
function conditionsMatch(expression) {
  return expression.split("&").every((condition) => {
    const [name, values] = condition.split("=");
    const checked = document.querySelector(`input[name="${name}"]:checked`);
    return checked && values.split("|").includes(checked.value);
  });
}

function updateConditionalSections() {
  document.querySelectorAll("[data-show-if]").forEach((element) => {
    element.classList.toggle("d-none", !conditionsMatch(element.dataset.showIf));
  });
  document.querySelectorAll("[data-hide-if]").forEach((element) => {
    element.classList.toggle("d-none", conditionsMatch(element.dataset.hideIf));
  });
}

document.addEventListener("change", updateConditionalSections);
document.addEventListener("DOMContentLoaded", updateConditionalSections);
