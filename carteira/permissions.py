from functools import wraps

from django.conf import settings
from django.http import HttpResponseForbidden


def is_workspace_admin(user):
    return bool(
        user.is_authenticated
        and (user.is_superuser or user.username.casefold() in settings.WORKSPACE_ADMIN_USERNAMES)
    )


def workspace_admin_required(view_function):
    @wraps(view_function)
    def wrapped(request, *args, **kwargs):
        if not is_workspace_admin(request.user):
            return HttpResponseForbidden("Acesso restrito ao administrador do workspace.")
        return view_function(request, *args, **kwargs)

    return wrapped
