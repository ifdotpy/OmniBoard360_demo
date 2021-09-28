from rest_framework.generics import CreateAPIView
from sales.serializers.request import RequestSerializer


class RequestView(CreateAPIView):
    versioning_class = None
    serializer_class = RequestSerializer
