from django.contrib import admin

from cra.models import Challenge
from siebox.model.hardware_user import UserForHardware

admin.site.register(Challenge)
admin.site.register(UserForHardware)
