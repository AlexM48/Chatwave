
from django.urls import path
from .views import (
    chat_index,
    room_list,
    room_detail,
    create_room,
    delete_room,  
    delete_message,
    manage_access,
    send_message,
)

app_name = 'mychat'

urlpatterns = [
    path('', chat_index, name='index'),
    path("room_list/", room_list, name="room_list"),
    path("room/<int:room_id>/", room_detail, name="room_detail"),
    path('room/<int:room_id>/send/', send_message, name='send_message'),
    path("create_room/", create_room, name="create_room"),
    path("delete_room/<int:room_id>/", delete_room, name="delete_room"),
    path("delete_message/<int:message_id>/", delete_message, name="delete_message"),
    path('room/<int:room_id>/access/', manage_access, name='manage_access'),
]
