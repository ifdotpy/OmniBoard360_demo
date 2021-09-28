from rest_framework.serializers import ModelSerializer

from hr.model.position import Position


class PositionSerializer(ModelSerializer):
    class Meta:
        model = Position
        fields = '__all__'
