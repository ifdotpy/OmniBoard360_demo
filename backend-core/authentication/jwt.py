from django.conf import settings
from rest_framework import exceptions
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenViewBase
from rest_framework_simplejwt.tokens import RefreshToken

ACCESS_TOKEN_LIFETIME_IN_SECONDS = settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].seconds


def add_custom_claims_for_user(token, user):
    token['username'] = user.username
    token['email'] = user.email
    token['has_password'] = user.has_usable_password()

    return token


def add_catalog_custom_claims_for_user(token, user):
    if user.is_staff:
        token['https://hasura.io/jwt/claims'] = {
            "x-hasura-allowed-roles": ['admin'],
            "x-hasura-default-role": "admin",
        }
    else:
        raise exceptions.AuthenticationFailed(
            'No staff permission found with the given account',
            'no_staff_permission',
        )

    return token


def get_tokens_for_hardware_by_user(user):
    token = RefreshToken.for_user(user)

    token['access'] = [{
        "type": "repository",
        "name": settings.STREAMLC_REPOSITORY_NAME,
        "actions": [
            "pull",
        ],
    }]

    return {
        'refresh': str(token),
        'access': str(token.access_token),
        'expires_in': ACCESS_TOKEN_LIFETIME_IN_SECONDS,
    }


def get_tokens_for_docker_by_user(user, access):
    token = RefreshToken.for_user(user)

    token['access'] = access

    return {
        'token': str(token.access_token),
    }


def _set_cors(response):
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Headers'] = '*'
    response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'

    return response


class HPLCTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        return add_custom_claims_for_user(token, user)

    def validate(self, attrs):
        data = super().validate(attrs)

        data['expires_in'] = ACCESS_TOKEN_LIFETIME_IN_SECONDS

        return data


class HPLCTokenObtainPairView(TokenObtainPairView):
    serializer_class = HPLCTokenObtainPairSerializer


class HPLCTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        data['expires_in'] = ACCESS_TOKEN_LIFETIME_IN_SECONDS

        return data


class HPLCTokenRefreshView(TokenViewBase):
    """
    Takes a refresh type JSON web token and returns an access type JSON web
    token if the refresh token is valid.
    """
    serializer_class = HPLCTokenRefreshSerializer


class CatalogTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        return add_catalog_custom_claims_for_user(token, user)

    def validate(self, attrs):
        data = super().validate(attrs)

        data['expires_in'] = ACCESS_TOKEN_LIFETIME_IN_SECONDS

        return data


class CatalogTokenObtainPairView(TokenObtainPairView):
    serializer_class = CatalogTokenObtainPairSerializer

    def finalize_response(self, request, response, *args, **kwargs):
        response = super(CatalogTokenObtainPairView, self).finalize_response(request, response, *args, **kwargs)

        return _set_cors(response)


class CatalogTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        data['expires_in'] = ACCESS_TOKEN_LIFETIME_IN_SECONDS

        return data


class CatalogTokenRefreshView(TokenViewBase):
    """
    Takes a refresh type JSON web token and returns an access type JSON web
    token if the refresh token is valid.
    """
    serializer_class = CatalogTokenRefreshSerializer

    def finalize_response(self, request, response, *args, **kwargs):
        response = super(CatalogTokenRefreshView, self).finalize_response(request, response, *args, **kwargs)

        return _set_cors(response)
