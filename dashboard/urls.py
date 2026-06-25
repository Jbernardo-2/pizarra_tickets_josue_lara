from django.urls import path

from .views import DashboardView, TicketBoardView

app_name = 'dashboard'

urlpatterns = [
    path('', DashboardView.as_view(), name='index'),
    path('pizarra/', TicketBoardView.as_view(), name='board'),
]
