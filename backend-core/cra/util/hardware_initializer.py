import binascii
import secrets
import string

from cra.crypto import encrypt_arc4, decrypt_arc4

KEY = 'XL4nW'.encode('ascii')

ascii_5bit = (string.digits + string.ascii_lowercase)[:2**5]


def bytes_to_bits(data):
    binary_len = len(data) * 8
    return bin_str(int(data.hex(), 16)).zfill(binary_len)


def bin_str(num):
    return bin(num)[2:]


def bits_to_char5bit(bits):
    return ascii_5bit[int(bits, 2)]


def char5bit_to_bits(char):
    ind = ascii_5bit.index(char)
    return bin_str(ind).zfill(5)


assert (bits_to_char5bit(char5bit_to_bits('0')) == '0')
assert (char5bit_to_bits(bits_to_char5bit('00100')) == '00100')


def bytes_to_string5bit(data):
    binary = bytes_to_bits(data)
    binary_len = len(binary)

    res = ''
    for i in range(5, binary_len + 1, 5):
        res += bits_to_char5bit(binary[i - 5:i])
    return res


def string5bit_to_bytes(data):
    res = ''
    for char in data:
        res += char5bit_to_bits(char)

    return int(res, 2).to_bytes(len(data) * 5 // 8, byteorder='big')


assert (bytes_to_string5bit(string5bit_to_bytes('lkfbsr35')) == 'lkfbsr35')
assert (string5bit_to_bytes(bytes_to_string5bit(b'\xad\x1e\xbele')) == b'\xad\x1e\xbele')


def str_insert(_str, pos, substr):
    return _str[:pos] + substr + _str[pos:]


def str_remove_at(s, i):
    return s[:i] + s[i + 1:]


def salt_bytes(data, salt):
    coords = [1, 12, 23, 34]
    binary = bytes_to_bits(data)[4:]

    bin_salt = bin_str(int(salt, 16)).zfill(len(coords))

    salted_bin = binary
    for i, c in enumerate(coords):
        salted_bin = str_insert(salted_bin, c + i, bin_salt[i])

    return int(salted_bin, 2).to_bytes(len(data), byteorder='big')


def unsalt_bytes(data):
    coords = [1, 12, 23, 34]
    binary = bytes_to_bits(data)

    unsalted_bin = binary
    for i, c in enumerate(coords):
        unsalted_bin = str_remove_at(unsalted_bin, c)

    return int(unsalted_bin, 2).to_bytes(len(data), byteorder='big')


def gen_hardware_key():
    key = secrets.token_hex(1)
    return key


def encode_serial(serial):
    serial_encoded = binascii.unhexlify('0' + serial[-9:])

    salt = secrets.token_hex(1)[0]

    serial_salted = salt_bytes(serial_encoded, salt)
    encrypted = encrypt_arc4(serial_salted, KEY)

    return bytes_to_string5bit(encrypted)


def decode_serial(fake_serial):
    fake_serial_bytes = string5bit_to_bytes(fake_serial)

    decrypted = decrypt_arc4(fake_serial_bytes, KEY)

    decrypted_usalted = unsalt_bytes(decrypted)

    return binascii.hexlify(decrypted_usalted).decode('ascii')[1:]


assert (decode_serial(encode_serial('fa54fa54fa54fa54')) == '4fa54fa54')
