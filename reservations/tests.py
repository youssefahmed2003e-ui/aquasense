from django.test import TestCase
from .models import Course, Instructor

class CourseModelTest(TestCase):
    def setUp(self):
        # Create a dummy instructor
        self.instructor = Instructor.objects.create(
            name="Test Instructor", 
            specialization="Diving",
            bio="Test Bio"
        )
        # Create a dummy course
        self.course = Course.objects.create(
            title="Intro to Diving",
            price=150.00,
            instructor=self.instructor,
            difficulty="Beginner",
            description="Test Description"
        )

    def test_course_creation(self):
        """Test that the course is created with correct attributes"""
        self.assertEqual(self.course.title, "Intro to Diving")
        self.assertEqual(self.course.price, 150.00)
        
    def test_slug_generation(self):
        """Test that the slug is auto-generated from the title"""
        self.course.save()
        self.assertEqual(self.course.slug, "intro-to-diving")