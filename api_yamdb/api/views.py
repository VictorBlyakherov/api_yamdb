from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db.models import Avg
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from reviews.models import Category, Comment, Genre, Review, Title, User

from .filters import TitleFilter
from .mixins import ListCreateDeleteViewSet
from .permissions import (IsAdminOrAuthorOrModeratorPermissions,
                          IsAdminPermissions, IsOnlyAdminPermissions)
from .serializers import (CategorySerializer, CommentSerializer,
                          GenreSerializer, ReadOnlyTitleSerializer,
                          ReviewSerializer, SignupUserSerializer,
                          TitleSerializer, UserSerializer, UserTokenSerializer)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def signup_user(request):
    try:
        if User.objects.filter(
                username=request.data['username'],
                email=request.data['email']).exists():
            return Response('', status=status.HTTP_200_OK)
        if User.objects.filter(username=request.data['username']).exists():
            return Response('', status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(email=request.data['email']).exists():
            return Response('', status=status.HTTP_400_BAD_REQUEST)
    except KeyError:
        pass

    serializer = SignupUserSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    user = get_object_or_404(
        User,
        username=serializer.validated_data['username']
    )
    code = default_token_generator.make_token(user)
    send_mail(
        subject='Код регистрации',
        message=f'Код подтверждения: {code}',
        from_email='xxxxxvic@yandex.ru',
        recipient_list=[user.email, ],
    )

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def send_token(request):
    serializer = UserTokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = get_object_or_404(
        User,
        username=request.data['username']
    )

    code = default_token_generator.make_token(user)
    if code == request.data['confirmation_code']:
        token = AccessToken.for_user(user)
        return Response({'token': str(token)}, status=status.HTTP_200_OK)

    return Response('', status=status.HTTP_400_BAD_REQUEST)


class CategoriesViewSet(ListCreateDeleteViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    permission_classes = (IsAdminPermissions, )
    lookup_field = "slug"


class GenresViewSet(ListCreateDeleteViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    permission_classes = (IsAdminPermissions, )
    lookup_field = "slug"


class TitlesViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.all().annotate(rating=Avg("reviews__score"))
    serializer_class = TitleSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = TitleFilter
    http_method_names = ['get', 'post', 'head', 'patch', 'delete', ]
    permission_classes = (IsAdminPermissions, )

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve',):
            return ReadOnlyTitleSerializer
        return self.serializer_class


class ReviewsViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = (IsAdminOrAuthorOrModeratorPermissions,)
    http_method_names = ['get', 'post', 'head', 'patch', 'delete', ]

    def get_queryset(self):
        title = get_object_or_404(Title, id=self.kwargs.get('title_id'))
        return title.reviews.all()

    def perform_create(self, serializer):
        title_id = self.kwargs.get('title_id')
        title = get_object_or_404(Title, id=title_id)
        serializer.save(author=self.request.user, title=title)


class CommentsViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = (IsAdminOrAuthorOrModeratorPermissions,)
    http_method_names = ['get', 'post', 'head', 'patch', 'delete', ]

    def get_queryset(self):
        review = get_object_or_404(Review, id=self.kwargs.get('review_id'))
        return review.comments.all()

    def perform_create(self, serializer):
        review_id = self.kwargs.get('review_id')
        review = get_object_or_404(Review, id=review_id)

        serializer.save(author=self.request.user, review=review, )


class UsersViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter]
    permission_classes = (IsAuthenticated, IsOnlyAdminPermissions,)
    lookup_field = "username"
    search_fields = ('username',)
    http_method_names = ['get', 'post', 'patch', 'delete']

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,),
        methods=['get', 'patch'],
        url_path='me',
    )
    def get_or_update_me(self, request: Request) -> Response:
        serializer = self.get_serializer(
            instance=request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data.get('role'):
            serializer.validated_data['role'] = request.user.role
        if request.method == 'PATCH':
            serializer.save()
            return Response(serializer.data)
        serializer = self.get_serializer(request.user, many=False)
        return Response(serializer.data)
