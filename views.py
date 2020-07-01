import logging
import msal
import uuid

from django.contrib.auth import get_user_model, login as auth_login, logout as auth_logout, authenticate
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.template.response import TemplateResponse


from .models import MicrosoftUser, MicrosoftTenant
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

    auth_url = _build_auth_url(scopes=conf.DJANGO_MSAL_SCOPE, state=request.session['state'])

    context = {
        'auth_url': auth_url,
        'version': msal.__version__,
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

    # Check the state variable that acts as CSRF token
    if request.GET['state'] != request.session['state']:
        return redirect('login')

    if request.GET.get('error', False):
        request.session['auth_error'] = {
            'error': request.GET.get('error'),
            'message': 'There was a problem authenticating you for this application'
        }
        return redirect('login')
    if request.GET.get('code', False):
        cache = _load_cache(request)
        result = _build_msal_app(cache=cache).acquire_token_by_authorization_code(
            request.GET['code'],
            scopes=conf.DJANGO_MSAL_SCOPE,  # Misspelled scope would cause an HTTP 400 error here
            redirect_uri=conf.DJANGO_MSAL_ABSOLUTE_REDIRECT_PATH)
        if 'error' in result:
            request.session['auth_error'] = {
                'error': result.get('error'),
                'message': 'There was a problem authenticating you for this application'
            }
            return redirect('login')

        id_token_claims = result.get('id_token_claims')
        # Check to make sure user have a valid Tenant ID
        tid = id_token_claims.get('tid', False)
        if not tid:
            request.session['auth_error'] = {
                'error': 'Missing Tenant ID',
                'message': 'There was a problem authenticating you for this application'
            }
            return redirect('login')

        tenant = None

        if conf.DJANGO_MSAL_RESTRICT_TENANTS:
            # Only allow tenants that are active in the MicrosoftTenant table
            try:
                MicrosoftTenant.objects.get(tid=tid, is_active=True)
            except MicrosoftTenant.DoesNotExist:
                request.session['auth_error'] = {
                    'error': 'Invalid Tenant ID',
                    'message': 'There was a problem authenticating you for this application',
                }
                return redirect('login')
        else:
            # We have not restricted tenants, but we want to keep track of what tentant a users is associated with
            # If the tenant is not yet in the system, create it
            try:
                tenant = MicrosoftTenant.objects.get(tid=tid)
            except MicrosoftTenant.DoesNotExist:
                tenant = MicrosoftTenant.objects.create(tid=tid, name=tid)

        oid = id_token_claims.get('oid', False)
        if not oid:
            request.session['auth_error'] = {
                'error': 'Missing Object ID',
                'message': 'There was a problem authenticating you for this application'
            }
            return redirect('login')

        try:
            microsoftuser = MicrosoftUser.objects.get(oid=oid)
            user = microsoftuser.user
        except MicrosoftUser.DoesNotExist:
            # The user is part of an accepted tenant, but has not yet logged into the application
            # Create a new user
            # We still use the User model set by the Django and therefore need a username and password
            # The preferred_username from Microsoft is not guaranteed to be unique.
            # We need to create a username that is unique to Django User model
            preferred_username = id_token_claims.get('preferred_username')
            user_email = None
            try:
                validate_email(preferred_username)
                user_email = preferred_username
            except ValidationError:
                user_email = None
            name = id_token_claims.get('name')
            username = preferred_username
            username_exists = True
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                username_exists = False

            while username_exists:
                username_suffix = 1
                username = '%s_%s' % (preferred_username, username_suffix)
                try:
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    username_exists = False

            # We will not be using this password, but the Django User model requires it
            random_password = BaseUserManager().make_random_password()
            if user_email:
                user = User.objects.create(username=username, password=random_password, email=user_email)
            else:
                user = User.objects.create(username=username, password=random_password)
            user.microsoftuser.oid = oid
            user.microsoftuser.tenant = tenant
            user.microsoftuser.name = name
            user.microsoftuser.preferred_username = preferred_username
            user.microsoftuser.save()
            logging.info('Created a new User and Microsoft User %s' % (user.username))

            if conf.DJANGO_MSAL_SEND_NEW_ACCOUNT_EMAILS:
                # Email site admins about new user sign-in
                from_email = conf.DJANGO_MSAL_FROM_EMAIL
                ####################################################################
                to_email = 'matt@langeman.net'
                subject = '%s - New Account Created' % (conf.DJANGO_MSAL_APP_NAME)
                message = render_to_string('django_msal/new_account_created_email.html', {
                    'name': user.microsoftuser.name,
                    'preferred_username': user.microsoftuser.preferred_username,
                    'app_name': conf.DJANGO_MSAL_APP_NAME
                })
                send_mail(subject, "", from_email, [to_email],
                            fail_silently=False, html_message=message)
                logger.info('Sent email to admin about new account creation')
                ####################################################################
                # Email user about their new account if we have their email in the form of preferred_username
                if user_email:
                    to_email = user_email
                    subject = 'Welcome to %s' % (conf.DJANGO_MSAL_APP_NAME)
                    message = render_to_string('django_msal/new_user_welcome_email.html', {
                        'name': user.microsoftuser.name,
                        'preferred_username': user.microsoftuser.preferred_username,
                        'app_name': conf.DJANGO_MSAL_APP_NAME
                    })
                    send_mail(subject, "", from_email, [to_email],
                                fail_silently=False, html_message=message)
                    logger.info('Sent welcome email to new user')
                ####################################################################

        # We have a user that has been authorized by an Microsoft Tenant. Log them in
        auth_login(request, user, backend='django_msal.auth.MSALAuthBackend')
        _save_cache(request, cache)

    next_url = request.session.get('next_url', '/%s' % conf.DJANGO_MSAL_LANDING_PATH)
    return redirect(next_url)


def _load_cache(request):
    cache = msal.SerializableTokenCache()
    if request.session.get('token_cache', False):
        cache.deserialize(request.session['token_cache'])
    return cache


def _save_cache(request, cache):
    if cache.has_state_changed:
        request.session['token_cache'] = cache.serialize()


def _build_msal_app(cache=None, authority=None):
    return msal.ConfidentialClientApplication(
        conf.DJANGO_MSAL_CLIENT_ID, authority=authority or conf.DJANGO_MSAL_AUTHORITY,
        client_credential=conf.DJANGO_MSAL_CLIENT_SECRET, token_cache=cache)


def _build_auth_url(authority=None, scopes=None, state=None, redirect_uri=None):
    # TODO: define authorize url
    return _build_msal_app(authority=authority).get_authorization_request_url(
        scopes or [],
        state=state or str(uuid.uuid4()),
        redirect_uri=redirect_uri or conf.DJANGO_MSAL_ABSOLUTE_REDIRECT_PATH)
