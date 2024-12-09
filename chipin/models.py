from django.db import models
from django.contrib.auth import get_user_model
from django.apps import apps  # For dynamic import of Transaction model

User = get_user_model()

class Group(models.Model):
    name = models.CharField(max_length=100)
    admin = models.ForeignKey(User, related_name='admin_groups', on_delete=models.CASCADE)
    members = models.ManyToManyField(User, related_name='group_memberships', blank=True)
    invited_users = models.ManyToManyField(User, related_name='pending_invitations', blank=True)

    def __str__(self):
        return self.name

class GroupJoinRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='join_requests')
    is_approved = models.BooleanField(default=False)
    votes = models.ManyToManyField(User, related_name='votes', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Join request by {self.user.username} for {self.group.name}"

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, related_name='comments', on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}: {self.content[:20]}..."

class Event(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Active', 'Active'),
        ('Archived', 'Archived'),
    ]

    name = models.CharField(max_length=100)
    date = models.DateField()
    total_spend = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    group = models.ForeignKey(Group, related_name='events', on_delete=models.CASCADE)
    members = models.ManyToManyField(User, related_name='event_memberships', blank=True)

    def calculate_share(self):
        members_count = self.group.members.count()
        if members_count == 0:
            raise ValueError("Cannot calculate share with no members.")
        return self.total_spend / members_count

    def check_status(self):
        """Check if all members' max spend can cover the event."""
        share = self.calculate_share()
        all_members_can_pay = all(
            hasattr(member, 'profile') and member.profile.max_spend >= share
            for member in self.group.members.all()
        )
        self.status = 'Active' if all_members_can_pay else 'Pending'
        return all_members_can_pay

    def __str__(self):
        return self.name

# Use dynamic import for Transaction to avoid circular imports
def get_transaction_model():
    return apps.get_model('users', 'Transaction')
