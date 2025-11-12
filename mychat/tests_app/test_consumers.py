# mychat/tests_app/test_consumers.py
from channels.testing import WebsocketCommunicator
from chatwave.asgi import application
from django.test import TransactionTestCase
from django.contrib.auth.models import User
from mychat.models import ChatRoom, Message
from asgiref.sync import sync_to_async

class ChatConsumerTests(TransactionTestCase):
    def setUp(self):
        # создаём синхронно пользователя и комнату
        self.user = User.objects.create_user(username='user', password='12345')
        self.room = ChatRoom.objects.create(name='TestRoom')
        self.room.allowed_users.add(self.user)

        # даём права на удаление сообщений
        from django.contrib.auth.models import Permission
        perm = Permission.objects.get(codename='delete_message')
        self.user.user_permissions.add(perm)

        # делаем пользователя staff, чтобы проверка в consumer точно прошла
        self.user.is_staff = True
        self.user.save()

    async def test_send_message(self):
        communicator = WebsocketCommunicator(application, f"/ws/chat/{self.room.id}/")
        # ! задаём пользователя в scope ДО connect
        communicator.scope['user'] = self.user

        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.send_json_to({'message': 'Hello'})
        # ожидаем событие от consumer (action: message)
        response = await communicator.receive_json_from(timeout=2)
        self.assertEqual(response['action'], 'message')
        self.assertEqual(response['message'], 'Hello')
        self.assertEqual(response['username'], self.user.username)

        # проверить, что сообщение появилось в БД
        exists = await sync_to_async(Message.objects.filter(room=self.room, content='Hello').exists)()
        self.assertTrue(exists)

        await communicator.disconnect()

    async def test_delete_message(self):
        # Создаём сообщение через sync_to_async
        msg = await sync_to_async(Message.objects.create)(
            room=self.room, user=self.user, content='To delete'
        )

        communicator = WebsocketCommunicator(application, f"/ws/chat/{self.room.id}/")
        communicator.scope['user'] = self.user  # обязательно ДО connect!

        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.send_json_to({'action': 'delete', 'message_id': msg.id})

        # ожидаем событие удаления
        response = await communicator.receive_json_from(timeout=2)
        self.assertEqual(response['action'], 'delete')
        self.assertEqual(int(response['message_id']), msg.id)

        exists = await sync_to_async(Message.objects.filter(id=msg.id).exists)()
        self.assertFalse(exists)

        await communicator.disconnect()
