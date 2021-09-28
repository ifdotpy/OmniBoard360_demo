import os

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers import algorithms, Cipher
from django.conf import settings


def _load_initializer_private_key():
    path = os.path.join(settings.SECRET_FILES_DIR, 'initializer/private.der')

    with open(path, "rb") as key_file:
        public_key = serialization.load_der_private_key(key_file.read(), password=None, backend=default_backend())
    return public_key


def load_initializer_public_key_bytes():
    path = os.path.join(settings.SECRET_FILES_DIR, 'initializer/public.der')

    with open(path, "rb") as key_file:
        return key_file.read()


def verify_pss(message, original_message, key):
    try:
        public_key = serialization.load_der_public_key(key, backend=default_backend())

        public_key.verify(message, original_message,
                          padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                          hashes.SHA256())
    except InvalidSignature:
        return False
    return True


# Not very secure, use only for encode serial
def encrypt_arc4(message: bytes, key):
    algorithm = algorithms.ARC4(key)
    cipher = Cipher(algorithm, mode=None, backend=default_backend())
    encryptor = cipher.encryptor()
    return encryptor.update(message)


def decrypt_arc4(message: bytes, key):
    algorithm = algorithms.ARC4(key)
    cipher = Cipher(algorithm, mode=None, backend=default_backend())
    decryptor = cipher.decryptor()
    return decryptor.update(message)
