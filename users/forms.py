from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User, Block, Farmer

class LoginForm(AuthenticationForm):
    pass

class UserForm(forms.ModelForm):
    profile_image = forms.ImageField(required=False, label="Upload Profile Picture")  # New Image Field

    class Meta:
        model = User
        fields = ['username', 'password', 'role', 'block', 'profile_image']  # Added profile_image
        widgets = {
            'password': forms.PasswordInput()
        }
class BlockForm(forms.ModelForm):
    class Meta:
        model = Block
        fields = ['name']

class FarmerForm(forms.ModelForm):
    image = forms.ImageField(required=False, label="Upload Farmer Image")  
    aadhar_image = forms.ImageField(required=False, label="Upload Aadhar Image")  # Added Aadhar Image Field  

    class Meta:
        model = Farmer
        fields = ['name', 'aadhar_id', 'block', 'profile_pic', 'aadhar_card']

    def clean_aadhar_id(self):
        aadhar_id = self.cleaned_data.get('aadhar_id')
        
        # Check if this is an update
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            # If this is an update, exclude the current instance from the check
            exists = Farmer.objects.filter(aadhar_id=aadhar_id).exclude(pk=instance.pk).exists()
        else:
            # For new farmers, check if aadhar_id already exists
            exists = Farmer.objects.filter(aadhar_id=aadhar_id).exists()
            
        if exists:
            raise forms.ValidationError("A farmer with this Aadhar ID already exists.")
            
        return aadhar_id

class ProfileForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), required=False, label='New Password')
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'password', 'image', 'role', 'block']
        widgets = {
            'role': forms.TextInput(attrs={'readonly': 'readonly'}),
            'block': forms.TextInput(attrs={'readonly': 'readonly'}),
        }

class DateRangeReportForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))