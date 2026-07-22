"""Template filters for comment permissions and reactions."""

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


@register.filter
def get_reaction_count(data, args: str) -> int:
    """Look up a reaction count from comment_reaction_data.

    Usage: ``{{ comment_reaction_data|get_reaction_count:"comment_id,likes" }}``
    """
    comment_id_str, field = args.split(",", 1)
    comment_id = int(comment_id_str)
    entry = data.get(comment_id)
    if entry is None:
        return 0
    if field == "likes":
        return entry[0]
    if field == "dislikes":
        return entry[1]
    return 0


@register.filter
def get_user_reaction(data, comment_id) -> int | None:
    """Look up the current user's reaction from comment_reaction_data.

    Usage: ``{{ comment_reaction_data|get_user_reaction:comment.id }}``
    """
    entry = data.get(int(comment_id))
    if entry is None:
        return None
    return entry[2]


@register.simple_tag
def reaction_count(data, comment, field: str) -> int:
    """Get a reaction count for a comment from the reaction data dict.

    Usage: ``{% reaction_count comment_reaction_data comment "likes" as likes %}``
    """
    entry = data.get(comment.id)
    if entry is None:
        return 0
    if field == "likes":
        return entry[0]
    if field == "dislikes":
        return entry[1]
    return 0


@register.simple_tag
def user_reaction_value(data, comment):
    """Get the current user's reaction value for a comment.

    Usage: ``{% user_reaction_value comment_reaction_data comment as urx %}``
    """
    entry = data.get(comment.id)
    if entry is None:
        return None
    return entry[2]
