from rest_framework.generics import CreateAPIView

from hr.model.response import Response
from hr.serializers.response import ResponseSerializer


class ResponseView(CreateAPIView):
    versioning_class = None
    serializer_class = ResponseSerializer
    model = Response
