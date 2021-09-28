from django.contrib.auth.models import User
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.utils import aware_utcnow

from authentication.jwt import get_tokens_for_hardware_by_user

from cra.models import Challenge
from cra.serializers import ChallengeSerializer, AuthVerifySerializer, AuthenticatedActionSerializer, \
    HARDWARE_AUTH_TYPE, INITIALIZE_ACTION_TYPE, AuthenticatedActionInitializePayloadSerializer
from cra.util.auth import is_challenge_not_expired, is_challenge_response_valid
from cra.util.public_key_getters import initialize_key_getter
from cra.actions import initialize_hardware

from django.conf import settings

CHALLENGE_LIFESPAN_SEC = 10

ACTIONS_MAP = {
    INITIALIZE_ACTION_TYPE: (initialize_hardware, initialize_key_getter, AuthenticatedActionInitializePayloadSerializer)
}


class GetChallengeThrottle(AnonRateThrottle):
    rate = '2000/day'


@api_view(['GET'])
@throttle_classes([GetChallengeThrottle])
def get_challenge(request):
    challenge = Challenge.objects.create()
    serializer = ChallengeSerializer(challenge)
    return Response(serializer.data)


@api_view(['POST'])
@throttle_classes([GetChallengeThrottle])
def verify_auth(request):
    request_received = aware_utcnow()

    serializer = AuthVerifySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    data = serializer.data

    try:
        challenge = Challenge.objects.get(pk=data['sid'])
    except Challenge.DoesNotExist:
        print('DoesNotExist Challenge')
        if settings.DEBUG:
            raise AuthenticationFailed(detail='DoesNotExist Challenge')
        else:
            raise AuthenticationFailed()

    try:
        is_challenge_not_expired(challenge, request_received, raise_exception=True)
    finally:
        challenge.delete()

    user = None
    if data['type'] == HARDWARE_AUTH_TYPE:
        try:
            user = User.objects.get(userforhardware__hardware__id=data['uname'])
        except User.DoesNotExist:
            print('DoesNotExist User')
            if settings.DEBUG:
                raise AuthenticationFailed(detail='DoesNotExist User')
            else:
                raise AuthenticationFailed()

    public_key = user.userforhardware.public_key
    is_challenge_response_valid(challenge, data, public_key, raise_exception=True)

    return Response(get_tokens_for_hardware_by_user(user))


@api_view(['POST'])
@throttle_classes([GetChallengeThrottle])
def authenticated_action(request):
    request_received = aware_utcnow()

    serializer = AuthenticatedActionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    data = serializer.data

    try:
        challenge = Challenge.objects.get(pk=data['sid'])
    except Challenge.DoesNotExist:
        if settings.DEBUG:
            raise AuthenticationFailed(detail='DoesNotExist Challenge')
        else:
            raise AuthenticationFailed()

    try:
        is_challenge_not_expired(challenge, request_received, raise_exception=True)
    finally:
        challenge.delete()

    action, get_public_key, PayloadSerializerClass = ACTIONS_MAP[data['action']]

    uname = data.get('uname', None)

    public_key = get_public_key(uname)

    is_challenge_response_valid(challenge, data, public_key, raise_exception=True)

    # serialize payload
    payload_serializer = PayloadSerializerClass(data=data.get('payload'))
    payload_serializer.is_valid(raise_exception=True)
    payload = payload_serializer.data

    # execute action
    result = action(uname, **payload)
    return Response(**result)
