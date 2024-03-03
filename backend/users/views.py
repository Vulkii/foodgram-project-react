from django.shortcuts import render
from django.contrib.auth import get_user_model
from .models import Subscription
from djoser.views import UserViewSet
from api.serializers import CustomUserSerializer
from api.pagination import CustomPagination
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


User = get_user_model()


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPagination

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            return super(CustomUserViewSet, self).get_permissions()
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def me(self, request):
        user = request.user
        serializer = self.get_serializer(user, context={'request': request})
        return Response(serializer.data)
