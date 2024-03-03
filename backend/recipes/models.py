from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, RegexValidator
from django.db.models import UniqueConstraint

User = get_user_model()


class Tag(models.Model):
    """Tag model."""

    name = models.CharField(
        verbose_name='Название',
        unique=True,
        max_length=200
    )

    color = models.CharField(
        verbose_name='Цвет в HEX',
        unique=True,
        max_length=7,
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
        max_length=200,
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
        max_length=200,
    )

    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=200,
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    """Recipe model."""

    name = models.TextField(
        verbose_name="Название",
        max_length=200,
    )

    image = models.ImageField(
        upload_to='reviews/images/',
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

    cooking_time = models.IntegerField(
        verbose_name='Время приготовления',
        validators=[
            MinValueValidator(
                1, message='Минимальное значение времени приготовления - 1'
            )
        ],
    )

    class Meta:
        ordering = ['-id']
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
        'Количество',
        validators=[MinValueValidator(1, message='Минимальное количество 1!')]
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'

    def __str__(self):
        return (
            f'{self.ingredient.name} - '
            f'{self.amount} '
            f'({self.ingredient.measurement_unit})'
        )


class Favourite(models.Model):
    """Favourite model."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь',
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            UniqueConstraint(fields=['user', 'recipe'],
                             name='unique_favourite')
        ]

    def __str__(self):
        return f'{self.user} добавил "{self.recipe}" в избранное.'


class ShoppingCart(models.Model):
    """Shopping cart model."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь',
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'Корзина покупок'
        constraints = [
            UniqueConstraint(fields=['user', 'recipe'],
                             name='unique_shopping_cart')
        ]

    def __str__(self):
        return f'{self.user} добавил "{self.recipe}" в корзину.'
