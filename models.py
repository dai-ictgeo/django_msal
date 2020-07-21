from django.contrib.auth import get_user_model
from django.db import models
from django.dispatch import receiver

User = get_user_model()

class MicrosoftUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    oid = models.CharField("Object ID", max_length=40, blank=True, null=True, unique=True)
    tenant = models.ForeignKey('MicrosoftTenant', blank=True, null=True, on_delete=models.CASCADE)
    preferred_username = models.CharField("Preferred Username", max_length=254, blank=True, null=True)
    name = models.CharField("Name", max_length=40, blank=True, null=True)

    def __str__(self):
        if self.name:
            return self.name
        else:
            return '%s - not linked' % (self.user.username)


@receiver(models.signals.post_save, sender=User)
def create_microsoft_user(sender, instance, created, **kwargs):
    if created:
        MicrosoftUser.objects.create(user=instance)

class MicrosoftTenant(models.Model):
    tid = models.CharField("Tenant ID", max_length=40, unique=True)
    name = models.CharField("Tenant Name", max_length=40)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
