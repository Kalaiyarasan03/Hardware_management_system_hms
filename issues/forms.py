from django import forms
from .models import Issue, Comment
from django.contrib.auth.models import User

class IssueForm(forms.ModelForm):
    class Meta:
        model = Issue
        fields = ['title', 'description', 'category', 'priority', 'attachment', 'store_name', 'floor']
        widgets = {
            'store_name': forms.TextInput(attrs={'placeholder': 'Enter store name'}),
            'floor': forms.TextInput(attrs={'placeholder': 'Enter floor'}),
        }
class AssignForm(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.filter(is_active=True))

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows':3, 'placeholder':'Add a comment...'})
        }
