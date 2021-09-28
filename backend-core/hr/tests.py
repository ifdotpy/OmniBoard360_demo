from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.utils import json

from hr.model.position import Position
from hr.serializers.position import PositionSerializer
from siebox.util.test import ExtendedAPITestCase


class PositionTests(ExtendedAPITestCase):
    def test_can_get_position(self):
        position = Position.objects.create(title='Lead Senior Chief Office Cleaner',
                                           description="Welcome",
                                           hourly_min=40,
                                           hourly_max=180)
        response = self.client.get(reverse('position', kwargs={'pk': position.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, PositionSerializer(instance=position).data)

    def test_can_get_positions_list(self):
        position = Position.objects.create(title='Lead Senior Chief Office Cleaner',
                                           description="Welcome",
                                           hourly_min=40,
                                           hourly_max=180)
        response = self.client.get(reverse('positions-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0], PositionSerializer(instance=position).data)


class ResponseTests(ExtendedAPITestCase):
    def setUp(self):
        position = Position.objects.create(title='Lead Senior Chief Office Cleaner',
                                           description="Welcome",
                                           hourly_min=40,
                                           hourly_max=180)
        self.valid_payload = {
            'name': 'Evan You',
            'phone': '+1-202-555-0178',
            'email': 'yyx990803@gmail.com',
            'cv_link': 'https://evanyou.me/',
            'position_id': position.id,
            'comment': 'Husband, father of two, creator of @vuejs and connoisseur of sushi.'
        }
        self.invalid_payload = {
            'name': '',
            'phone': '',
            'email': '',
            'cv_link': '',
            'position_id': position.id,
            'comment': ''
        }

    def test_can_post_valid_response(self):
        response = self.client.post(reverse('response'), self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_can_post_invalid_response(self):
        response = self.client.post(reverse('response'), self.invalid_payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
