from django.urls import path

from . import views

app_name = 'tickets'

urlpatterns = [
    path('', views.TicketListView.as_view(), name='list'),
    path('crear/', views.TicketCreateView.as_view(), name='create'),
    path('<int:pk>/', views.TicketDetailView.as_view(), name='detail'),
    path('<int:pk>/editar/', views.TicketUpdateView.as_view(), name='edit'),
    path('<int:pk>/asignar/', views.TicketAssignView.as_view(), name='assign'),
    path('<int:pk>/trabajo/', views.TicketWorkUpdateView.as_view(), name='work'),
    path('<int:pk>/comentar/', views.add_comment, name='comment'),
    path('<int:pk>/archivo/', views.upload_file, name='file'),
    path('<int:pk>/cerrar/', views.close_ticket, name='close'),
    path('<int:pk>/cancelar/', views.cancel_ticket, name='cancel'),
]
