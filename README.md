# Django MSAL

This is a package created to integrate Django applications with Microsoft Azure Active Directory using MSAL.


## Installation


### Requirements

 * [Django 2.2+](https://www.djangoproject.com/)
 * [MSAL Python](https://github.com/AzureAD/microsoft-authentication-library-for-python)
 * [App registered via Azure Portal](https://docs.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app)


### Get the package
You can current install this app using the following:

```
django-msal @ git+https://github.com/dai-ictgeo/django_msal.git

or 

django-msal @ git+https://github.com/dai-ictgeo/django_msal.git@<ref>   # where <ref> is a branch, commmit or tag/version 

```


## Configuration

The django_msal app can be configured for serveral different scenarios:

1. Only allow authorization from a specific MS tenanat
2. Allow authorization from multiple MS tenants
3. Allow authorization from 1 or more tenants and from Django user model
    - Users that do not have MS account can use a Django login
    - Users that do have an MS account must login via MS


### Settings

Add django_msal to installed apps and set the authentication backend.

```
INSTALLED_APPS = [
    ...
	'django_msal',
]

AUTHENTICATION_BACKENDS = (
	'django_msal.auth.MSALAuthBackend',
)

```

**Allow non Microsoft logins**:
If you want to allow for authenticaiton of users that do not have MS accounts, you need to set the following:

```
AUTHENTICATION_BACKENDS = (
	'django_msal.auth.MSALAuthBackend',
    'django.contrib.auth.backends.ModelBackend',
)


DJANGO_MSAL_ALLOW_DJANGO_USERS = True

```

**Manditory Configuration**: 
You will need to override at least the following variables in your settings. You can look at the [conf.py file](conf.py) file for an overview of all configuration options.

```
DJANGO_MSAL_APP_NAME
DJANGO_MSAL_PRIMARY_TENANT_NAME
DJANGO_MSAL_PRIMARY_TENANT_ID
DJANGO_MSAL_CLIENT_ID
DJANGO_MSAL_CLIENT_SECRET
DJANGO_MSAL_REDIRECT_DOMAIN
```


### urls

```
## Add this to the top of your list of project urls
path('', include('django_msal.urls')),

```

Note: django_msal should generally be at the top of your urls list in order to take precedence over urls from other apps. 

```
# django_msal uses the following urls by default
# these can all be configured by overriding settings (see conf.py)
login/
logout/
landing/    # where to go after successful login
authorize/ 
```

**Overriding urls from admin app**:
django_msal overrides the following urls in order to make users login via Microsoft sign in and in order to remove options to reset Django password.

```
# django_msal also overrides some urls from the DJango admin app
# Note: if you have your admin urls somewhere other than admin/, you can change this via a setting DJANGO_MSAL_ADMIN_PATH
admin/login/
admin/logout/
admin/password_change/           # Not overridden if DJANGO_MSAL_ALLOW_DJANGO_USER
admin/password_change/done/      # Not overridden if DJANGO_MSAL_ALLOW_DJANGO_USER 
admin/auth/user/<int>/password/  # Not overridden if DJANGO_MSAL_ALLOW_DJANGO_USER 

```

### migrations and data setup
The django_msal app has two intial migrations along with a management command that can be used to 

```
# Runs the first two migrations that setup the database and create new MicrosoftUsers for current Users
python manage.py migrate
```

```
# Management command that will attempt to link existing users with MS accounts based on email addresses.
python manage.py link_ms_accounts
```




### Overview
django_msal creates a MicrosoftUser that is associated with the normal Django User model via a OneToOneField. It should handle custom user models via the AUTH\_USER\_MODEL setting. A signal is used to create a new MicrosoftUser whenever a Django User is created. A data migration is used to create MicrosoftUsers for any existing Users during initial setup.
