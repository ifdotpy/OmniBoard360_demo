import base64
from time import sleep

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status

from siebox.model.hardware_user import UserForHardware
from cra.util.test import create_rsa_keys_bytes, sign_pss, load_initializer_private_key_bytes, gen_raspberry_cpuid
from siebox.model import Hardware, Device
from siebox.util.test import ExtendedAPITestCase


def get_challenge(client, url):
    response = client.get(url)
    challenge = response.data['challenge'].encode('ascii')
    return challenge, response


def do_challenge(challenge, private):
    return base64.b64encode(sign_pss(challenge, private))


def auth_with_challenge(client, url, sid, uname, challenge_response):
    return client.post(url, {'sid': sid, 'challenge_response': challenge_response, 'uname': uname, 'type': 'hardware'})


def auth_initialize_action_with_challenge(client, url, sid, challenge_response, public_key, cpuid):
    return client.post(
        url, {
            'sid': sid,
            'challenge_response': challenge_response,
            'action': 'initialize-hardware',
            'payload': {
                'public_key': public_key,
                'cpuid': cpuid,
                'type': 'hub',
                'model': 'slc'
            }
        })


class CRAHardwareAuthEndpointTestCase(ExtendedAPITestCase):
    def setUp(self):
        self.url_get_challenge = reverse('get_challenge_view')
        self.url_verify_auth = reverse('verify_auth_view')

        self.private, self.public = create_rsa_keys_bytes()

        self.box = Hardware.create(serial='QAK-DEW-NBD', key='3412', type='hub', public_key=self.public)

    def test_success_auth(self):
        challenge, response = get_challenge(self.client, self.url_get_challenge)

        challenge_response = do_challenge(challenge, self.private)

        response = auth_with_challenge(self.client,
                                       self.url_verify_auth,
                                       sid=response.data['sid'],
                                       uname=self.box.id,
                                       challenge_response=challenge_response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_fake_auth(self):
        challenge, response = get_challenge(self.client, self.url_get_challenge)

        fake_private, fake_public = create_rsa_keys_bytes()

        challenge_response = do_challenge(challenge, fake_private)

        response = auth_with_challenge(self.client,
                                       self.url_verify_auth,
                                       sid=response.data['sid'],
                                       uname=self.box.id,
                                       challenge_response=challenge_response)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_expired_challenge(self):
        challenge, response = get_challenge(self.client, self.url_get_challenge)

        challenge_response = do_challenge(challenge, self.private)

        sleep(11)

        response = auth_with_challenge(self.client,
                                       self.url_verify_auth,
                                       sid=response.data['sid'],
                                       uname=self.box.id,
                                       challenge_response=challenge_response)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CRAInitializeActionEndpointTestCase(ExtendedAPITestCase):
    def setUp(self):
        self.url_get_challenge = reverse('get_challenge_view')
        self.url_authenticated_action = reverse('authenticated_action_view')
        self.url_verify_auth = reverse('verify_auth_view')

        self.serial = gen_raspberry_cpuid()

        self.initializer_private = load_initializer_private_key_bytes()
        self.private, self.public = create_rsa_keys_bytes()

        self.device_count = Device.objects.count()
        self.hardware_user_count = UserForHardware.objects.count()
        self.user_count = User.objects.count()

    def test_success_initialization_with_auth(self):
        challenge, response = get_challenge(self.client, self.url_get_challenge)

        challenge_response = do_challenge(challenge, self.initializer_private)

        public_key = base64.b64encode(self.public).decode('ascii')

        response = auth_initialize_action_with_challenge(self.client,
                                                         self.url_authenticated_action,
                                                         sid=response.data['sid'],
                                                         challenge_response=challenge_response,
                                                         public_key=public_key,
                                                         cpuid=self.serial)

        serial = response.data['serial']

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(self.device_count + 1, Device.objects.count())
        self.assertEqual(self.hardware_user_count + 1, UserForHardware.objects.count())
        self.assertEqual(self.user_count + 1, User.objects.count())

        # Authentication

        challenge, response = get_challenge(self.client, self.url_get_challenge)

        challenge_response = do_challenge(challenge, self.private)

        response = auth_with_challenge(self.client,
                                       self.url_verify_auth,
                                       sid=response.data['sid'],
                                       uname=serial,
                                       challenge_response=challenge_response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_failed_initialization(self):
        challenge, response = get_challenge(self.client, self.url_get_challenge)

        #  change self.initializer_private to self.private
        challenge_response = do_challenge(challenge, self.private)

        public_key = base64.b64encode(self.public).decode('ascii')

        response = auth_initialize_action_with_challenge(self.client,
                                                         self.url_authenticated_action,
                                                         sid=response.data['sid'],
                                                         challenge_response=challenge_response,
                                                         public_key=public_key,
                                                         cpuid=self.serial)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.assertEqual(self.device_count, Device.objects.count())
        self.assertEqual(self.hardware_user_count, UserForHardware.objects.count())
        self.assertEqual(self.user_count, User.objects.count())

    def test_duplicated_initialization(self):
        challenge, response = get_challenge(self.client, self.url_get_challenge)

        challenge_response = do_challenge(challenge, self.initializer_private)

        public_key = base64.b64encode(self.public).decode('ascii')

        response = auth_initialize_action_with_challenge(self.client,
                                                         self.url_authenticated_action,
                                                         sid=response.data['sid'],
                                                         challenge_response=challenge_response,
                                                         public_key=public_key,
                                                         cpuid=self.serial)

        serial = response.data['serial']

        # DUPLICATE REQUEST
        challenge, response = get_challenge(self.client, self.url_get_challenge)

        challenge_response = do_challenge(challenge, self.initializer_private)

        public_key = base64.b64encode(self.public).decode('ascii')

        response = auth_initialize_action_with_challenge(self.client,
                                                         self.url_authenticated_action,
                                                         sid=response.data['sid'],
                                                         challenge_response=challenge_response,
                                                         public_key=public_key,
                                                         cpuid=self.serial)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(serial, response.data['serial'])

        self.assertTrue(Device.objects.filter(cpuid=self.serial).exists())

        self.assertEqual(self.device_count + 1, Device.objects.count())
        self.assertEqual(self.hardware_user_count + 1, UserForHardware.objects.count())
        self.assertEqual(self.user_count + 1, User.objects.count())


class DockerAuthEndpointTestCase(ExtendedAPITestCase):
    def setUp(self):
        self.url_token_obtain_docker = reverse('token_obtain_docker')

    def test_token_in_password(self):
        token = 'faketoken'
        auth_headers = {
            'HTTP_AUTHORIZATION': 'Basic ' + base64.b64encode(f'jwt:{token}'.encode("ascii")).decode("ascii"),
        }
        response = self.client.get(self.url_token_obtain_docker, **auth_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(token, response.data['token'])

    def test_basic_auth(self):
        username = 'testuser@test.com'
        password = '123456'
        user = User.objects.create_superuser(username=username, password=password)

        auth_headers = {
            'HTTP_AUTHORIZATION': 'Basic ' + base64.b64encode(f'{username}:{password}'.encode("ascii")).decode("ascii"),
        }
        response = self.client.get(self.url_token_obtain_docker, **auth_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
