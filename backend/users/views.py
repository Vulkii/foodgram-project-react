from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.pagination import CustomPagination
from api.serializers import CustomUserSerializer, SubscriptionSerializer
from .models import Subscription

User = get_user_model()


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPagination

    def get_permissions(self):

        if (self.action == 'subscriptions'
           or self.action == 'subscribe' or self.action == 'unsubscribe'):
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def me(self, request):
        user = request.user
        if isinstance(user, AnonymousUser):
            return Response({"error":
                            ('You should be autorized'
                             'to get access to this page.')},
                            status=status.HTTP_401_UNAUTHORIZED)

        serializer = CustomUserSerializer(user, context={'request': request})
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['get'],
    )
    def subscriptions(self, request):
        user = request.user
        queryset = User.objects.filter(subscribing__user=user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(pages,
                                            many=True,
                                            context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post'],
    )
    def subscribe(self, request, **kwargs):
        user = request.user
        author_id = self.kwargs.get('id')
        author = get_object_or_404(User, id=author_id)

        serializer = SubscriptionSerializer(author,
                                            data=request.data,
                                            context={"request": request})
        serializer.is_valid(raise_exception=True)
        Subscription.objects.create(user=user, author=author)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=['delete'],
        permission_classes=[IsAuthenticated]
    )
    def unsubscribe(self, request, **kwargs):
        user = request.user
        author_id = self.kwargs.get('id')
        author = get_object_or_404(User, id=author_id)

        subscription = get_object_or_404(Subscription,
                                         user=user,
                                         author=author)
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
