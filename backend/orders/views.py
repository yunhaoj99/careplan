from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Order, CarePlan
from . import services


@api_view(['POST'])
def create_order(request):
    result = services.create_order(request.data)
    return Response(result, status=201)


@api_view(['GET'])
def get_order(request, order_id):
    try:
        result = services.get_order_detail(order_id)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=404)
    return Response(result)


@api_view(['GET'])
def get_careplan_status(request, careplan_id):
    try:
        result = services.get_careplan_status(careplan_id)
    except CarePlan.DoesNotExist:
        return Response({'error': 'CarePlan not found'}, status=404)
    return Response(result)
