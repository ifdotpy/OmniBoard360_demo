import os
import secrets

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from django.conf import settings


def load_initializer_private_key_bytes():
    path = os.path.join(settings.SECRET_FILES_DIR, 'initializer/private.der')

    with open(path, "rb") as key_file:
        return key_file.read()


def create_rsa_keys_bytes():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())
    private_der = private_key.private_bytes(encoding=serialization.Encoding.DER,
                                            format=serialization.PrivateFormat.TraditionalOpenSSL,
                                            encryption_algorithm=serialization.NoEncryption())
    public_der = private_key.public_key().public_bytes(encoding=serialization.Encoding.DER,
                                                       format=serialization.PublicFormat.SubjectPublicKeyInfo)
    return private_der, public_der


def sign_pss(message, key):
    private_key = serialization.load_der_private_key(key, password=None, backend=default_backend())

    return private_key.sign(message, padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                            hashes.SHA256())


def gen_raspberry_cpuid():
    return secrets.token_hex(8)
