"""Template filters for comment edit/delete permissions."""

from django import template
from django.contrib.auth.models import User

register = template.Library()


@register.filter
def can_edit_comment(comment, user: User) -> bool:
    """Return True if *user* can edit *comment* (owner, within 24h, not deleted)."""
    return comment.can_be_edited_by(user)


@register.filter
def can_delete_comment(comment, user: User) -> bool:
    """Return True if *user* can delete *comment* (owner or staff, not deleted)."""
    return comment.can_be_deleted_by(user)
