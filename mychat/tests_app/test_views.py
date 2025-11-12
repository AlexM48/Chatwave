from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from mychat.models import ChatRoom

class RoomViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user', password='12345')
        self.room = ChatRoom.objects.create(name='TestRoom')
        self.room.allowed_users.add(self.user)

    def test_room_detail_access(self):
        # Нужно залогиниться
        self.client.login(username='user', password='12345')

        url = reverse('mychat:room_detail', args=[self.room.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.room.name)
