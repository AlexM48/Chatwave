# mychat/consumers.py
import json
# from channels.generic.websocket import AsyncWebsocketConsumer
import logging
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from .models import ChatRoom, Message 
from django.contrib.auth.models import User
from channels.db import database_sync_to_async
import base64
from django.core.files.base import ContentFile
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        user = self.scope['user']
        if not user.is_authenticated:
            logger.warning("Анонимный пользователь попытался подключиться к чату")
            await self.close()
            return

        # Лог подключения
        logger.info(f"WebSocket CONNECT user={user} room_id={self.room_id}")

        # Присоединяемся к группе комнаты
        try:
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()
        except Exception as e:
            logger.error(f"Ошибка при подключении WebSocket: {e}", exc_info=True)
            await self.close()

    async def disconnect(self, close_code):
        logger.info(f"WebSocket DISCONNECT user={self.scope['user']} code={close_code}")
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            logger.debug(f"WebSocket RECEIVE raw_data={text_data}")
            data = json.loads(text_data)
            user = self.scope['user']
            message_text = data.get('message', '')
            video_base64 = data.get('video_base64', None)
            action = data.get('action', 'send')
            logger.info(f"Получено действие={action} от user={user}")
        except Exception as e:
            logger.error(f"Ошибка в receive: {e}", exc_info=True)    

        # Сохраняем видео, если есть
        video_file = None
        if video_base64:
            try:
                format, imgstr = video_base64.split(';base64,') 
                ext = format.split('/')[-1] 
                video_file = ContentFile(base64.b64decode(imgstr), name=f"video_{user.id}.{ext}")
                logger.debug(f"Видео получено от user={user.username}, размер={len(imgstr)} байт")
            except Exception as e:
                logger.error(f"Ошибка при обработке видео от {user.username}: {e}", exc_info=True)

        # 1️⃣ Создание нового сообщения
        if action == 'send' and (message_text or video_file):
            msg = await database_sync_to_async(Message.objects.create)(
                room_id=self.room_id,
                user=user,
                content=message_text,
                video=video_file
            )
            logger.info(f"Создано сообщение id={msg.id} пользователем={user.username}")

            # Рассылаем всем в комнате через группу
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message_id': msg.id,
                    'username': user.username,
                    'is_superuser': user.is_superuser,
                    'message': msg.content,
                    'video_url': msg.video.url if msg.video else None,
                    'image_url': msg.image.url if msg.image else None,
                }
            )

        # 2️⃣ Удаление сообщения
        if action == 'delete':
            message_id = data.get('message_id')
            if not message_id:
                logger.warning(f"Попытка удалить без message_id от user={user.username}")
                return  # ничего не делаем, если нет ID

            # Проверяем права пользователя
            has_permission = await sync_to_async(user.has_perm)('mychat.delete_message')

            if user.is_superuser or user.is_staff or has_permission:
                # Удаляем сообщение
                await database_sync_to_async(Message.objects.filter(id=message_id).delete)()
                logger.info(f"Сообщение id={message_id} удалено пользователем={user.username}")

                # Отправляем обратно пользователю подтверждение
                await self.send(text_data=json.dumps({
                    'action': 'delete',
                    'message_id': message_id,
                }))

                # Также уведомляем других участников
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'delete_message',
                        'message_id': message_id,
                    }
                )
            else:
                logger.warning(f"Отказано в удалении user={user.username}, нет прав")


    # Отправка нового сообщения всем клиентам
    async def chat_message(self, event):
        message = event.get('message')
        if message is None:
            logger.debug(f"Отправка сообщения в комнату {self.room_group_name}: {event}")
            return  # просто выходим, не ломаем соединение
        
        logger.debug(f"Отправка сообщения в комнату {self.room_group_name}: {event}")
        await self.send_json({
            'action': 'message',
            'message_id': event['message_id'],
            'username': event['username'],
            'is_superuser': event['is_superuser'],
            'message': event.get('content') or event.get('message'),
            'video_url': event['video_url'],
            'image_url': event['image_url'],
        })

    # Отправка события удаления
    async def delete_message(self, event):
        logger.debug(f"Удаление сообщения event={event}")
        await self.send_json({
            'action': 'delete',
            'message_id': event['message_id'],
        })

