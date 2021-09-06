"""URLS for SIS"""

from django.urls import include, path
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register('academic_years', views.AcademicYearViewSet)
router.register('students', views.StudentViewSet)
router.register('teachers', views.TeacherViewSet)
router.register('dorms', views.DormViewSet)
router.register('grades', views.GradeViewSet)
router.register('enrollments', views.EnrollmentViewSet)
router.register('courses', views.CourseViewSet)
router.register('sections', views.SectionViewSet)
router.register('student_registrations', views.StudentRegistrationViewSet)
router.register('parents', views.ParentViewSet)
router.register('student_parent_relations', views.StudentParentRelationshipViewSet)

# app_name = 'sis-api'
urlpatterns = [
    path('', include(router.urls)),
]
