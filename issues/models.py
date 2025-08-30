from django.db import models
from django.contrib.auth.models import User

ROLE_CHOICES = [
    ('employee', 'employee'),
    ('hardware', 'hardware'),
    ('manager', 'manager'),
    ('admin', 'admin'),
]

# Update your UserProfile model in models.py with this version
# This version handles the migration issue by providing defaults

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('manager', 'Manager'),
        ('hardware', 'Hardware Technician'),
        ('admin', 'Administrator'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        blank=True,
        null=True,
        help_text='Upload a profile picture (max 5MB)'
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='user',
        blank=True
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        help_text='Your contact phone number'
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        help_text='Your department or team'
    )
    bio = models.TextField(
        blank=True,
        help_text='Tell us about yourself'
    )
    # Use default=timezone.now instead of auto_now_add for existing models
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    @property
    def full_name(self):
        """Return user's full name or username if names not provided"""
        if self.user.first_name and self.user.last_name:
            return f"{self.user.first_name} {self.user.last_name}"
        elif self.user.first_name:
            return self.user.first_name
        else:
            return self.user.username

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

# Auto-create UserProfile when User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()
    else:
        UserProfile.objects.create(user=instance)

class Issue(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('claimed', 'Claimed'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
    ]
    PRIORITY_CHOICES = [
        ('low','Low'),
        ('medium','Medium'),
        ('high','High'),
    ]
    CATEGORY_CHOICES = [
        ('hardware', 'Hardware'),
        ('application', 'Application'),
        ('network', 'Network'),
        ('Middle Ware','Middle Ware'),
        ('others', 'Others'),
    ]
    SUBCATEGORY_CHOICES = {
    'hardware': [
        ('POS', 'POS'),
        ('Printer', 'Printer'),
        ('Computer', 'Computer'),
        ('Server', 'Server'),
        ('Weighing Scale', 'Weighing Scale'),
        ('Kiosk', 'Kiosk'),
    ],
    'network': [
        ('Airtel', 'Airtel'),
        ('BSNL', 'BSNL'),
        ('Vodaphone', 'Vodaphone'),
    ],
    'application': [
        ('SAP', 'SAP'),
        ('Zakya', 'Zakya'),
        ('P2P', 'P2P'),
        ('VMS', 'VMS'),
        ('PetPooja', 'PetPooja'),
    ],
    'middle ware': [
        ('PineLabs', 'PineLabs'),
        ('PayTM', 'PayTM'),
    ],
    'others': [
        ('Others', 'Others'),
    ],
}
    ALL_SUBCATEGORY_CHOICES = []
    for choices in SUBCATEGORY_CHOICES.values():
        ALL_SUBCATEGORY_CHOICES.extend(choices)

    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES, blank=True)
    subcategory = models.CharField(max_length=100, choices=ALL_SUBCATEGORY_CHOICES, blank=True)
    raised_by = models.ForeignKey(User, related_name='raised_issues', on_delete=models.SET_NULL, null=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    claimed = models.BooleanField(default=False)
    attachment = models.FileField(upload_to='attachments/', null=True, blank=True)
    store_name = models.CharField(max_length=100, null=True, blank=True)
    floor = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"#{self.id} {self.title} - {self.status}"

class Comment(models.Model):
    issue = models.ForeignKey(Issue, related_name='comments', on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author} on #{self.issue.id}"
