from django import template

register = template.Library()

@register.filter
def label_attr(value, arg):
    return value.label_tag(attrs={'class': arg})

@register.filter
def label_style(value, arg):
    return value.label_tag(attrs={'style': arg})
