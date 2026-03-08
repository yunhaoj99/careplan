from django.urls import path
from . import views

urlpatterns = [
    path('orders/', views.create_order),
    path('orders/<str:order_id>/', views.get_order),
]
