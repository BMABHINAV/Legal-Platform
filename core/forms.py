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


class UserProfileEditForm(forms.ModelForm):
    """User profile editing form"""
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone', 'profile_image')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name == 'profile_image':
                field.widget.attrs['class'] = 'file-input file-input-bordered w-full'
            else:
                field.widget.attrs['class'] = 'input input-bordered w-full'


class PasswordChangeForm(forms.Form):
    """Password change form"""
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'input input-bordered w-full'})
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'input input-bordered w-full'}),
        min_length=8
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'input input-bordered w-full'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if new_password and confirm_password and new_password != confirm_password:
            raise forms.ValidationError("Passwords don't match")
        return cleaned_data


class ProviderProfileEditForm(forms.ModelForm):
    """Provider profile editing form"""
    SPECIALIZATION_CHOICES = [
        ('family', 'Family Law'),
        ('property', 'Property Law'),
        ('criminal', 'Criminal Law'),
        ('civil', 'Civil Law'),
        ('corporate', 'Corporate Law'),
        ('labor', 'Labor Law'),
        ('tax', 'Tax Law'),
        ('consumer', 'Consumer Law'),
        ('constitutional', 'Constitutional Law'),
        ('intellectual-property', 'Intellectual Property'),
        ('banking', 'Banking & Finance'),
        ('cyber', 'Cyber Law'),
    ]
    
    specializations = forms.MultipleChoiceField(
        choices=SPECIALIZATION_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    languages_str = forms.CharField(
        max_length=200,
        help_text='Comma separated list of languages',
        required=False
    )
    
    class Meta:
        model = ProviderProfile
        fields = ('provider_type', 'bar_registration_number', 'years_of_experience',
                  'city', 'state', 'bio', 'hourly_rate', 'availability_status')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name != 'specializations':
                field.widget.attrs['class'] = 'input input-bordered w-full'
        
        # Initialize languages_str from instance
        if self.instance and self.instance.languages:
            self.initial['languages_str'] = ', '.join(self.instance.languages)
        
        # Initialize specializations
        if self.instance and self.instance.specializations:
            self.initial['specializations'] = self.instance.specializations


class ServiceListingForm(forms.ModelForm):
    """Service listing form for providers"""
    from .models import ServiceListing
    
    features_str = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'One feature per line'}),
        help_text='Enter features one per line',
        required=False
    )
    
    class Meta:
        from .models import ServiceListing
        model = ServiceListing
        fields = ('title', 'description', 'category', 'price_min', 'price_max', 
                  'duration', 'delivery_time', 'is_active')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name == 'description' or field_name == 'features_str':
                field.widget.attrs['class'] = 'textarea textarea-bordered w-full'
            elif field_name == 'is_active':
                field.widget.attrs['class'] = 'checkbox checkbox-primary'
            else:
                field.widget.attrs['class'] = 'input input-bordered w-full'
        
        # Initialize features_str from instance
        if self.instance and self.instance.features:
            self.initial['features_str'] = '\n'.join(self.instance.features)


class ProviderTimeOffForm(forms.Form):
    """Provider time off request form"""
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'input input-bordered w-full'})
    )
    reason = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'Reason (optional)'})
    )


class AdminVerificationForm(forms.Form):
    """Admin verification form for providers"""
    STATUS_CHOICES = [
        ('verified', 'Approve'),
        ('rejected', 'Reject'),
    ]
    
    status = forms.ChoiceField(choices=STATUS_CHOICES)
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'textarea textarea-bordered w-full'}),
        required=False,
        help_text='Notes for rejection reason (optional)'
    )
