from .permissions import is_workspace_admin


def workspace_permissions(request):
    return {"is_workspace_admin": is_workspace_admin(request.user)}
