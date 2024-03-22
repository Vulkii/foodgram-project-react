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

from .filters import TagsInRecipeFilter, IngredientFilter
from .pagination import Pagination
from .permissions import (AllowAnyOrIsAdminOrReadOnly,
                          IsAuthorOrAdminOrReadOnly)
from .serializers import (IngredientSerializer, RecipeForSubSerializer,
                          RecipeSerializer, TagSerializer)
from recipes.models import Favourite, Ingredient, Recipe, ShoppingCart, Tag

User = get_user_model()


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAnyOrIsAdminOrReadOnly,)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAnyOrIsAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrAdminOrReadOnly)
    serializer_class = RecipeSerializer
    pagination_class = Pagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TagsInRecipeFilter

    def get_queryset(self):
        return super().get_queryset()

    def destroy(self, request, *args, **kwargs):
        recipe = get_object_or_404(Recipe, pk=kwargs.get('pk'))

        return super().destroy(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def update(self, request, *args, **kwargs):
        recipe = self.get_object()

        return super().update(request, *args, **kwargs)

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

    @shopping_cart.mapping.delete
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

    @favorite.mapping.delete
    def unfavorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user
        favorite = Favourite.objects.filter(user=user, recipe=recipe).first()
        if favorite:
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({'detail': 'The recipe is not in favorites'},
                            status=status.HTTP_400_BAD_REQUEST)
