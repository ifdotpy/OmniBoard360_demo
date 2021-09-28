from django.urls import path

from cra import views

urlpatterns = [
    path('challenge', views.get_challenge, name='get_challenge_view'),
    path('auth', views.verify_auth, name='verify_auth_view'),
    path('action', views.authenticated_action, name='authenticated_action_view')
]
