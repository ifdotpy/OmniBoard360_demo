from django.conf.urls import url
from sales.view import views_contact

urlpatterns = [
    url(r'^contact-us/$', views_contact.RequestView.as_view(), name='contact-us'),
]
