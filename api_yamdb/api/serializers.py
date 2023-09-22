import re

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.validators import UniqueValidator
from reviews.models import Category, Comment, Genre, Review, Title, User


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
        pattern = re.compile(r'^[\w.@+-]+\Z')
        if value.lower() == "me":
            raise serializers.ValidationError('Некорректное имя пользователя')
        if not pattern.match(value):
            raise serializers.ValidationError(
                'Username не соответствует шаблону'
            )
        if len(value) > 150:
            raise serializers.ValidationError('Email не соответствует шаблону')
        return value

    def validate_email(self, value):
        if len(value) > 254:
            raise serializers.ValidationError('Email не соответствует шаблону')
        return value

    class Meta:
        model = User
        fields = ("username", "email")


class CategorySerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(
        validators=[
            UniqueValidator(queryset=Category.objects.all())
        ]
    )

    def validate(self, data):
        pattern = re.compile(r'^[-a-zA-Z0-9_]+$')
        if len(data['name']) > 256:
            raise serializers.ValidationError(
                'Имя категории должен быть короче 256 символов'
            )
        if len(data['slug']) > 50:
            raise serializers.ValidationError(
                'Slug должен быть короче 50 символов'
            )
        if not pattern.match(data['slug']):
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
        pattern = re.compile(r'^[-a-zA-Z0-9_]+$')
        if len(data['name']) > 256:
            raise serializers.ValidationError(
                'Имя жанра должен быть короче 256 символов'
            )
        if len(data['slug']) > 50:
            raise serializers.ValidationError(
                'Slug должен быть короче 50 символов'
            )
        if not pattern.match(data['slug']):
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
        if len(data['name']) > 256:
            raise serializers.ValidationError(
                'Имя произведения должен быть короче 256 символов'
            )
        return data

    class Meta:
        model = Title
        lookup_field = 'id'
        fields = '__all__'

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
        fields = '__all__'


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
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(validators=[
        UniqueValidator(queryset=User.objects.all()),
    ])
    email = serializers.EmailField(validators=[
        UniqueValidator(queryset=User.objects.all()),
    ])

    def validate_username(self, value):
        pattern = re.compile(r'^[\w.@+-]+\Z')
        if not pattern.match(value):
            raise serializers.ValidationError(
                'Username не соответствует шаблону'
            )
        if len(value) > 150:
            raise serializers.ValidationError(
                'Email не соответствует шаблону'
            )
        return value

    def validate_email(self, value):
        if len(value) > 254:
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
