from rest_framework.permissions import BasePermission

class IsNotAuthenticated(BasePermission):
    """
    Allows access only to unauthenticated users.
    """
    message = "You are already authenticated. Please log out to access this page."

    def has_permission(self, request, view):
        return not request.user.is_authenticated
