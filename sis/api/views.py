"""DRF API views"""

from rest_framework import viewsets, permissions, authentication, pagination

from sis import models

from . import serializers


class Paginator(pagination.CursorPagination):
    """Cursor based pagination"""

    page_size = 100
    max_page_size = 5000
    page_size_query_param = 'page_size'
    ordering = ['pk']


class Base(viewsets.ModelViewSet):
    """Base model view set"""

    permission_classes = [permissions.DjangoModelPermissions]
    authentication_classes = [authentication.BasicAuthentication]
    pagination_class = Paginator


class AcademicYearViewSet(Base):
    """API endpoint to allow academic years to allow managing academic years"""

    queryset = models.AcademicYear.objects.all()
    serializer_class = serializers.AcademicYearSerializer


class StudentViewSet(Base):
    """API end point to allow managing students"""

    queryset = models.Student.objects.all()
    serializer_class = serializers.StudentSerializer


class TeacherViewSet(Base):
    """API endpoint for teacher management"""

    queryset = models.Teacher.objects.all()
    serializer_class = serializers.TeacherSerializer


class DormViewSet(Base):
    """API endpoint for managing dorms"""

    queryset = models.Dorm.objects.all()
    serializer_class = serializers.DormSerializer


class GradeViewSet(Base):
    """API endpoint for managing grades"""

    queryset = models.Grade.objects.all()
    serializer_class = serializers.GradeSerializer


class EnrollmentViewSet(Base):
    """API endpoint for managing enrollments"""

    queryset = models.Enrollment.objects.all()
    serializer_class = serializers.EnrollmentSerializer


class CourseViewSet(Base):
    """API endpoint for managing courses"""

    queryset = models.Course.objects.all()
    serializer_class = serializers.CourseSerializer


class SectionViewSet(Base):
    """API endpoint for sections"""

    queryset = models.Section.objects.all()
    serializer_class = serializers.SectionSerializer


class StudentRegistrationViewSet(Base):
    """API endpoint for student registrations"""

    queryset = models.StudentRegistration.objects.all()
    serializer_class = serializers.StudentRegistrationSerializer


class ParentViewSet(Base):
    """API endpoint for managing parents"""

    queryset = models.Parent.objects.all()
    serializer_class = serializers.ParentSerializer


class StudentParentRelationshipViewSet(Base):
    """API endpoint for managing student/parent relationships"""

    queryset = models.StudentParentRelation.objects.all()
    serializer_class = serializers.StudentParentRelationshipSerializer
