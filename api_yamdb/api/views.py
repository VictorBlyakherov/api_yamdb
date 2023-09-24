from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db.models import Avg
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken

from reviews.models import Category, Comment, Genre, Review, Title, User
from api_yamdb.settings import FROM_EMAIL

from api.filters import TitleFilter
from api.mixins import ListCreateDeleteViewSet
from api.permissions import (
    IsAdminOrAuthorOrModeratorPermissions,
    IsAdminPermissions,
    IsOnlyAdminPermissions
)
from api.serializers import (
    CategorySerializer,
    CommentSerializer,
    GenreSerializer,
    ReadOnlyTitleSerializer,
    ReviewSerializer,
    SignupUserSerializer,
    TitleSerializer,
    UserSerializer,
    UserTokenSerializer
)


class SignUpView(APIView):
    permission_classes = (permissions.AllowAny, )
    http_method_names = ('post', )

    def post(self, request):
        return_data = ''
        return_status = ''
        try:
            if User.objects.filter(
                    username=request.data['username'],
                    email=request.data['email']).exists():
                return_status = status.HTTP_200_OK
            if return_status == '' and User.objects.filter(
                    username=request.data['username']
            ).exists():
                return_status = status.HTTP_400_BAD_REQUEST
            if return_status == '' and User.objects.filter(
                    email=request.data['email']
            ).exists():
                return_status = status.HTTP_400_BAD_REQUEST
        except KeyError:
            pass
        print(return_status)

        if return_status == '':
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
                from_email=FROM_EMAIL,
                recipient_list=[user.email, ],
            )
            return_data = {'email': user.email, 'username': user.username}
            return_status = status.HTTP_200_OK

        return Response(return_data, return_status)


class SendTokenView(APIView):
    permission_classes = (permissions.AllowAny, )
    http_method_names = ('post', )

    def post(self, request):
        serializer = UserTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(
            User,
            username=request.data['username']
        )

        code = default_token_generator.make_token(user)
        if code == request.data['confirmation_code']:
            token = AccessToken.for_user(user)
            return_data = {'token': str(token)}
            return_status = status.HTTP_200_OK
        else:
            return_data = ''
            return_status = status.HTTP_400_BAD_REQUEST

        return Response(return_data, return_status)


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
    http_method_names = ('get', 'post', 'head', 'patch', 'delete', )
    permission_classes = (IsAdminPermissions, )

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve',):
            return ReadOnlyTitleSerializer
        return self.serializer_class


class ReviewsViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = (IsAdminOrAuthorOrModeratorPermissions,)
    http_method_names = ('get', 'post', 'head', 'patch', 'delete', )

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
    http_method_names = ('get', 'post', 'head', 'patch', 'delete', )

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
    http_method_names = ('get', 'post', 'patch', 'delete', )

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,),
        methods=('get', 'patch', ),
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
