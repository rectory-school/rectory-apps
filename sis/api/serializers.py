"""Serializers for DRF, mainly to sync data"""

from rest_framework import serializers

from sis import models


class AcademicYearSerializer(serializers.HyperlinkedModelSerializer):
    """Serializer for academic years"""

    class Meta:
        model = models.AcademicYear
        fields = ['url', 'year']


class StudentSerializer(serializers.HyperlinkedModelSerializer):
    """Serializer for students"""

    class Meta:
        model = models.Student
        fields = ['url', 'student_id', 'first_name', 'last_name', 'nickname', 'email', 'gender']


class TeacherSerializer(serializers.HyperlinkedModelSerializer):
    """Serializer for teachers"""

    class Meta:
        model = models.Teacher
        fields = ['url', 'teacher_id', 'unique_name', 'first_name', 'last_name', 'prefix', 'email', 'active']


class DormSerializer(serializers.HyperlinkedModelSerializer):
    """Serializer for dorms"""

    class Meta:
        model = models.Dorm
        fields = ['url', 'dorm_name', 'building', 'wing', 'level', 'heads']


class GradeSerializer(serializers.HyperlinkedModelSerializer):
    """Serializer for grades"""

    class Meta:
        model = models.Grade
        fields = ['url', 'grade', 'description', 'school']


class EnrollmentSerializer(serializers.HyperlinkedModelSerializer):
    """Serializer for enrollments"""

    class Meta:
        model = models.Enrollment
        fields = ['url', 'student', 'academic_year', 'boarder', 'dorm', 'grade', 'division',
                  'section', 'advisor', 'status_enrollment', 'status_attending', 'enrolled_date']


class CourseSerializer(serializers.HyperlinkedModelSerializer):
    """Serializer for courses"""

    class Meta:
        model = models.Course
        fields = ['url', 'number', 'course_name', 'course_name_short',
                  'course_name_transcript', 'division', 'grade_level', 'department', 'course_type']


class SectionSerializer(serializers.HyperlinkedModelSerializer):
    """Serializer for sections"""

    class Meta:
        model = models.Section
        fields = ['url', 'course', 'csn', 'academic_year', 'teacher']


class StudentRegistrationSerializer(serializers.HyperlinkedModelSerializer):
    """Serializer for student registrations"""

    class Meta:
        model = models.StudentRegistration
        fields = ['url', 'student_reg_id', 'student', 'section']


class ParentSerializer(serializers.HyperlinkedModelSerializer):
    """Serializer for parents"""

    class Meta:
        model = models.Parent
        fields = ['url', 'family_id', 'parent_id', 'first_name', 'last_name',
                  'email', 'phone_home', 'phone_work', 'phone_cell', 'address', 'updated_at']


class StudentParentRelationshipSerializer(serializers.HyperlinkedModelSerializer):
    """Serializer for student/parent relationships"""

    class Meta:
        model = models.StudentParentRelation
        fields = ['url', 'student', 'parent', 'relationship']
