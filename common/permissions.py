from rest_framework import permissions


class IsCreatorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow any authenticated user to view (GET/HEAD/OPTIONS),
    but only the creator to edit or delete the object.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the creator
        return getattr(obj, 'created_by', None) == request.user


class IsOwnerOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to view/edit it.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return getattr(obj, 'created_by', None) == request.user
