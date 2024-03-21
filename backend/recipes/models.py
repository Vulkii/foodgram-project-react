from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models import UniqueConstraint

from constraints.constraints import (
    max_tag_length, max_color_length, max_tag_slug_length,
    max_ingridient_name, max_measurement_unit_length, max_recipe_length)

User = get_user_model()


class Tag(models.Model):
    """Tag model."""

    name = models.CharField(
        verbose_name='Название',
        unique=True,
        max_length=max_tag_length
    )

    color = models.CharField(
        verbose_name='Цвет в HEX',
        unique=True,
        max_length=max_color_length,
        validators=[
            RegexValidator(
                regex='^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$',
                message='Введенное значение не является цветом в формате HEX!'
            )
        ]
    )

    slug = models.SlugField(
        verbose_name='Уникальный слаг',
        unique=True,
        max_length=max_tag_slug_length,
        validators=[
            RegexValidator(
                regex=r'^[-a-zA-Z0-9_]{0,200}$',
                message='В введенном тексте есть запрещенные символы!'
            )
        ]
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Ingridient Model."""

    name = models.CharField(
        verbose_name='Название',
        max_length=max_ingridient_name,
    )

    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=max_measurement_unit_length,
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']
        unique_together = (('name', 'measurement_unit'),)

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    """Recipe model."""

    name = models.TextField(
        verbose_name="Название",
        max_length=max_recipe_length,
    )

    author = models.ForeignKey(
        User,
        related_name='recipes',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Автор',
    )

    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Ссылка на картинку на сайте',
    )

    text = models.TextField(
        verbose_name='Описание',
    )

    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги'
    )

    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe',
        related_name='recipes',
        verbose_name='Ингредиенты'
    )

    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        validators=[
            MinValueValidator(
                1, message='Минимальное значение времени приготовления - 1'
            )
        ],
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class IngredientInRecipe(models.Model):
    """Model to connect Ingredient and Recipe."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient_list',
        verbose_name='Рецепт',
    )

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
    )

    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(1, message='Минимальное количество 1!')]
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        return (
            f'{self.ingredient.name} - '
            f'{self.amount} '
            f'({self.ingredient.measurement_unit})'
        )


class UserRecipeRelation(models.Model):
    """Abstract base class for user and recipe relationship models."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='%(class)s_related',
        verbose_name='Пользователь',
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='%(class)s_related',
        verbose_name='Рецепт',
    )

    class Meta:
        abstract = True
        constraints = [
            UniqueConstraint(fields=['user', 'recipe'],
                             name='%(class)s_unique_together')
        ]

    def __str__(self):
        return f'{self.user} - {self.recipe}'


class Favourite(UserRecipeRelation):
    """Favourite model."""

    class Meta(UserRecipeRelation.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

    def __str__(self):
        return f'{self.user} добавил "{self.recipe}" в избранное.'


class ShoppingCart(UserRecipeRelation):
    """Shopping cart model."""

    class Meta(UserRecipeRelation.Meta):
        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'Корзина покупок'

    def __str__(self):
        return f'{self.user} добавил "{self.recipe}" в корзину.'
