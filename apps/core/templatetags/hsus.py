from django import template

register = template.Library()

CHECK_WIDGETS = {"checkbox", "radioselect", "checkboxselectmultiple"}


@register.filter
def bootstrap(field):
    """Renderiza o widget com as classes do Bootstrap 5."""
    if field.widget_type in CHECK_WIDGETS:
        css = "form-check-input"
    elif field.widget_type == "select":
        css = "form-select"
    else:
        css = "form-control"
    if field.errors:
        css += " is-invalid"
    return field.as_widget(attrs={"class": css})


@register.filter
def check_input(radio):
    """Uma opção de rádio (`{% for radio in field %}`) com a classe do Bootstrap."""
    radio.data["attrs"]["class"] = "form-check-input"
    return radio.tag()
