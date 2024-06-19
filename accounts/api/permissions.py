from rest_framework.permissions import BasePermission


class IsSuperUser(BasePermission):
    """
    Allows access only to superuser users.
    """

    def has_permission(self, request, view):
        # Check if the user making the request is a superuser
        return bool(request.user and request.user.is_superuser)
