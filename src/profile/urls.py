from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.default),
    url(r'^(?P<user_id>\w+)/$', views.show_profile, name='user_profile'),
    url(r'^(?P<user_id>\w+)/create/student/$', views.create_student_portfolio),
    url(r'^(?P<user_id>\w+)/create/organization/$', views.create_organization),
]