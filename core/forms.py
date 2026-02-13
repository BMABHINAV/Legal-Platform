from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, ProviderProfile


class SignUpForm(UserCreationForm):
    """User registration form"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    phone = forms.CharField(max_length=20, required=False)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-input w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent'


class LoginForm(AuthenticationForm):
    """User login form"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-input w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent'


class ProviderSignUpForm(forms.ModelForm):
    """Provider profile creation form"""
    PROVIDER_TYPE_CHOICES = [
        ('advocate', 'Advocate'),
        ('mediator', 'Mediator'),
        ('arbitrator', 'Arbitrator'),
        ('notary', 'Notary'),
        ('document_writer', 'Document Writer'),
    ]
    
    SPECIALIZATION_CHOICES = [
        ('family', 'Family Law'),
        ('property', 'Property Law'),
        ('criminal', 'Criminal Law'),
        ('civil', 'Civil Law'),
        ('corporate', 'Corporate Law'),
        ('labor', 'Labor Law'),
        ('tax', 'Tax Law'),
        ('consumer', 'Consumer Law'),
    ]
    
    provider_type = forms.ChoiceField(choices=PROVIDER_TYPE_CHOICES)
    bar_registration_number = forms.CharField(max_length=100, required=False)
    years_of_experience = forms.IntegerField(min_value=0)
    specializations = forms.MultipleChoiceField(
        choices=SPECIALIZATION_CHOICES,
        widget=forms.CheckboxSelectMultiple
    )
    languages = forms.CharField(max_length=200, help_text='Comma separated list of languages')
    city = forms.CharField(max_length=100)
    state = forms.CharField(max_length=100)
    bio = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), required=False)
    hourly_rate = forms.IntegerField(min_value=0, required=False)
    
    class Meta:
        model = ProviderProfile
        fields = ('provider_type', 'bar_registration_number', 'years_of_experience', 
                  'specializations', 'languages', 'city', 'state', 'bio', 'hourly_rate')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name != 'specializations':
                field.widget.attrs['class'] = 'form-input w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent'


class DocumentUploadForm(forms.Form):
    """Document upload form for analysis"""
    document = forms.FileField(
        help_text='Upload a PDF, DOCX, or TXT file for analysis'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['document'].widget.attrs['class'] = 'file-input w-full'
        self.fields['document'].widget.attrs['accept'] = '.pdf,.docx,.txt'


class ChatForm(forms.Form):
    """Chat message form"""
    message = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'Ask your legal question...',
            'class': 'form-input w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent',
            'autocomplete': 'off',
        })
    )
