import msal
import requests

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django_msal.models import MicrosoftUser, MicrosoftTenant
from django_msal import conf


class Command(BaseCommand):
    help = 'Link Django users with Microsoftusers by calling microsoft graph api'

    def handle(self, *args, **options):
        # Make sure our primary tenant exists
        try:
            tenant = MicrosoftTenant.objects.get(tid=conf.DJANGO_MSAL_PRIMARY_TENANT_ID)
        except MicrosoftTenant.DoesNotExist:
            tenant =MicrosoftTenant.objects.create(
                tid=conf.DJANGO_MSAL_PRIMARY_TENANT_ID,
                name=conf.DJANGO_MSAL_PRIMARY_TENANT_NAME
            )
        authority = 'https://login.microsoftonline.com/%s' % (tenant.tid)
        msal_app = msal.ConfidentialClientApplication(
            conf.DJANGO_MSAL_CLIENT_ID,
            authority=authority,
            client_credential=conf.DJANGO_MSAL_CLIENT_SECRET)

        scope = "https://graph.microsoft.com/.default"
        token_result = msal_app.acquire_token_for_client(scopes=scope)
        if not 'access_token' in token_result:
            raise Exception('Unable to get MSAL app token')

        microsoftusers = MicrosoftUser.objects.filter(oid=None)
        for microsoftuser in microsoftusers:
            user = microsoftuser.user
            email = user.email
            if not email:
                print ('User %s does not have an email address and therefore cannot be linked to an MS account' % (user.username))
            else:
                select = '%s?$select=displayName,userPrincipalName,mail,id' % (email)
                query = '%s/%s' % (conf.DJANGO_MSAL_GRAPH_ENDPOINT, select)
                result = requests.get(
                    query,
                    headers={'Authorization': 'Bearer ' + token_result['access_token']},
                ).json()
                if 'error' in result:
                    print ('Email: %s - Error: %s' % (email, result['error']))
                else:
                    try:
                        microsoftuser.oid = result['id']
                        microsoftuser.preferred_username = result['userPrincipalName']
                        microsoftuser.name = result['displayName']
                        microsoftuser.tenant = tenant
                        microsoftuser.save()
                        print ('Email: %s - Saved new microsoft user' % (email))
                    except Exception as e:
                        print ('Email: %s - Error: %s' % (email, e))
