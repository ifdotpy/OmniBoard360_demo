from rest_framework import serializers

from hr.model.response import Response


class ResponseSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()

    class Meta:
        model = Response
        fields = '__all__'
