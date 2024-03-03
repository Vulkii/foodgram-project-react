from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminOrReadOnly(BasePermission):

    def has_permission(self, request, view):
        return (request.method in SAFE_METHODS
                or request.user.is_staff)


class IsAuthorOrReadOnly(BasePermission):

    def has_permission(self, request, view):
        return (request.method in SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return obj.author == request.user


class AllowAnyOrIsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method == 'POST' or 'PUT' or 'PATCH':
            return True
        return request.method in ('GET', 'HEAD', 'OPTIONS') or request.user and request.user.is_staff
