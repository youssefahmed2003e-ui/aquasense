from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from cloudinary.models import CloudinaryField

# ==========================================
#              USER PROFILES
# ==========================================

class UserProfile(models.Model):
    """Extends the default User model with additional contact and diver info."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    certification_level = models.CharField(max_length=100, default='Beginner')
    profile_image = CloudinaryField('image', default='https://res.cloudinary.com/dp2ov37tr/image/upload/v1763854352/aquasense/aquasense/default_avatar.png')

    def __str__(self):
        return f"{self.user.username}'s Profile"

# ==========================================
#           COURSE MANAGEMENT
# ==========================================

class Instructor(models.Model):
    """Represents a diving instructor."""
    name = models.CharField(max_length=100)
    bio = models.TextField()
    photo = CloudinaryField('image')
    specialization = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Course(models.Model):
    """Represents a diving course or excursion."""
    DIFFICULTY_CHOICES = [
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
        ('Expert', 'Expert'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.CharField(max_length=50, help_text="e.g., '3 Days', '4 Hours'")
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='Beginner')
    image = CloudinaryField('image')
    instructor = models.ForeignKey(Instructor, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses')
    is_popular = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

# ==========================================
#               BOOKINGS
# ==========================================

class Reservation(models.Model):
    """Tracks user bookings for specific courses."""
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled'),
        ('Completed', 'Completed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservations')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reservations')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    booking_date = models.DateTimeField(auto_now_add=True)
    scheduled_date = models.DateField(null=True, blank=True, help_text="Desired date for the dive")
    notes = models.TextField(blank=True, null=True)

    # Detailed Booking Info
    full_name = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    number_of_divers = models.PositiveIntegerField(default=1)
    certification_level = models.CharField(max_length=100, blank=True, null=True)
    medical_clearance = models.BooleanField(default=False, help_text="User confirmed they have no conflicting medical conditions")

    def __str__(self):
        return f"{self.user.username} - {self.course.title}"
