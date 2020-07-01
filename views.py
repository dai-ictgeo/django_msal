import logging
import uuid

from django.contrib.auth import get_user_model, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.template.response import TemplateResponse

from .auth import MSALAuthBackend
from . import conf

User = get_user_model()

logger = logging.getLogger(__name__)

@login_required(redirect_field_name=conf.DJANGO_MSAL_REDIRECT_FIELD_NAME)
def landing(request):
    context = {
        'name': request.user.microsoftuser.name,
        'preferred_username': request.user.microsoftuser.preferred_username,
        'app_name': conf.DJANGO_MSAL_APP_NAME,
    }
    return TemplateResponse(request, 'DJANGO_MSAL/landing.html', context=context)


# We have choosen to remove some urls/views that are used by Django admin, such as change password, etc.
@login_required(redirect_field_name=conf.DJANGO_MSAL_REDIRECT_FIELD_NAME)
def password_area_removed(request, pk=None):
    context = {

    }
    return TemplateResponse(request, 'DJANGO_MSAL/password_area_removed.html', context=context)


def logout(request):
    # You can have a user logged out of the Django app when then log out of their MS account.
    # Define a Logout URL when registering your app in the Azure portal.

    # Logout of Django app
    auth_logout(request)

    if conf.DJANGO_MSAL_LOGOUT_OF_MS_ACCOUNT:
        return redirect(
            "https://login.microsoftonline.com/common/oauth2/v2.0/logout"
            "?post_logout_redirect_uri=%s" % (conf.DJANGO_MSAL_ABSOLUTE_LOGOUT_PATH)
        )
    return redirect('login')


def login(request):
    # MSAL uses the state parameter as a CSRF token to protect agains cross site scripting. Create unique id that will be returned by MSAL
    request.session['state'] = str(uuid.uuid4())

    # By default Django uses ?next=<url> to redirect a user after login
    # The redirect_field_name can be changed via settings
    request.session['next_url'] = request.GET.get(conf.DJANGO_MSAL_REDIRECT_FIELD_NAME, '/%s' % conf.DJANGO_MSAL_LANDING_PATH)

    auth_url = MSALAuthBackend().build_auth_url(scopes=conf.DJANGO_MSAL_SCOPE, state=request.session['state'])

    context = {
        'auth_url': auth_url,
        'auth_error': request.session.get('auth_error', False),
        'app_name': conf.DJANGO_MSAL_APP_NAME,
    }

    # We do not want to show the same auth error again. Delete auth_error session variable
    try:
        del request.session['auth_error']
    except KeyError:
        pass

    return TemplateResponse(request, 'DJANGO_MSAL/login.html', context=context)

def authorize(request):
    # The auth_error session variable is used to pass error information back to login page if an error occurs
    # It should not be set at this point as it is deleted in login view, but lets make sure
    try:
        del request.session['auth_error']
    except KeyError:
        pass

    auth_backend = MSALAuthBackend()

    if not auth_backend.validate_request(request):
        return redirect('login')

    # validate request makes sure there is a code in request GET vars
    token_result = auth_backend.acquire_token_by_authorization_code(request)
    if not auth_backend.validate_token_result(request, token_result):
        return redirect('login')

    # validate token claims for tenant and user
    token_claims = token_result.get('id_token_claims')

    tenant = auth_backend.validate_token_claims_tenant(request, token_claims)
    if not tenant:
        return redirect('login')

    user = auth_backend.validate_token_claims_user(request, token_claims)
    if not user:
        return redirect('login')

    # Log user in
    auth_backend.login(request, user)

    next_url = request.session.get('next_url', '/%s' % conf.DJANGO_MSAL_LANDING_PATH)
    return redirect(next_url)
