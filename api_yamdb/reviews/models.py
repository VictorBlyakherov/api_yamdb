from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class User(AbstractUser):
    UserRole = (
        ('admin', 'Administrator'),
        ('moderator', 'Moderator'),
        ('user', 'User')
    )
    username = models.CharField(unique=True, max_length=150)
    email = models.EmailField(max_length=254,)
    role = models.CharField(choices=UserRole, max_length=30, default='user')
    bio = models.TextField(null=True, blank=True)
    first_name = models.TextField(null=True, blank=True, max_length=150)
    last_name = models.TextField(null=True, blank=True, max_length=150)

    @property
    def is_moderator(self):
        return self.role == 'moderator'

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_user(self):
        return self.role == 'user'


class Category(models.Model):
    name = models.TextField()
    slug = models.SlugField()

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.TextField()
    slug = models.SlugField()


class Title(models.Model):
    name = models.TextField()
    year = models.IntegerField()
    description = models.TextField(blank=True, null=True)
    genre = models.ManyToManyField(
        Genre,
        through='GenreTitle'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        related_name='titles',
        null=True
    )


class Review(models.Model):
    text = models.TextField()
    author = models.ForeignKey(
        User, on_delete=models.CASCADE
    )
    score = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1, 'Рейтинг должен быть от 1 до 10'),
            MaxValueValidator(10, 'Рейтинг должен быть от 1 до 10'),
        ]
    )
    pub_date = models.DateTimeField(auto_now_add=True)
    title = models.ForeignKey(
        Title, on_delete=models.CASCADE, related_name='reviews'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'author'],
                name='review_constraint'
            ),
        ]


class Comment(models.Model):
    review = models.ForeignKey(
        Review, on_delete=models.CASCADE, related_name='comments'
    )
    text = models.TextField()
    pub_date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )


class GenreTitle(models.Model):
    genre = models.ForeignKey(
        Genre, on_delete=models.CASCADE
    )
    title = models.ForeignKey(
        Title, on_delete=models.CASCADE
    )
