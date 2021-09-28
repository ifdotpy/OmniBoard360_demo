from rest_framework import serializers

from sales.model.request import Request


class RequestSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()

    class Meta:
        model = Request
        fields = '__all__'
