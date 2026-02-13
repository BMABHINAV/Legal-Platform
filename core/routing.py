"""
WebSocket URL routing for real-time features.
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Real-time chat between client and lawyer
    re_path(r'ws/chat/(?P<room_id>\w+)/$', consumers.ChatConsumer.as_asgi()),
    
    # Video call signaling
    re_path(r'ws/video/(?P<room_id>\w+)/$', consumers.VideoCallConsumer.as_asgi()),
    
    # Notifications (typing indicators, new bookings, etc.)
    re_path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi()),
    
    # Panic button broadcasts
    re_path(r'ws/emergency/$', consumers.EmergencyConsumer.as_asgi()),
]
