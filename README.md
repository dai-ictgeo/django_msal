# Django MSAL

This is a package created to integrate Django applications with Microsoft Azure Active Directory using MSAL.


## Installation


### Requirements

 * [Django 2.2+](https://www.djangoproject.com/)
 * [MSAL Python](https://github.com/AzureAD/microsoft-authentication-library-for-python)
 * [App registered via Azure Portal](https://docs.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app)


### Get the package
Eventually this app will be put in pypi for easy installation. For now you can clone the repo to someone outside of your project directory and then symnlink it into the project.


##Configuration

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

The configurable settings can be found in the [conf.py file](conf.py). You will need to override at least the following variables in your settings.

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

django_msal overrides the following urls in order to make users login via Microsoft sign in and in order to remove options to reset Django password.

```
# django_msal also overrides the following urls from the DJango admin app
# Note: if you have your admin urls somewhere other than admin/, you can change this via a setting DJANGO_MSAL_ADMIN_PATH
admin/login/
admin/logout/
admin/password_change/
admin/password_change/done/
admin/auth/user/<int>/password/

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