from rest_framework.generics import ListAPIView, RetrieveAPIView

from hr.model.position import Position
from hr.serializers.position import PositionSerializer


class PositionsListView(ListAPIView):
    versioning_class = None
    model = Position
    serializer_class = PositionSerializer
    queryset = Position.objects.filter(archived=False).all()


class PositionView(RetrieveAPIView):
    versioning_class = None
    model = Position
    serializer_class = PositionSerializer
    queryset = Position.objects.filter(archived=False).all()
