from rest_framework import status
from rest_framework.test import APITestCase


class WebsocketTests(APITestCase):
    USERNAME1 = 'Degrijo'
    EMAIL1 = 'degrijoyarik@gmail.com'
    PASSWORD1 = 'TestPassword'
    USERNAME2 = 'Denis'
    EMAIL2 = 'denpolitikin@gmail.com'
    PASSWORD2 = 'TestPassword'
    ROOM_NAME = 'TestRoom'
    fixtures = ['main.json']
    token1 = ''
    token2 = ''

    def signup(self, client, username, email, password):
        data = {'username': username, 'email': email, 'password': password}
        response = client.post('/auth/signup/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def login(self, client, username, password):
        data = {'username_or_email': username, 'password': password}
        response = client.post('/auth/login/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + response.data['access'])
        return response.data['access']

    def create_room(self, client):
        data = {'username': '', 'name': self.ROOM_NAME}
        response = client.post('/room/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.data['password']

    def connect_room(self, client, password):
        data = {'username': '', 'name': self.ROOM_NAME, 'password': password}
        response = client.post('/room/connect/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_all(self):
        self.client2 = self.client_class()
        self.signup(self.client, self.USERNAME1, self.EMAIL1, self.PASSWORD1)
        self.signup(self.client2, self.USERNAME2, self.EMAIL2, self.PASSWORD2)
        self.token1 = self.login(self.client, self.USERNAME1, self.PASSWORD1)
        self.token2 = self.login(self.client2, self.USERNAME2, self.PASSWORD2)
        password = self.create_room(self.client)
        self.connect_room(self.client2, password)
