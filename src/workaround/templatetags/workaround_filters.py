from django import template

register = template.Library()

@register.filter
def get_by_department(items, department_name):
    """Возвращает первый элемент с указанным названием отдела."""
    for item in items:
        if item.department.name == department_name:
            return item
    return None