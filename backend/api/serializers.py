import base64

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile
from djoser.serializers import UserSerializer
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ImageField, ModelSerializer

from users.models import Subscription
from recipes.models import Ingredient, Recipe, Tag, IngredientInRecipe

User = get_user_model()


class IngredientSerializer(ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class UserSerializer(UserSerializer):
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

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            if user.id == obj.id:
                return False
            return Subscription.objects.filter(user=user, author=obj).exists()
        else:
            return False


class UserCreateSerializer(ModelSerializer):
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


class Base64ImageField(ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class RecipeSerializer(ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = SerializerMethodField()
    image = Base64ImageField()
    is_favorited = SerializerMethodField(read_only=True)
    is_in_shopping_cart = SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def validate(self, data):
        tags_data = self.initial_data.get('tags')
        ingredients_data = self.initial_data.get('ingredients')

        if not tags_data:
            raise ValidationError({'tags':
                                   'At least one tag must be provided.'})

        if len(tags_data) != len(set(tags_data)):
            raise ValidationError({'tags': 'Tags must be unique.'})

        if not all(Tag.objects.filter(id=tag_id).exists()
                   for tag_id in tags_data):
            raise ValidationError({'tags': 'One or more tags do not exist.'})

        if not ingredients_data:
            raise ValidationError({'ingredients':
                                   'At least one ingredient must be provided.'})

        ingredient_ids = [ingredient.get('id')
                          for ingredient in ingredients_data if 'id'
                          in ingredient and 'amount' in ingredient]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise ValidationError({'ingredients': 'Ingredients must be unique.'})

        for ingredient in ingredients_data:
            if 'id' not in ingredient or 'amount' not in ingredient:
                raise ValidationError({
                    'ingredients':
                    'Each ingredient must have an id and an amount.'})
            if int(ingredient['amount']) <= 0:
                raise ValidationError({
                    'ingredients':
                    'The amount for each ingredient must be greater than zero.'})

        if (Ingredient.objects.filter(id__in=ingredient_ids).count()
           != len(ingredient_ids)):
            raise ValidationError({'ingredients':
                                   'One or more ingredients do not exist.'})

        return data

    def get_ingredients(self, obj):
        ingredients_data = []
        for ingredient_relation in obj.ingredient_list.all():
            ingredient = ingredient_relation.ingredient
            ingredients_data.append({
                'id': ingredient.id,
                'name': ingredient.name,
                'measurement_unit': ingredient.measurement_unit,
                'amount': ingredient_relation.amount
            })
        return ingredients_data

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.favourite_related.filter(recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.shoppingcart_related.filter(recipe=obj).exists()

    def create(self, validated_data):
        tags_data = self.context['request'].data.get('tags')
        ingredients_data = self.context['request'].data.get('ingredients', [])

        recipe = Recipe.objects.create(**validated_data)

        if tags_data:
            tags = Tag.objects.filter(id__in=tags_data)
            recipe.tags.set(tags)

        if ingredients_data:
            for ingredient_data in ingredients_data:
                ingredient_id = ingredient_data.get('id')
                amount = ingredient_data.get('amount')
                ingredient = get_object_or_404(Ingredient, id=ingredient_id)
                IngredientInRecipe.objects.create(
                    recipe=recipe,
                    ingredient=ingredient,
                    amount=amount
                )

        recipe.save()
        return recipe


class SubscriptionSerializer(UserSerializer):
    recipes_count = SerializerMethodField()
    recipes = SerializerMethodField()

    class Meta(UserSerializer.Meta):
        model = User
        fields = UserSerializer.Meta.fields + ('recipes_count',
                                               'recipes',)
        read_only_fields = ('email', 'username')

    def validate(self, data):
        author = self.instance
        user = self.context.get('request').user
        if Subscription.objects.filter(author=author, user=user).exists():
            raise ValidationError(
                detail='Вы уже подписаны на этого пользователя.',
                code=status.HTTP_400_BAD_REQUEST
            )
        if user == author:
            raise ValidationError(
                detail='Вы не можете подписаться на самого себя.',
                code=status.HTTP_400_BAD_REQUEST
            )
        return data

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipe_limit = request.GET.get('recipes_limit')

        if recipe_limit and recipe_limit.isdigit():
            recipe_limit = int(recipe_limit)
            recipes = obj.recipes.all()[:recipe_limit]
        else:
            recipes = obj.recipes.all()

        serializer = RecipeForSubSerializer(recipes, many=True, read_only=True)
        return serializer.data


class RecipeForSubSerializer(ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )
