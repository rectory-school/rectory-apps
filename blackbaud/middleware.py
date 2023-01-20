from typing import Optional

from django.utils.functional import SimpleLazyObject

from blackbaud.models import Teacher, Student


class AcademicRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        def get_student() -> Optional[Student]:
            if request.user.is_anonymous:
                return None

            return Student.objects.filter(email=request.user.email).first()

        def get_teacher() -> Optional[Teacher]:
            if request.user.is_anonymous:
                return None

            return Teacher.objects.filter(email=request.user.email).first()

        request.student = SimpleLazyObject(get_student)
        request.teacher = SimpleLazyObject(get_teacher)

        return self.get_response(request)
