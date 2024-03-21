from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import UniqueConstraint

from constraints.constraints import max_email_length, max_name_length


class User(AbstractUser):
    """User model."""

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [
        'username',
        'first_name',
        'last_name',
    ]
    email = models.EmailField(
        verbose_name='Почта',
        max_length=max_email_length,
        unique=True,
    )
    username = models.CharField(
        max_length=max_name_length,
        unique=True,
        verbose_name='Имя пользователя'
    )

    class Meta:
        ordering = ['username']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Subscription model."""

    user = models.ForeignKey(
        User,
        related_name='subscriber',
        verbose_name="Подписчик",
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        User,
        related_name='subscribing',
        verbose_name="Автор",
        on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ['-id']
        constraints = [
            UniqueConstraint(fields=['user', 'author'],
                             name='unique_subscription')
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
