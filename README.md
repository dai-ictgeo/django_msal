## Django MSAL

This is a package created to integrate Django applications with Microsoft Azure Active Directory using MSAL.


### Installation


**Requirements**

 * [Django 2.2+](https://www.djangoproject.com/)
 * [MSAL Python](https://github.com/AzureAD/microsoft-authentication-library-for-python)
 * [App registered via Azure Portal](https://docs.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app)


**Configuration**

The configurable settings can be found in the [conf.py file](conf.py). You will need to override at least three variables in your settings to align with values in the Azure Portal app registration.

```
DJANGO_MSAL_CLIENT_SECRET
DJANGO_MSAL_CLIENT_ID
DJANGO_MSAL_REDIRECT_DOMAIN
```

### Overview
django_msal creates a MicrosoftUser that is associated with the normal Django User model via a OneToOneField. It should handle custom user models via the AUTH\_USER\_MODEL setting. A signal is used to create a new MicrosoftUser whenever a Django User is created. A data migration is used to create MicrosoftUsers for any existing Users during initial setup.
   
