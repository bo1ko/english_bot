from django.http import HttpResponseForbidden
from functools import wraps


def role_required(roles):
    if isinstance(roles, str):
        roles = [roles]

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not hasattr(request.user, "role") or request.user.role not in roles:
                return HttpResponseForbidden(
                    "You do not have permission to view this page."
                )
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator