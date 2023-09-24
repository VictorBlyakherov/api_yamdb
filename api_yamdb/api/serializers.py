import re

from django.core.validators import validate_email
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.validators import UniqueValidator

from reviews.models import Category, Comment, Genre, Review, Title, User
from api_yamdb.settings import (MAX_SLUG_LENGTH,
                                MAX_EMAIL_LENGTH, MAX_USERNAME_LENGTH,
                                MAX_NAME_LENGTH, USER_OWN_URL)


pattern_username = re.compile(r'^[\w.@+-]+\Z')
pattern_slug = re.compile(r'^[-a-zA-Z0-9_]+$')


class SignupUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        validators=[
            UniqueValidator(queryset=User.objects.all())
        ]
    )
    email = serializers.EmailField(
        validators=[
            UniqueValidator(queryset=User.objects.all())
        ]
    )

    def validate_username(self, value):
        if value.lower() == USER_OWN_URL:
            raise serializers.ValidationError('Некорректное имя пользователя')
        if not pattern_username.match(value):
            raise serializers.ValidationError(
                'Username не соответствует шаблону'
            )
        if len(value) > MAX_USERNAME_LENGTH:
            raise serializers.ValidationError(
                'Username не соответствует шаблону'
            )
        return value

    def validate_email(self, value):
        if len(value) > MAX_EMAIL_LENGTH:
            raise serializers.ValidationError(
                'Email не должен быть длинее 254 символов'
            )
        if validate_email(value):
            raise serializers.ValidationError('Email не соответствует шаблону')
        return value

    class Meta:
        model = User
        fields = ("username", "email", )


class CategorySerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(
        validators=[
            UniqueValidator(queryset=Category.objects.all())
        ]
    )

    def validate(self, data):
        if len(data['name']) > MAX_NAME_LENGTH:
            raise serializers.ValidationError(
                'Имя категории должен быть короче 256 символов'
            )
        if len(data['slug']) > MAX_SLUG_LENGTH:
            raise serializers.ValidationError(
                'Slug должен быть короче 50 символов'
            )
        if not pattern_slug.match(data['slug']):
            raise serializers.ValidationError('Slug не соответствует шаблону')
        return data

    class Meta:
        model = Category
        fields = ('name', 'slug',)
        lookup_field = 'slug'
        extra_kwargs = {
            'url': {'lookup_field': 'slug'}
        }


class GenreSerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(
        validators=[
            UniqueValidator(queryset=Genre.objects.all())
        ]
    )

    def validate(self, data):
        if len(data['name']) > MAX_NAME_LENGTH:
            raise serializers.ValidationError(
                'Имя жанра должен быть короче 256 символов'
            )
        if len(data['slug']) > MAX_SLUG_LENGTH:
            raise serializers.ValidationError(
                'Slug должен быть короче 50 символов'
            )
        if not pattern_slug.match(data['slug']):
            raise serializers.ValidationError('Slug не соответствует шаблону')
        return data

    class Meta:
        model = Genre
        fields = ('name', 'slug',)
        lookup_field = 'slug'
        extra_kwargs = {
            'url': {'lookup_field': 'slug'}
        }


class TitleSerializer(serializers.ModelSerializer):
    genre = serializers.SlugRelatedField(
        slug_field='slug', many=True, queryset=Genre.objects.all()
    )
    category = serializers.SlugRelatedField(
        slug_field='slug', queryset=Category.objects.all()
    )

    def validate(self, data):
        if len(data['name']) > MAX_NAME_LENGTH:
            raise serializers.ValidationError(
                'Имя произведения должен быть короче 256 символов'
            )
        return data

    class Meta:
        model = Title
        lookup_field = 'id'
        fields = ('id', 'name', 'year', 'description', 'genre', 'category', )

        extra_kwargs = {
            'url': {'lookup_field': 'id'}
        }


class ReadOnlyTitleSerializer(serializers.ModelSerializer):
    genre = GenreSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    rating = serializers.IntegerField(read_only=True)

    class Meta:
        model = Title
        fields = (
            'id', 'name', 'year', 'description', 'genre', 'category', 'rating',
        )


class ReviewSerializer(serializers.ModelSerializer):
    title = serializers.SlugRelatedField(
        slug_field='name',
        read_only=True,
    )
    author = serializers.SlugRelatedField(
        default=serializers.CurrentUserDefault(),
        slug_field='username',
        read_only=True,
    )

    def validate(self, data):
        author = self.context['request'].user
        title_id = self.context['view'].kwargs.get('title_id')
        title = get_object_or_404(Title, pk=title_id)
        if self.context['request'].method == 'POST':
            if Review.objects.filter(title=title, author=author).exists():
                raise ValidationError(
                    'Нельзя добавить больше одного отзыва на произведение'
                )
        return data

    class Meta:
        model = Review
        fields = ('id', 'text', 'author', 'score', 'pub_date', 'title', )


class CommentSerializer(serializers.ModelSerializer):
    title = serializers.SlugRelatedField(slug_field='name', read_only=True,)
    review = serializers.SlugRelatedField(slug_field='id', read_only=True,)
    author = serializers.SlugRelatedField(
        default=serializers.CurrentUserDefault(),
        slug_field='username',
        read_only=True,
    )

    class Meta:
        model = Comment
        fields = ('id', 'review', 'text', 'pub_date', 'author', 'title', )


class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(validators=[
        UniqueValidator(queryset=User.objects.all()),
    ])
    email = serializers.EmailField(validators=[
        UniqueValidator(queryset=User.objects.all()),
    ])

    def validate_username(self, value):
        if not pattern_username.match(value):
            raise serializers.ValidationError(
                'Username не соответствует шаблону'
            )
        if len(value) > MAX_USERNAME_LENGTH:
            raise serializers.ValidationError(
                'Email не соответствует шаблону'
            )
        return value

    def validate_email(self, value):
        if len(value) > MAX_EMAIL_LENGTH:
            raise serializers.ValidationError(
                'Email не может быть длинее 254 символов'
            )
        if validate_email(value):
            raise serializers.ValidationError('Email не соответствует шаблону')
        return value

    class Meta:
        model = User
        fields = (
            "username", "email", "first_name", "last_name", "bio", "role"
        )


class UserTokenSerializer(serializers.Serializer):
    username = serializers.CharField()
    confirmation_code = serializers.CharField()
