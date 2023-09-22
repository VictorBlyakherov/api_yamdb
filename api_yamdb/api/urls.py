from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (CategoriesViewSet, CommentsViewSet, GenresViewSet,
                    ReviewsViewSet, TitlesViewSet, UsersViewSet, send_token,
                    signup_user)

router = DefaultRouter()

router.register(r'categories', CategoriesViewSet)
router.register(r'genres', GenresViewSet)
router.register(r'titles', TitlesViewSet)
router.register(r'titles/(?P<title_id>\d+)/reviews', ReviewsViewSet)
router.register(
    r'titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments',
    CommentsViewSet
)
router.register(r'users', UsersViewSet)


urlpatterns = [
    path('api/v1/auth/signup/', signup_user, name='signup'),
    path('api/v1/auth/token/', send_token, name='send_token'),
    path('api/v1/', include(router.urls)),
]
