from django.shortcuts import render
from django.contrib.auth import get_user_model
from .models import Subscription
from djoser.views import UserViewSet


User = get_user_model()


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
