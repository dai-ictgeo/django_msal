from django.urls import path

from . import views
from . import conf

urlpatterns = [
    path(conf.DJANGO_MSAL_LOGIN_PATH, views.login, name='login'),
    path(conf.DJANGO_MSAL_LOGOUT_PATH, views.logout, name='logout'),
    path(conf.DJANGO_MSAL_LANDING_PATH, views.landing, name='landing'),
    path(conf.DJANGO_MSAL_REDIRECT_PATH, views.authorize, name='authorize'),
    path('%slogin/' % conf.DJANGO_MSAL_ADMIN_PATH, views.login),
    path('%slogout/'% conf.DJANGO_MSAL_ADMIN_PATH, views.logout),
    path('%spassword_change/' % conf.DJANGO_MSAL_ADMIN_PATH, views.password_area_removed),
    path('%spassword_change/done/' % conf.DJANGO_MSAL_ADMIN_PATH, views.password_area_removed),
    path('%sauth/user/<int:pk>/password/' % conf.DJANGO_MSAL_ADMIN_PATH, views.password_area_removed),
]