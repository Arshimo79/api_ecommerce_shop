from rest_framework import permissions


class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        elif request.method == "DELETE":
            return bool(request.user and request.user.has_perm('shop.delete_comment'))
        return bool(request.user and request.user.is_authenticated)
