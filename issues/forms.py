from django import forms
from .models import Issue, Comment
from django.contrib.auth.models import User

class IssueForm(forms.ModelForm):
    class Meta:
        model = Issue
        fields = ['title', 'description', 'category','subcategory', 'priority', 'attachment', 'store_name', 'floor']
        widgets = {
            'store_name': forms.TextInput(attrs={'placeholder': 'Enter store name'}),
            'floor': forms.TextInput(attrs={'placeholder': 'Enter floor'}),
        }
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            category = self.initial.get('category') or self.data.get('category')
            if category and category.lower() in Issue.SUBCATEGORY_CHOICES:
                self.fields['subcategory'].widget = forms.Select(
                    choices=Issue.SUBCATEGORY_CHOICES[category.lower()]
                )
            else:
                self.fields['subcategory'].widget = forms.Select(choices=[])
class AssignForm(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.filter(is_active=True))

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows':3, 'placeholder':'Add a comment...'})
        }

# Create this file as issues/forms.py (or add to existing forms.py)

from django import forms
from django.contrib.auth.models import User
from .models import UserProfile

class EditUserForm(forms.ModelForm):
    """Form for editing basic user information"""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )
    first_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name'
        })
    )
    last_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name'
        })
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

class UserProfileForm(forms.ModelForm):
    """Form for editing user profile information"""
    
    ROLE_CHOICES = [
        ('', 'Select Role'),
        ('user', 'User'),
        ('manager', 'Manager'),
        ('hardware', 'Hardware Technician'),
        ('admin', 'Administrator'),
    ]
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your phone number'
        })
    )
    
    department = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your department'
        })
    )
    
    bio = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Tell us about yourself...',
            'rows': 4
        })
    )
    
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )

    class Meta:
        model = UserProfile
        fields = ['profile_picture', 'role', 'phone_number', 'department', 'bio']
        
    def clean_profile_picture(self):
        """Validate profile picture"""
        picture = self.cleaned_data.get('profile_picture')
        if picture:
            if picture.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError('Image file too large ( > 5MB )')
            return picture
        return picture