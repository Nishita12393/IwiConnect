from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('', views.event_calendar, name='event_calendar'),
    path('create/', views.create_event, name='create_event'),
    path('api/events/', views.event_list_json, name='event_list_json'),
    path('<int:event_id>/', views.event_detail, name='event_detail'),
    path('<int:event_id>/attendees/', views.event_attendees, name='event_attendees'),
    path('join/<int:event_id>/', views.join_event, name='join_event'),
    path('my/', views.my_events, name='my_events'),
] 