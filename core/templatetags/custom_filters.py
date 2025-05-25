from django import template
from django.utils.safestring import mark_safe
from django.utils.html import strip_tags

register = template.Library()

@register.filter
def truncatehtml(content, num_words):
    words = strip_tags(content).split()
    truncated_content = " ".join(words[:num_words])
    return mark_safe(truncated_content + ('...' if len(words) > num_words else ''))
