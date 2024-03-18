from recipes.models import Favourite, Ingredient, Recipe, ShoppingCart, Tag
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from .filters import TagsInRecipeFilter
from .pagination import CustomPagination
from .permissions import (AllowAnyOrIsAdminOrReadOnly, IsAdminOrReadOnly,
                          IsAuthorOrReadOnly)
from .serializers import (IngredientSerializer, RecipeForSubSerializer,
                          RecipeSerializer, TagSerializer)

User = get_user_model()


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAnyOrIsAdminOrReadOnly,)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        return Response({"detail": "Method Not Allowed"},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, *args, **kwargs):
        return Response({"detail": "Method Not Allowed"},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, *args, **kwargs):
        return Response({"detail": "Method Not Allowed"},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAnyOrIsAdminOrReadOnly,)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        return Response({"detail": "Method Not Allowed"},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, *args, **kwargs):
        return Response({"detail": "Method Not Allowed"},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, *args, **kwargs):
        return Response({"detail": "Method Not Allowed"},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly | IsAdminOrReadOnly,)
    serializer_class = RecipeSerializer
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TagsInRecipeFilter

    def get_queryset(self):
        queryset = super().get_queryset()
        author_id = self.request.query_params.get('author')
        is_in_shopping_cart = self.request.query_params.get
        ('is_in_shopping_cart', None)
        is_favorited = self.request.query_params.get('is_favorited', None)

        if author_id is not None:
            get_object_or_404(User, pk=author_id)
            queryset = queryset.filter(author_id=author_id)
        if self.request.user.is_authenticated:
            if is_in_shopping_cart is not None:
                if is_in_shopping_cart.lower() == '1':
                    queryset = queryset.filter(
                        shopping_cart__user=self.request.user)
                elif is_in_shopping_cart.lower() == '0':
                    queryset = queryset.exclude(
                        shopping_cart__user=self.request.user)

            if is_favorited is not None:
                if is_favorited.lower() == '1':
                    queryset = queryset.filter(
                        favorites__user=self.request.user)
                elif is_favorited.lower() == '0':
                    queryset = queryset.exclude(
                        favorites__user=self.request.user)
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        try:
            recipe = Recipe.objects.get(id=pk)
        except Recipe.DoesNotExist:
            return Response({'error': 'Recipe does not exist'},
                            status=status.HTTP_400_BAD_REQUEST)
        shopping_cart, created = ShoppingCart.objects.get_or_create(
            user=request.user, recipe=recipe)
        if created:
            serializer = RecipeForSubSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response({'status': 'The recipe already in shopping cart'},
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'],
            permission_classes=[IsAuthorOrReadOnly | IsAdminOrReadOnly,])
    def remove_from_shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        try:
            shopping_cart_item = ShoppingCart.objects.get(user=request.user,
                                                          recipe=recipe)
            shopping_cart_item.delete()
            return Response({'status': 'Recipe removed from shopping cart'},
                            status=status.HTTP_204_NO_CONTENT)
        except ShoppingCart.DoesNotExist:
            return Response({'error': 'The recipe not in shopping cart'},
                            status=status.HTTP_400_BAD_REQUEST)

    @action(methods=("get",), detail=False)
    def download_shopping_cart(self, request):
        shopping_cart_items = ShoppingCart.objects.filter(user=request.user
                                                          ).prefetch_related(
            'recipe',
            'recipe__ingredient_list',
            'recipe__ingredient_list__ingredient'
        )

        shopping_cart_content = "Shopping list:\n\n"

        ingredients = {}

        for item in shopping_cart_items:
            for ingredient in item.recipe.ingredient_list.all():
                key = (ingredient.ingredient.name,
                       ingredient.ingredient.measurement_unit)
                if key in ingredients:
                    ingredients[key] += ingredient.amount
                else:
                    ingredients[key] = ingredient.amount

        for (name, unit), amount in ingredients.items():
            shopping_cart_content += f"{name} - {amount} {unit}\n"

        response = HttpResponse(shopping_cart_content,
                                content_type="text/plain; charset=utf-8")
        response['Content-Disposition'] = 'attachment; filename="shg_cart.txt"'
        return response

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            raise ValidationError({'detail': 'There is no such recipe'},
                                  code=status.HTTP_400_BAD_REQUEST)

        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user
        favorite, created = Favourite.objects.get_or_create(user=user,
                                                            recipe=recipe)
        if created:
            serializer = RecipeForSubSerializer(recipe,
                                                context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response({'detail': 'Recipe is already in favorites'},
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'],
            permission_classes=[IsAuthenticated])
    def unfavorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user
        favorite = Favourite.objects.filter(user=user, recipe=recipe).first()
        if favorite:
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({'detail': 'The recipe is not in favorites'},
                            status=status.HTTP_404_NOT_FOUND)

    def create(self, request, *args, **kwargs):
        ingredients_data = request.data.get('ingredients', [])
        tags_data = request.data.get('tags', [])

        ingredients_ids = []
        for ingredient in ingredients_data:
            if ('id' in ingredient
                and 'amount' in ingredient
                    and ingredient['amount'] > 0):
                ingredients_ids.append(ingredient.get('id'))
            else:
                return Response({'error':
                                ('Each ingredient must have'
                                 'a valid id and amount must'
                                 'be greater than 0')},
                                status=status.HTTP_400_BAD_REQUEST)

        if not ingredients_data or not ingredients_ids:
            return Response({'error': ('At least two'
                                       'ingredients must be provided'
                                       'and must be valid')},
                            status=status.HTTP_400_BAD_REQUEST)

        if not tags_data:
            return Response({'error':
                            ('At least one tag must be provided'
                             'and must be valid.')},
                            status=status.HTTP_400_BAD_REQUEST)

        if len(ingredients_ids) != len(set(ingredients_ids)):
            return Response({'error': 'Ingredients must be unique'},
                            status=status.HTTP_400_BAD_REQUEST)

        if len(tags_data) != len(set(tags_data)):
            return Response({'error': 'Tags must be unique'},
                            status=status.HTTP_400_BAD_REQUEST)

        if (Ingredient.objects.filter(id__in=ingredients_ids).count()
           != len(set(ingredients_ids))):
            return Response({'error': 'One or more ingredients do not exist'},
                            status=status.HTTP_400_BAD_REQUEST)

        if not all(
                Tag.objects.filter(id=tag_id).exists() for tag_id
                in tags_data):
            return Response({'error': 'One or more tags do not exist'},
                            status=status.HTTP_400_BAD_REQUEST)

        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        recipe = self.get_object()

        if recipe.author != request.user:
            return Response({'detail':
                             ('You do not have permission'
                              'to perform this action')},
                            status=status.HTTP_403_FORBIDDEN)

        ingredients_data = request.data.get('ingredients', [])
        tags_data = request.data.get('tags', [])

        ingredients_ids = []
        for ingredient in ingredients_data:
            if ('id' in ingredient and 'amount' in ingredient
                    and ingredient['amount'] > 0):
                ingredients_ids.append(ingredient.get('id'))
            else:
                return Response({'error':
                                ('Each ingredient must have a valid'
                                 'id and amount must be greater than 0')},
                                status=status.HTTP_400_BAD_REQUEST)

        if ingredients_data is None or tags_data is None:
            return Response({'error':
                            'Fields ingredients and tags are required'},
                            status=status.HTTP_400_BAD_REQUEST)

        if not ingredients_data or not tags_data:
            return Response({'error':
                             'ingredients and tags fields cannot be empty'},
                            status=status.HTTP_400_BAD_REQUEST)

        if len(ingredients_ids) != len(set(ingredients_ids)):
            return Response({'error': 'Ingredients must be unique'},
                            status=status.HTTP_400_BAD_REQUEST)

        if len(tags_data) != len(set(tags_data)):
            return Response({'error': 'Tags must be unique'},
                            status=status.HTTP_400_BAD_REQUEST)

        if (Ingredient.objects.filter(id__in=ingredients_ids).count()
           != len(set(ingredients_ids))):
            return Response({'error': 'One or more ingredients do not exist'},
                            status=status.HTTP_400_BAD_REQUEST)

        if not all(
                Tag.objects.filter(id=tag_id).exists() for tag_id
                in tags_data):
            return Response({'error': 'One or more tags do not exist'},
                            status=status.HTTP_400_BAD_REQUEST)

        return super().update(request, *args, **kwargs)
