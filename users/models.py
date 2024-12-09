from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()

class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='users_transactions')
    event = models.ForeignKey('chipin.Event', on_delete=models.CASCADE, related_name='transactions')  # Use string reference
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - ${self.amount}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()

def validate_unique_nickname(nickname, instance=None):
    if instance:
        if Profile.objects.filter(nickname=nickname).exclude(pk=instance.pk).exists():
            raise ValidationError(f"Nickname '{nickname}' is already taken.")
    else:
        if Profile.objects.filter(nickname=nickname).exists():
            raise ValidationError(f"Nickname '{nickname}' is already taken.")

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=30)
    surname = models.CharField(max_length=30)
    nickname = models.CharField(max_length=30, unique=True, null=False, blank=False)
    max_spend = models.DecimalField(max_digits=10, decimal_places=2, default=100.00)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=100.00)

    def clean(self):
        validate_unique_nickname(self.nickname, instance=self)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.username