from django.shortcuts import render
from recipes.models import Tag, Ingredient, Recipe, ShoppingCart
from .permissions import IsAdminOrReadOnly, AllowAnyOrIsAdminOrReadOnly, IsAuthorOrReadOnly
from .serializers import TagSerializer, IngredientSerializer, RecipeSerializer, RecipeForSubSerializer
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from .pagination import CustomPagination
from django_filters.rest_framework import DjangoFilterBackend
from .filters import TagsInRecipeFilter
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse


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
        return Response({"detail": "Method Not Allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, *args, **kwargs):
        return Response({"detail": "Method Not Allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, *args, **kwargs):
        return Response({"detail": "Method Not Allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAnyOrIsAdminOrReadOnly,)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        return Response({"detail": "Method Not Allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, *args, **kwargs):
        return Response({"detail": "Method Not Allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, *args, **kwargs):
        return Response({"detail": "Method Not Allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


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
        if author_id is not None:
            get_object_or_404(User, pk=author_id)
            queryset = queryset.filter(author_id=author_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        try:
            recipe = Recipe.objects.get(id=pk)
        except Recipe.DoesNotExist:
            return Response({'error': 'Recipe does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        shopping_cart, created = ShoppingCart.objects.get_or_create(user=request.user, recipe=recipe)
        if created:
            serializer = RecipeForSubSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response({'status': 'The recipe already in shopping cart'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated])
    def remove_from_shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        try:
            shopping_cart_item = ShoppingCart.objects.get(user=request.user, recipe=recipe)
            shopping_cart_item.delete()
            return Response({'status': 'The recipe removed from shopping cart'}, status=status.HTTP_204_NO_CONTENT)
        except ShoppingCart.DoesNotExist:
            return Response({'error': 'The recipe not in shopping cart'}, status=status.HTTP_400_BAD_REQUEST)


class DownloadShoppingCartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        shopping_cart_items = ShoppingCart.objects.filter(user=request.user).prefetch_related('recipe', 'recipe__ingredient_list', 'recipe__ingredient_list__ingredient')
        shopping_cart_content = "Список покупок:\n\n"

        ingredients = {}

        for item in shopping_cart_items:
            for ingredient in item.recipe.ingredient_list.all():
                key = (ingredient.ingredient.name, ingredient.ingredient.measurement_unit)
                if key in ingredients:
                    ingredients[key] += ingredient.amount
                else:
                    ingredients[key] = ingredient.amount

        for (name, unit), amount in ingredients.items():
            shopping_cart_content += f"{name} - {amount} {unit}\n"

        response = HttpResponse(shopping_cart_content, content_type="text/plain; charset=utf-8")
        response['Content-Disposition'] = 'attachment; filename="shopping_cart.txt"'
        return response
