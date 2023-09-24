from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (CategoriesViewSet, CommentsViewSet, GenresViewSet,
                    ReviewsViewSet, TitlesViewSet, UsersViewSet,
                    SignUpView, SendTokenView)

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
    path('api/v1/auth/signup/', SignUpView.as_view(), name='signup'),
    path('api/v1/auth/token/', SendTokenView.as_view(), name='send_token'),
    path('api/v1/', include(router.urls)),
]
