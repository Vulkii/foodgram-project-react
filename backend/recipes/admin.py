from django.contrib import admin
import json
from django import forms

from .models import (Favourite, Ingredient, IngredientInRecipe, Recipe,
                     ShoppingCart, Tag)

if admin.site.is_registered(Ingredient):
    admin.site.unregister(Ingredient)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'color', 'slug']
    search_fields = ['name', 'slug']


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'author', 'cooking_time']
    search_fields = ['name', 'author__username', 'ingredients__name']
    list_filter = ['tags']


@admin.register(IngredientInRecipe)
class IngredientInRecipeAdmin(admin.ModelAdmin):
    list_display = ['recipe', 'ingredient', 'amount']
    search_fields = ['recipe__name', 'ingredient__name']


@admin.register(Favourite)
class FavouriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'recipe']
    search_fields = ['user__username', 'recipe__name']


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ['user', 'recipe']
    search_fields = ['user__username', 'recipe__name']


class IngredientUploadForm(forms.ModelForm):
    ingredients_file = forms.FileField(
        required=False, label='Загрузить ингредиенты из JSON файла')

    class Meta:
        model = Ingredient
        fields = '__all__'

    def save(self, commit=True):
        ingredients_file = self.cleaned_data.get('ingredients_file', None)
        if ingredients_file:
            ingredients_data = json.load(ingredients_file)
            for item in ingredients_data:
                Ingredient.objects.get_or_create(
                    name=item['name'],
                    defaults={'measurement_unit': item['measurement_unit']}
                )
        return super().save(commit=commit)


class IngredientAdmin(admin.ModelAdmin):
    form = IngredientUploadForm
    list_display = ['name', 'measurement_unit']

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)


admin.site.register(Ingredient, IngredientAdmin)
