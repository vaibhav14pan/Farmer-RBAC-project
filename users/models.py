from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.core.validators import RegexValidator
from django.conf import settings

class Block(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class User(AbstractUser):  
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('supervisor', 'Supervisor'),
        ('surveyor', 'Surveyor'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    block = models.ForeignKey('Block', on_delete=models.SET_NULL, null=True, blank=True)
    image = models.ImageField(upload_to='user_images/', null=True, blank=True)  # Image Upload Field

    # Custom related names to avoid conflicts
    groups = models.ManyToManyField(Group, related_name="custom_user_groups")
    user_permissions = models.ManyToManyField(Permission, related_name="custom_user_permissions")

    def _str_(self):
        return f"{self.username} - {self.role}"

class Farmer(models.Model):
    aadhar_validator = RegexValidator(
        regex=r'^\d{12}$',  
        message="Aadhar ID must be a 12-digit number."
    )
    
    name = models.CharField(max_length=100)
    aadhar_id = models.CharField(
        max_length=12, 
        unique=True,
        validators=[aadhar_validator] 
    )
    block = models.ForeignKey(Block, on_delete=models.CASCADE)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='farmer_images/', null=True, blank=True)  
    aadhar_image = models.ImageField(upload_to='aadhar_images/', null=True, blank=True)  
    profile_pic = models.ImageField(upload_to='farmer_profiles/', null=True, blank=True)
    aadhar_card = models.FileField(upload_to='aadhar_cards/', null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['aadhar_id'], name='unique_aadhar_id')
        ]