from django import template
from django.urls import reverse

register = template.Library()


@register.simple_tag
def url_template(url_name, placeholders="", **kwargs):
    """
    Generate a URL template with placeholders for JavaScript interpolation.

    Unlike Django's {% url %} tag which requires all parameters, this tag
    generates a URL pattern with {placeholder} syntax for parameters that
    will be filled in by JavaScript at runtime.

    Usage:
        {% url_template 'battycoda_app:edit_segment' placeholders='segment_id' segmentation_id=segmentation.id %}

    This produces: "/segmentations/123/segments/{segment_id}/edit/"

    For multiple placeholders:
        {% url_template 'battycoda_app:some_view' placeholders='param1,param2' fixed_param=value %}

    Args:
        url_name: The name of the URL pattern (e.g., 'battycoda_app:edit_segment')
        placeholders: Comma-separated list of parameter names to use as placeholders
        **kwargs: Fixed parameters to include in the URL

    Returns:
        A URL string with {placeholder} syntax for the specified parameters
    """
    # Parse placeholder names
    placeholder_names = [p.strip() for p in placeholders.split(",") if p.strip()]

    # Build kwargs with placeholder values (use a marker we can replace)
    url_kwargs = dict(kwargs)
    placeholder_marker = "__PLACEHOLDER_{}__"

    for name in placeholder_names:
        # Use 0 as a dummy value that will be replaced
        url_kwargs[name] = 0

    # Generate the URL with dummy values
    url = reverse(url_name, kwargs=url_kwargs)

    # Replace dummy values with placeholder syntax
    for name in placeholder_names:
        # Replace /0/ with /{name}/ - handles integer placeholders
        url = url.replace("/0/", "/{" + name + "}/", 1)

    return url


@register.filter
def get_item(dictionary, key):
    """
    Template filter to get an item from a dictionary by key

    Usage:
        {{ my_dict|get_item:key_var }}
    """
    return dictionary.get(key, "")


@register.filter
def add_class(field, css_class):
    """
    Template filter to add a CSS class to a form field

    Usage:
        {{ form.field|add_class:"form-control" }}
    """
    return field.as_widget(attrs={"class": css_class})


@register.filter
def div(value, arg):
    """
    Divides the value by the argument

    Usage:
        {{ value|div:arg }}
    """
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0


@register.filter
def mul(value, arg):
    """
    Multiplies the value by the argument

    Usage:
        {{ value|mul:arg }}
    """
    try:
        return float(value) * float(arg)
    except ValueError:
        return 0


@register.filter
def regroup_by(queryset, key_value):
    """
    Filter a queryset to only include items with a specific value

    Usage:
        {{ tasks|regroup_by:"completed" }}
    """
    result = []
    for item in queryset:
        if hasattr(item, "status") and item.status == key_value:
            result.append(item)
    return result


@register.filter
def count_by_status(queryset, status_value):
    """
    Count items in a queryset with a specific status

    Usage:
        {{ tasks|count_by_status:"completed" }}
    """
    count = 0
    for item in queryset:
        if hasattr(item, "status") and item.status == status_value:
            count += 1
    return count


@register.filter
def count_done(queryset):
    """
    Count items in a queryset that are marked as done

    Usage:
        {{ tasks|count_done }}
    """
    count = 0
    for item in queryset:
        if hasattr(item, "is_done") and item.is_done:
            count += 1
    return count


@register.filter
def multiply(value, arg):
    """
    Multiplies the value by the argument, similar to mul but works with template variable chains

    Usage:
        {{ value|multiply:100 }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def subtract(value, arg):
    """
    Subtracts the argument from the value

    Usage:
        {{ value|subtract:arg }}
    """
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0
