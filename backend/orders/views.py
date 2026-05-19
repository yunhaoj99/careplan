from rest_framework.decorators import api_view
from rest_framework.response import Response

from . import services


@api_view(['POST'])
def create_order(request):
    result = services.create_order(request.data)
    return Response(result, status=201)


@api_view(['GET'])
def get_order(request, order_id):
    result = services.get_order_detail(order_id)
    return Response(result)


@api_view(['GET'])
def get_careplan_status(request, careplan_id):
    result = services.get_careplan_status(careplan_id)
    return Response(result)
