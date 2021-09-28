from django.urls import path
from .jwt import HPLCTokenObtainPairView, HPLCTokenRefreshView, CatalogTokenRefreshView, CatalogTokenObtainPairView
from .views import DockerTokenObtainView

urlpatterns = [
    path('token/docker/', DockerTokenObtainView.as_view(), name='token_obtain_docker'),
    path('token/', HPLCTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', HPLCTokenRefreshView.as_view(), name='token_refresh'),
    path('token/catalog/', CatalogTokenObtainPairView.as_view(), name='token_obtain_catalog'),
    path('token/catalog/refresh/', CatalogTokenRefreshView.as_view(), name='token_refresh_catalog'),
]
