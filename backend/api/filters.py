import django_filters
from django.contrib.auth import get_user_model

from recipes.models import Recipe, Ingredient

User = get_user_model()


class TagsInRecipeFilter(django_filters.FilterSet):
    tags = django_filters.AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = django_filters.NumberFilter(method='filter_is_favorited')
    author = django_filters.NumberFilter(method='filter_author')
    is_in_shopping_cart = django_filters.NumberFilter(
        method='filter_is_in_shopping_cart')

    def filter_author(self, queryset, name, value):
        return queryset.filter(author_id=value)

    def filter_is_favorited(self, queryset, name, value):
        if not self.request or not self.request.user.is_authenticated:
            return queryset

        value = value in [True, '1', 1]
        if value:
            return queryset.filter(favourite_related__user=self.request.user)
        return queryset.exclude(favourite_related__user=self.request.user)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if not self.request or not self.request.user.is_authenticated:
            return queryset

        value = value in [True, '1', 1]
        if value:
            return queryset.filter(
                shoppingcart_related__user=self.request.user)
        return queryset.exclude(shoppingcart_related__user=self.request.user)

    class Meta:
        model = Recipe
        fields = ['tags', 'author']


class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name',
                                     lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']
