from rest_framework import status
from rest_framework.authentication import BasicAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.views import APIView

from cra.util.auth import get_userpassword_from_basic_auth
from authentication.jwt import get_tokens_for_docker_by_user


def grant_access(user, request_params):
    """Produces a list of allowed actions, one for each access right
    requested by a `scope` parameter."""
    allowed_actions = []
    scope = request_params.get('scope')
    if not isinstance(scope, list):
        scope = [scope]
    if scope:
        for requested_permissions in scope:
            # Each permission of form [u'repository:my/image:push,pull']
            if requested_permissions is not None:
                type, name, actions = requested_permissions.split(':')
                actions = ['pull']
                if user.is_staff:
                    actions.append('push')
                allowed_actions.append({'type': type, 'name': name, 'actions': actions})
    return allowed_actions


class DockerTokenObtainView(APIView):
    def get(self, request, format=None):
        """Respond to authentication requests as prescribed by
        https://github.com/docker/distribution/blob/master/docs/spec/auth/token.md
        """

        # scope = self.kwargs.get('scope')
        try:
            user, _ = BasicAuthentication().authenticate(request)
        except AuthenticationFailed:
            user = None

        if user and user.is_authenticated:
            request_params = request.query_params
            access = grant_access(user, request_params)
            data = get_tokens_for_docker_by_user(user, access)
            return Response(status=status.HTTP_200_OK, data=data)
        else:
            try:
                username, password = get_userpassword_from_basic_auth(request)
                if username == 'jwt':
                    data = {'token': password}
                    return Response(status=status.HTTP_200_OK, data=data)
            except Exception:
                pass
        return Response(status=status.HTTP_403_FORBIDDEN, data={'error': 'Header has no valid basic auth and token'})
