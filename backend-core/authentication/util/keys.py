import os

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.x509 import load_pem_x509_certificate


def load_file_der_private_key(path):
    with open(path, "rb") as key_file:
        return serialization.load_der_private_key(key_file.read(), password=None, backend=default_backend())


def load_file_pem_x509_certificate(path):
    with open(path, "rb") as key_file:
        return load_pem_x509_certificate(key_file.read(), backend=default_backend())


def load_jwt_keys(secrets_path):
    folder_path = os.path.join(secrets_path, 'jwt/')
    try:
        private_key = load_file_der_private_key(os.path.join(folder_path, 'private.der')).private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()).decode('ascii')

        public_key = load_file_pem_x509_certificate(os.path.join(folder_path, 'jwt.crt')).public_key().public_bytes(
            encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo).decode('ascii')
    except FileNotFoundError:
        return None, None

    return private_key, public_key
