from recipes.models import Ingredient, Tag
from users.models import Subscription
from rest_framework.serializers import ModelSerializer
from djoser.serializers import UserCreateSerializer, UserSerializer
from django.contrib.auth import get_user_model
from rest_framework.fields import SerializerMethodField

User = get_user_model()


class IngredientSerializer(ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class CustomUserSerializer(UserSerializer):
    is_subscribed = SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )

    def get_subscription(self, obj):
        user = self.context.get('request').user
        if user.is_auntificated:
            return Subscription.objects.filter(user=user, author=obj).exists()
        else:
            return False


class CustomUserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password')
        extra_kwargs = {
            'password': {'write_only': True},
            'first_name': {'required': True},
            'last_name': {'required': True}
        }

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user
