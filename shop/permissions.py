from rest_framework import permissions
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        elif request.method == "DELETE":
            return bool(request.user and request.user.has_perm('shop.delete_comment'))
        return bool(request.user and request.user.is_authenticated)


class IsOwnerOrReadOnly(BasePermission):
    """
    - GET permission for everyone
    - POST permission for users who has loged in
    - DELETE permission for users who created the review
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True  # GET, HEAD, OPTIONS

        if request.method == "POST":
            return request.user and request.user.is_authenticated

        if request.method == "DELETE":
            return request.user and request.user.is_authenticated

        return False

    def has_object_permission(self, request, view, obj):
        # Only owner of review be able to DELETE review
        if request.method == "DELETE":
            return obj.user == request.user

        return True
