import base64

from django.db import transaction
from rest_framework import status

from siebox.model import Hardware, Device
from cra.util.hardware_initializer import gen_hardware_key, encode_serial


def initialize_hardware(uname, public_key, type, model, cpuid):
    update = False
    devices = Device.objects.filter(cpuid=cpuid)

    if devices.count() > 0:
        update = True

    key = gen_hardware_key()

    public_key = base64.b64decode(public_key)

    serial = encode_serial(cpuid)

    if update:
        device = devices[0]

        values = {'type': type, 'model': model}

        for key, value in values.items():
            setattr(device, key, value)
        device.save(update_fields=values.keys())

        hardwareuser = device.userforhardware
        hardwareuser.public_key = public_key
        hardwareuser.save(update_fields=['public_key'])

        serial = device.hardware_ptr_id
    else:
        with transaction.atomic():
            hw = Hardware.create(serial, key, type, model, cpuid, public_key)
            Device.create(hw)

    return {'data': {'serial': serial}, 'status': status.HTTP_200_OK if update else status.HTTP_201_CREATED}
