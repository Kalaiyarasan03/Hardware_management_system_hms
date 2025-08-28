from django.contrib import admin
from .models import Issue, UserProfile, Comment

class IssueAdmin(admin.ModelAdmin):
    list_display = ('id','title','status','priority','raised_by','assigned_to','created_at')
    list_filter = ('status','priority')

admin.site.register(Issue, IssueAdmin)
admin.site.register(UserProfile)
admin.site.register(Comment)
