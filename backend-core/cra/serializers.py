from abc import ABC, ABCMeta

from rest_framework import serializers

from cra.models import Challenge
from siebox.model.hardware import HardwareTypeChoice, HardwareModelChoice


class ChallengeSerializer(serializers.ModelSerializer):
    sid = serializers.CharField(source='id')

    class Meta:
        model = Challenge
        fields = ['sid', 'challenge']


HARDWARE_AUTH_TYPE = 'hardware'
AUTH_TYPES = [(HARDWARE_AUTH_TYPE, HARDWARE_AUTH_TYPE)]


class AuthVerifySerializer(serializers.Serializer):
    sid = serializers.UUIDField()
    uname = serializers.CharField()
    type = serializers.ChoiceField(choices=AUTH_TYPES)
    challenge_response = serializers.CharField()


INITIALIZE_ACTION_TYPE = 'initialize-hardware'
ACTION_TYPES = [(INITIALIZE_ACTION_TYPE, INITIALIZE_ACTION_TYPE)]


class AuthenticatedActionSerializer(serializers.Serializer):
    sid = serializers.UUIDField()
    uname = serializers.CharField(required=False)
    action = serializers.ChoiceField(choices=ACTION_TYPES)
    challenge_response = serializers.CharField()
    payload = serializers.JSONField(required=False)


class AuthenticatedActionInitializePayloadSerializer(serializers.Serializer):
    public_key = serializers.CharField()
    type = serializers.ChoiceField(choices=HardwareTypeChoice.CHOICES)
    model = serializers.ChoiceField(choices=HardwareModelChoice.CHOICES)
    cpuid = serializers.CharField(max_length=16)
