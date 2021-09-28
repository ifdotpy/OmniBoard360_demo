from django.urls import path

from hr.view.views_position import PositionsListView, PositionView
from hr.view.views_response import ResponseView

urlpatterns = [
    path('positions/', PositionsListView.as_view(), name='positions-list'),
    path('positions/<int:pk>', PositionView.as_view(), name='position'),
    path('response/', ResponseView.as_view(), name='response'),
]
