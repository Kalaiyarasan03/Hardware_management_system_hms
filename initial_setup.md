After running migrations, create users and userprofiles.
Example (in Django shell):

from django.contrib.auth.models import User
from issues.models import UserProfile

u1 = User.objects.create_user('employee1','e1@example.com','password123')
UserProfile.objects.create(user=u1, role='employee')

u2 = User.objects.create_user('hardware1','h1@example.com','password123')
UserProfile.objects.create(user=u2, role='hardware')

u3 = User.objects.create_user('manager1','m1@example.com','password123')
UserProfile.objects.create(user=u3, role='manager')
