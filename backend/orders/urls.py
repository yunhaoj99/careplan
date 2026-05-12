from django.urls import path
from . import views

urlpatterns = [
    path('orders/', views.create_order),
    path('orders/<str:order_id>/', views.get_order),
    path('careplan/<int:careplan_id>/status/', views.get_careplan_status),
]
