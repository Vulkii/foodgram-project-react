from rest_framework.permissions import SAFE_METHODS, BasePermission


class AllowAnyOrIsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method == 'POST' or 'PUT' or 'PATCH':
            return True
        return (request.method in ('GET', 'HEAD', 'OPTIONS')
                or request.user and request.user.is_staff)


class IsAuthorOrAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        return obj.author == request.user or request.user.is_staff
