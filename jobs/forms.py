from django import forms
from django.contrib.auth.models import User
from .models import Job, Profile, JOB_TYPE_CHOICES


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = [
            'title', 'company_name', 'description', 'location',
            'salary', 'category', 'job_type', 'experience'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'e.g. Senior Django Developer'}),
            'company_name': forms.TextInput(attrs={'placeholder': 'e.g. Acme Corp'}),
            'location': forms.TextInput(attrs={'placeholder': 'e.g. Mumbai, India or Remote'}),
            'salary': forms.NumberInput(attrs={'placeholder': 'e.g. 80000'}),
            'experience': forms.NumberInput(attrs={'min': 0, 'max': 30}),
            'description': forms.Textarea(attrs={
                'rows': 8,
                'placeholder': 'Describe the role, responsibilities, and requirements…'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


class UserRegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Create a password'}),
        min_length=8,
        help_text="Minimum 8 characters."
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm your password'}),
        label="Confirm Password"
    )
    role = forms.ChoiceField(
        choices=Profile.ROLE_CHOICES,
        widget=forms.RadioSelect,
        initial='job_seeker'
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Choose a username'}),
            'email': forms.EmailInput(attrs={'placeholder': 'your@email.com'}),
        }

    def clean(self):
        cleaned = super().clean()
        pw = cleaned.get('password')
        cpw = cleaned.get('confirm_password')
        if pw and cpw and pw != cpw:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError("Email is required.")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user._profile_role = self.cleaned_data['role']
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['skills', 'education', 'experience', 'bio', 'phone', 'location', 'website', 'resume']
        widgets = {
            'skills': forms.TextInput(attrs={
                'placeholder': 'e.g. Python, Django, React, SQL',
                'class': 'form-control'
            }),
            'bio': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Brief professional summary…',
                'class': 'form-control'
            }),
            'education': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'e.g. B.Sc Computer Science, XYZ University (2018–2022)',
                'class': 'form-control'
            }),
            'experience': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'e.g. Software Developer at ACME Corp (2022–Present)\n— Built REST APIs with Django…',
                'class': 'form-control'
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': '+91 9876543210',
                'class': 'form-control'
            }),
            'location': forms.TextInput(attrs={
                'placeholder': 'e.g. Mumbai, India',
                'class': 'form-control'
            }),
            'website': forms.URLInput(attrs={
                'placeholder': 'https://yourportfolio.com',
                'class': 'form-control'
            }),
        }
