from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

try:
    DJANGO_MSAL_CLIENT_ID = settings.DJANGO_MSAL_CLIENT_ID
except AttributeError:
    raise ImproperlyConfigured('DJANGO_MSAL_CLIENT_ID is a required setting')

try:
    DJANGO_MSAL_CLIENT_SECRET = settings.DJANGO_MSAL_CLIENT_SECRET
except AttributeError:
    raise ImproperlyConfigured('DJANGO_MSAL_CLIENT_SECRET is a required setting')

# Can be set to http://localhost:<port> when in development.
# Used to create the absolute redirect and logout paths set below
try:
    DJANGO_MSAL_REDIRECT_DOMAIN = settings.DJANGO_MSAL_REDIRECT_DOMAIN
except AttributeError:
    raise ImproperlyConfigured('DJANGO_MSAL_REDIRECT_DOMAIN is a required setting')

try:
    DJANGO_MSAL_PRIMARY_TENANT_ID = settings.DJANGO_MSAL_PRIMARY_TENANT_ID
except AttributeError:
    raise ImproperlyConfigured('DJANGO_MSAL_PRIMARY_TENANT_ID is a required setting')

try:
    DJANGO_MSAL_PRIMARY_TENANT_NAME = settings.DJANGO_MSAL_PRIMARY_TENANT_NAME
except AttributeError:
    raise ImproperlyConfigured('DJANGO_MSAL_PRIMARY_TENANT_NAME is a required setting')

# For multi-tenant app
# DJANGO_MSAL_AUTHORITY = getattr(settings, 'DJANGO_MSAL_AUTHORITY', 'https://login.microsoftonline.com/common')
# For single tenant app
DJANGO_MSAL_AUTHORITY = "https://login.microsoftonline.com/%s" % (DJANGO_MSAL_PRIMARY_TENANT_ID)

DJANGO_MSAL_GRAPH_ENDPOINT = getattr(settings, 'DJANGO_MSAL_GRAPH_ENDPOINT', 'https://graph.microsoft.com/v1.0/users')

DJANGO_MSAL_LOGIN_PATH = getattr(settings, 'DJANGO_MSAL_LOGIN_PATH', 'login/')
DJANGO_MSAL_LANDING_PATH = getattr(settings, 'DJANGO_MSAL_LANDING_PATH', 'landing/')
DJANGO_MSAL_LOGOUT_PATH = getattr(settings, 'DJANGO_MSAL_LOGOUT_PATH', 'logout/')
DJANGO_MSAL_REDIRECT_PATH = getattr(settings, 'DJANGO_MSAL_REDIRECT_PATH','authorize/')

# Change this if you choose to change the Django admin url
DJANGO_MSAL_ADMIN_PATH = getattr(settings, 'DJANGO_MSAL_ADMIN_PATH','admin/')

# Change this if you choose to use a different redirect_field_name for your login required views
DJANGO_MSAL_REDIRECT_FIELD_NAME = getattr(settings, 'DJANGO_MSAL_REDIRECT_FIELD_NAME', 'next')

# Must match the redirect URI set in the Azure portal
DJANGO_MSAL_ABSOLUTE_REDIRECT_PATH = '%s/%s' % (DJANGO_MSAL_REDIRECT_DOMAIN, DJANGO_MSAL_REDIRECT_PATH)

# Must match the Logout URL set in the Azure portal
DJANGO_MSAL_ABSOLUTE_LOGOUT_PATH = '%s/%s' % (DJANGO_MSAL_REDIRECT_DOMAIN, DJANGO_MSAL_LOGOUT_PATH)

# You can find more Microsoft Graph API endpoints from Graph Explorer
# https://developer.microsoft.com/en-us/graph/graph-explorer
DJANGO_MSAL_ENDPOINT = 'https://graph.microsoft.com/v1.0/users'  # This resource requires no admin consent

# You can find the proper permission names from this document
# https://docs.microsoft.com/en-us/graph/permissions-reference
DJANGO_MSAL_SCOPE = getattr(settings, 'DJANGO_MSAL_SCOPE', [])

# If DJANGO_MSAL_LOGOUT_OF_MS_ACCOUNT is True,
#       a user will be logged out of their MS account when the logout of the Django app
# If DJANGO_MSAL_LOGOUT_OF_MS_ACCOUNT is False,
#       a user will not be logged out of their MS account.
#       this means they will be able to log back into the Django app by hitting the Sign in with Microsoft button
DJANGO_MSAL_LOGOUT_OF_MS_ACCOUNT = getattr(settings, 'DJANGO_MSAL_LOGOUT_OF_MS_ACCOUNT', False)

# If DJANGO_MSAL_RESTRICT_TENANTS is True:
#       the user must login with an account from a Tenant that is active in the MicrosoftTenant table
# If DJANGO_MSAL_RESTRICT_TENANTS is False:
#       the user can login with any Azure Active Directory account
# Note: There is also a setting when registering the application in the Azure portal that
#       determines what tenants are allowed when authenicateing users

DJANGO_MSAL_RESTRICT_TENANTS = getattr(settings, 'DJANGO_MSAL_RESTRICT_TENANTS', True)

# In your Django settings, make sure to set LOGIN_URL to the align with DJANGO_MSAL_LOGIN_PATH
# If going with defaults, this should go in settings.py: LOGIN_URL = '/login/'