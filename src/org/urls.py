from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^(?P<org_id>[-\w]+)/$', views.show_organization),
]