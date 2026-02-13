"""
WebSocket Consumers for Real-Time Features.
Handles chat, video calls, notifications, and emergency broadcasts.
"""

import json
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async


class ChatConsumer(AsyncWebsocketConsumer):
    """
    Real-time chat between client and lawyer.
    Features: typing indicators, message delivery status, read receipts.
    """
    
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        self.user = self.scope.get('user')
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Notify others that user joined
        if self.user and self.user.is_authenticated:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_joined',
                    'user_id': str(self.user.id),
                    'username': self.user.get_full_name() or self.user.username,
                }
            )
    
    async def disconnect(self, close_code):
        # Notify others that user left
        if self.user and self.user.is_authenticated:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_left',
                    'user_id': str(self.user.id),
                    'username': self.user.get_full_name() or self.user.username,
                }
            )
        
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', 'message')
        
        if message_type == 'message':
            # Save message to database
            message_id = await self.save_message(data.get('content', ''))
            
            # Broadcast message to room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message_id': message_id,
                    'content': data.get('content', ''),
                    'sender_id': str(self.user.id) if self.user else 'anonymous',
                    'sender_name': self.user.get_full_name() if self.user else 'Anonymous',
                    'timestamp': datetime.now().isoformat(),
                    'status': 'sent',
                }
            )
        
        elif message_type == 'typing':
            # Broadcast typing indicator
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'user_id': str(self.user.id) if self.user else 'anonymous',
                    'username': self.user.get_full_name() if self.user else 'Anonymous',
                    'is_typing': data.get('is_typing', False),
                }
            )
        
        elif message_type == 'read':
            # Mark messages as read
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'message_read',
                    'message_id': data.get('message_id'),
                    'reader_id': str(self.user.id) if self.user else 'anonymous',
                }
            )
    
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message_id': event['message_id'],
            'content': event['content'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'timestamp': event['timestamp'],
            'status': event['status'],
        }))
    
    async def typing_indicator(self, event):
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user_id': event['user_id'],
            'username': event['username'],
            'is_typing': event['is_typing'],
        }))
    
    async def message_read(self, event):
        await self.send(text_data=json.dumps({
            'type': 'read',
            'message_id': event['message_id'],
            'reader_id': event['reader_id'],
        }))
    
    async def user_joined(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'user_id': event['user_id'],
            'username': event['username'],
        }))
    
    async def user_left(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'user_id': event['user_id'],
            'username': event['username'],
        }))
    
    @database_sync_to_async
    def save_message(self, content):
        from .models import ChatRoom, RealTimeMessage
        try:
            room = ChatRoom.objects.get(id=self.room_id)
            message = RealTimeMessage.objects.create(
                room=room,
                sender=self.user if self.user and self.user.is_authenticated else None,
                content=content,
            )
            return str(message.id)
        except Exception:
            return None


class VideoCallConsumer(AsyncWebsocketConsumer):
    """
    WebRTC signaling for video calls.
    Handles offer/answer exchange and ICE candidates.
    """
    
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'video_{self.room_id}'
        self.user = self.scope.get('user')
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Notify room about new participant
        if self.user and self.user.is_authenticated:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'participant_joined',
                    'user_id': str(self.user.id),
                    'username': self.user.get_full_name() or self.user.username,
                }
            )
    
    async def disconnect(self, close_code):
        if self.user and self.user.is_authenticated:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'participant_left',
                    'user_id': str(self.user.id),
                }
            )
        
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        signal_type = data.get('type')
        
        if signal_type == 'offer':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'webrtc_offer',
                    'offer': data.get('offer'),
                    'sender_id': str(self.user.id) if self.user else 'anonymous',
                }
            )
        
        elif signal_type == 'answer':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'webrtc_answer',
                    'answer': data.get('answer'),
                    'sender_id': str(self.user.id) if self.user else 'anonymous',
                }
            )
        
        elif signal_type == 'ice-candidate':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'ice_candidate',
                    'candidate': data.get('candidate'),
                    'sender_id': str(self.user.id) if self.user else 'anonymous',
                }
            )
        
        elif signal_type == 'whiteboard':
            # Share whiteboard drawing data
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'whiteboard_update',
                    'data': data.get('data'),
                    'sender_id': str(self.user.id) if self.user else 'anonymous',
                }
            )
    
    async def webrtc_offer(self, event):
        await self.send(text_data=json.dumps({
            'type': 'offer',
            'offer': event['offer'],
            'sender_id': event['sender_id'],
        }))
    
    async def webrtc_answer(self, event):
        await self.send(text_data=json.dumps({
            'type': 'answer',
            'answer': event['answer'],
            'sender_id': event['sender_id'],
        }))
    
    async def ice_candidate(self, event):
        await self.send(text_data=json.dumps({
            'type': 'ice-candidate',
            'candidate': event['candidate'],
            'sender_id': event['sender_id'],
        }))
    
    async def whiteboard_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'whiteboard',
            'data': event['data'],
            'sender_id': event['sender_id'],
        }))
    
    async def participant_joined(self, event):
        await self.send(text_data=json.dumps({
            'type': 'participant_joined',
            'user_id': event['user_id'],
            'username': event['username'],
        }))
    
    async def participant_left(self, event):
        await self.send(text_data=json.dumps({
            'type': 'participant_left',
            'user_id': event['user_id'],
        }))


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    Push notifications for providers and citizens.
    New booking requests, document analysis ready, case updates.
    """
    
    async def connect(self):
        self.user = self.scope.get('user')
        
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return
        
        # Personal notification channel
        self.user_group = f'notifications_{self.user.id}'
        
        # Role-based channels
        self.role_group = f'notifications_{self.user.role}'
        
        await self.channel_layer.group_add(self.user_group, self.channel_name)
        await self.channel_layer.group_add(self.role_group, self.channel_name)
        
        await self.accept()
        
        # Send any pending notifications
        notifications = await self.get_pending_notifications()
        if notifications:
            await self.send(text_data=json.dumps({
                'type': 'pending_notifications',
                'notifications': notifications,
            }))
    
    async def disconnect(self, close_code):
        if self.user and self.user.is_authenticated:
            await self.channel_layer.group_discard(self.user_group, self.channel_name)
            await self.channel_layer.group_discard(self.role_group, self.channel_name)
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')
        
        if action == 'mark_read':
            notification_id = data.get('notification_id')
            await self.mark_notification_read(notification_id)
    
    async def notification(self, event):
        """Handle incoming notification"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'id': event.get('id'),
            'title': event.get('title'),
            'message': event.get('message'),
            'notification_type': event.get('notification_type'),
            'data': event.get('data', {}),
            'timestamp': event.get('timestamp', datetime.now().isoformat()),
        }))
    
    async def booking_request(self, event):
        """New booking request for providers"""
        await self.send(text_data=json.dumps({
            'type': 'booking_request',
            'booking_id': event.get('booking_id'),
            'client_name': event.get('client_name'),
            'service': event.get('service'),
            'urgency': event.get('urgency', 'normal'),
            'timestamp': event.get('timestamp'),
        }))
    
    async def document_ready(self, event):
        """Document analysis ready notification"""
        await self.send(text_data=json.dumps({
            'type': 'document_ready',
            'analysis_id': event.get('analysis_id'),
            'document_name': event.get('document_name'),
            'health_score': event.get('health_score'),
        }))
    
    @database_sync_to_async
    def get_pending_notifications(self):
        from .models import Notification
        try:
            notifications = Notification.objects.filter(
                user=self.user,
                is_read=False
            ).order_by('-created_at')[:10]
            return [
                {
                    'id': str(n.id),
                    'title': n.title,
                    'message': n.message,
                    'type': n.notification_type,
                    'timestamp': n.created_at.isoformat(),
                }
                for n in notifications
            ]
        except Exception:
            return []
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        from .models import Notification
        try:
            Notification.objects.filter(
                id=notification_id,
                user=self.user
            ).update(is_read=True)
        except Exception:
            pass


class EmergencyConsumer(AsyncWebsocketConsumer):
    """
    Panic Button / Legal Emergency broadcasts.
    Broadcasts emergency alerts to lawyers within radius.
    """
    
    async def connect(self):
        self.user = self.scope.get('user')
        
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return
        
        # All emergency responders (criminal lawyers)
        self.emergency_group = 'emergency_responders'
        
        # Check if user is a criminal defense lawyer
        is_responder = await self.check_if_responder()
        
        if is_responder:
            await self.channel_layer.group_add(
                self.emergency_group,
                self.channel_name
            )
        
        # Personal emergency updates
        self.user_emergency_group = f'emergency_{self.user.id}'
        await self.channel_layer.group_add(
            self.user_emergency_group,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        if hasattr(self, 'emergency_group'):
            await self.channel_layer.group_discard(
                self.emergency_group,
                self.channel_name
            )
        if hasattr(self, 'user_emergency_group'):
            await self.channel_layer.group_discard(
                self.user_emergency_group,
                self.channel_name
            )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')
        
        if action == 'panic':
            # Create emergency alert
            emergency = await self.create_emergency(
                latitude=data.get('latitude'),
                longitude=data.get('longitude'),
                description=data.get('description', 'Legal Emergency'),
            )
            
            # Broadcast to all responders
            await self.channel_layer.group_send(
                self.emergency_group,
                {
                    'type': 'emergency_alert',
                    'emergency_id': emergency['id'],
                    'user_name': self.user.get_full_name(),
                    'latitude': data.get('latitude'),
                    'longitude': data.get('longitude'),
                    'description': data.get('description'),
                    'timestamp': datetime.now().isoformat(),
                }
            )
        
        elif action == 'respond':
            emergency_id = data.get('emergency_id')
            await self.respond_to_emergency(emergency_id)
    
    async def emergency_alert(self, event):
        """Receive emergency alert"""
        await self.send(text_data=json.dumps({
            'type': 'emergency_alert',
            'emergency_id': event.get('emergency_id'),
            'user_name': event.get('user_name'),
            'latitude': event.get('latitude'),
            'longitude': event.get('longitude'),
            'description': event.get('description'),
            'timestamp': event.get('timestamp'),
        }))
    
    async def emergency_response(self, event):
        """Lawyer responded to emergency"""
        await self.send(text_data=json.dumps({
            'type': 'emergency_response',
            'emergency_id': event.get('emergency_id'),
            'responder_name': event.get('responder_name'),
            'responder_phone': event.get('responder_phone'),
            'eta': event.get('eta'),
        }))
    
    @database_sync_to_async
    def check_if_responder(self):
        try:
            if hasattr(self.user, 'provider_profile'):
                profile = self.user.provider_profile
                return 'criminal' in profile.specializations
        except Exception:
            pass
        return False
    
    @database_sync_to_async
    def create_emergency(self, latitude, longitude, description):
        from .models import LegalEmergency
        try:
            emergency = LegalEmergency.objects.create(
                user=self.user,
                latitude=latitude,
                longitude=longitude,
                description=description,
            )
            return {'id': str(emergency.id)}
        except Exception:
            return {'id': None}
    
    @database_sync_to_async
    def respond_to_emergency(self, emergency_id):
        from .models import LegalEmergency
        from django.conf import settings
        try:
            emergency = LegalEmergency.objects.get(id=emergency_id)
            emergency.responder = self.user
            emergency.status = 'responded'
            emergency.save()
            
            # Award bonus points
            if hasattr(self.user, 'provider_profile'):
                profile = self.user.provider_profile
                profile.incentive_points += settings.PANIC_BUTTON_BONUS_POINTS
                profile.save()
            
            return True
        except Exception:
            return False
