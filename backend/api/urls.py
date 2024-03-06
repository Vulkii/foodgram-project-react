from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import TagViewSet, IngredientViewSet, RecipeViewSet, DownloadShoppingCartAPIView

router = DefaultRouter()
router.register('tags', TagViewSet)
router.register('ingredients', IngredientViewSet)
router.register('recipes', RecipeViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('api/recipes/download_shopping_cart/',
         DownloadShoppingCartAPIView.as_view(), name='download_shopping_cart'),
]
