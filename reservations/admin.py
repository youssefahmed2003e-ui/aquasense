from django.contrib import admin
from .models import Course, Instructor, Reservation, UserProfile

# ==========================================
#           COURSE & INSTRUCTOR
# ==========================================

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'difficulty', 'is_popular', 'created_at')
    list_filter = ('difficulty', 'is_popular')
    search_fields = ('title', 'description')

@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ('name', 'specialization')

# ==========================================
#           BOOKINGS & ACTIONS
# ==========================================

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'status', 'booking_date', 'scheduled_date', 'full_name', 'phone_number', 'number_of_divers')
    list_filter = ('status', 'booking_date')
    actions = ['approve_reservations', 'reject_reservations']

    @admin.action(description='Approve selected reservations')
    def approve_reservations(self, request, queryset):
        queryset.update(status='Confirmed')
        self.message_user(request, "Selected reservations have been approved.")

    @admin.action(description='Reject selected reservations')
    def reject_reservations(self, request, queryset):
        queryset.update(status='Cancelled')
        self.message_user(request, "Selected reservations have been rejected.")

# ==========================================
#              USER PROFILES
# ==========================================

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'certification_level')
