from django.contrib.auth import get_user_model
from .models import Subscription
from djoser.views import UserViewSet
from api.serializers import CustomUserSerializer, SubscriptionSerializer
from api.pagination import CustomPagination
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework import status


User = get_user_model()


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPagination

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
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
        permission_classes=[IsAuthenticated]
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
