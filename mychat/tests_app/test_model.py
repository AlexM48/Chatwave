from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from mychat.models import ChatRoom, Message, UserProfile
import time

class ChatRoomModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user', password='12345')
        self.staff = User.objects.create_user(username='staff', password='12345', is_staff=True)
        self.superuser = User.objects.create_superuser(username='admin', password='12345')
        self.room_locked = ChatRoom.objects.create(name='LockedRoom', is_locked=True)
        self.room_unlocked = ChatRoom.objects.create(name='OpenRoom', is_locked=False)
        self.room_locked.allowed_users.add(self.user)

    def test_user_has_access_unlocked_room(self):
        self.assertTrue(self.room_unlocked.user_has_access(self.user))
        self.assertTrue(self.room_unlocked.user_has_access(self.staff))
        self.assertTrue(self.room_unlocked.user_has_access(self.superuser))

    def test_user_has_access_locked_room(self):
        # Разрешённый пользователь
        self.assertTrue(self.room_locked.user_has_access(self.user))
        # Не разрешённый пользователь
        other_user = User.objects.create_user(username='other', password='12345')
        self.assertFalse(self.room_locked.user_has_access(other_user))
        # Staff и superuser имеют доступ
        self.assertTrue(self.room_locked.user_has_access(self.staff))
        self.assertTrue(self.room_locked.user_has_access(self.superuser))

class MessageModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user', password='12345')
        self.room = ChatRoom.objects.create(name='TestRoom')
        self.message = Message.objects.create(room=self.room, user=self.user, content='Hello!')

    def test_as_dict_serialization(self):
        data = self.message.as_dict()
        self.assertEqual(data['username'], self.user.username)
        self.assertEqual(data['content'], 'Hello!')
        self.assertIsNone(data['video_url'])
        self.assertFalse(data['is_superuser'])
        self.assertIn('created_at', data)

class UserProfileModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user', password='12345')
        self.profile = UserProfile.objects.create(user=self.user)

    def test_update_last_seen(self):
        old_time = self.profile.last_seen
        time.sleep(1)  # чтобы точно отличалось время
        self.profile.update_last_seen()
        self.profile.refresh_from_db()
        self.assertGreater(self.profile.last_seen, old_time)
