import logging
import msal
import uuid

from django.contrib.auth import get_user_model, login as auth_login
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.base_user import BaseUserManager
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.template.loader import render_to_string

from .models import MicrosoftUser, MicrosoftTenant
from . import conf

User = get_user_model()

logger = logging.getLogger(__name__)

class MSALAuthBackend(ModelBackend):
    def authenticate(self, request, oid=None):
        if not oid:
            return None

        try:
            return MicrosoftUser.objects.get(oid=oid).user
        except MicrosoftUser.DoesNotExist:
            return None


    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


    def login(self, request, user):
        # We have a user that has been authorized by an Microsoft Tenant. Log them in
        auth_login(request, user, backend='django_msal.auth.MSALAuthBackend')


    def validate_request(self, request):
        # Check the state variable that acts as CSRF token
        if request.GET['state'] != request.session['state']:
            logger.warn('CSRF token issue for django_msal login')
            request.session['auth_error'] = {
                'error': 'Authentication Error',
                'message': 'There was a problem authenticating you for this application',
            }
            return False

        if request.GET.get('error', False):
            logger.warn('There was an issue validating request in MSALAuthBackend: %s' % request.GET.get('error'))
            request.session['auth_error'] = {
                'error': request.GET.get('error'),
                'message': 'There was a problem authenticating you for this application',
            }
            return False

        if not request.GET.get('code', False):
            logger.warn('There was an issue validating request in MSALAuthBackend. No code found in request')
            request.session['auth_error'] = {
                'error': 'Authentication Error',
                'message': 'There was a problem authenticating you for this application',
            }
            return False

        return True


    def acquire_token_by_authorization_code(self, request):
        cache = self._load_cache(request)
        token_result =  self._build_msal_app(cache=cache).acquire_token_by_authorization_code(
            request.GET['code'],
            scopes=conf.DJANGO_MSAL_SCOPE,  # Misspelled scope would cause an HTTP 400 error here
            redirect_uri=conf.DJANGO_MSAL_ABSOLUTE_REDIRECT_PATH)
        # We store cache in case we want to make more queries without need to get new token
        self._save_cache(request, cache)
        return token_result


    def validate_token_result(self, request, token_result):
        if 'error' in token_result:
            request.session['auth_error'] = {
                'error': token_result.get('error'),
                'message': 'There was a problem authenticating you for this application'
            }
            return False

        return True


    def validate_token_claims_tenant(self, request, token_claims):
      # Check to make sure user have a valid Tenant ID
        if not token_claims.get('tid', False):
            request.session['auth_error'] = {
                'error': 'Missing Tenant ID',
                'message': 'There was a problem authenticating you for this application'
            }
            return False

        if conf.DJANGO_MSAL_RESTRICT_TENANTS:
            # Only allow tenants that are active in the MicrosoftTenant table
            try:
                MicrosoftTenant.objects.get(tid=token_claims.get('tid'), is_active=True)
            except MicrosoftTenant.DoesNotExist:
                request.session['auth_error'] = {
                    'error': 'Invalid Tenant ID',
                    'message': 'There was a problem authenticating you for this application',
                }
                return False
        # If the tenant is not yet in the system, create it
        tid = token_claims.get('tid')
        try:
            tenant = MicrosoftTenant.objects.get(tid=tid)
        except MicrosoftTenant.DoesNotExist:
            tenant = MicrosoftTenant.objects.create(tid=tid, name=tid)
        return tenant


    def validate_token_claims_user(self, request, token_claims):
        if not token_claims.get('oid', False):
            request.session['auth_error'] = {
                'error': 'Missing Object ID',
                'message': 'There was a problem authenticating you for this application'
            }
            return False
        oid = token_claims.get('oid')
        try:
            microsoftuser = MicrosoftUser.objects.get(oid=oid)
            user = microsoftuser.user
        except MicrosoftUser.DoesNotExist:
            user = self._create_microsoft_user_from_token_claims(token_claims)
            if conf.DJANGO_MSAL_SEND_NEW_ACCOUNT_EMAILS:
                self._send_new_account_emails(user)

        return user


    def _send_new_account_emails(self, user):
        user_email = user.email
        # Email site admins about new user sign-in
        from_email = conf.DJANGO_MSAL_FROM_EMAIL
        ####################################################################
        admin_emails = [a[1] for a in conf.DJANGO_MSAL_ADMINS]
        subject = '%s - New Account Created' % (conf.DJANGO_MSAL_APP_NAME)
        message = render_to_string('django_msal/new_account_created_email.html', {
            'name': user.microsoftuser.name,
            'preferred_username': user.microsoftuser.preferred_username,
            'app_name': conf.DJANGO_MSAL_APP_NAME
        })
        send_mail(subject, "", from_email, admin_emails,
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


    def _create_microsoft_user_from_token_claims(self, token_claims):
        # The user is part of an accepted tenant, but has not yet logged into the application
        # Create a new user
        # We still use the User model set by the Django and therefore need a username and password
        # The preferred_username from Microsoft is not guaranteed to be unique.
        # We need to create a username that is unique to Django User model
        tid = token_claims.get('tid')
        tenant = MicrosoftTenant.objects.get(tid=tid)

        oid = token_claims.get('oid')
        preferred_username = token_claims.get('preferred_username')
        user_email = None
        try:
            validate_email(preferred_username)
            user_email = preferred_username
        except ValidationError:
            user_email = None
        name = token_claims.get('name')
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
        return user


    def build_auth_url(self, authority=None, scopes=None, state=None, redirect_uri=None):
        return self._build_msal_app(authority=authority).get_authorization_request_url(
            scopes or [],
            state=state or str(uuid.uuid4()),
            redirect_uri=redirect_uri or conf.DJANGO_MSAL_ABSOLUTE_REDIRECT_PATH)


    def _load_cache(self, request):
        cache = msal.SerializableTokenCache()
        if request.session.get('token_cache', False):
            cache.deserialize(request.session['token_cache'])
        return cache


    def _save_cache(self, request, cache):
        if cache.has_state_changed:
            request.session['token_cache'] = cache.serialize()


    def _build_msal_app(self, cache=None, authority=None):
        return msal.ConfidentialClientApplication(
            conf.DJANGO_MSAL_CLIENT_ID, authority=authority or conf.DJANGO_MSAL_AUTHORITY,
            client_credential=conf.DJANGO_MSAL_CLIENT_SECRET, token_cache=cache)
