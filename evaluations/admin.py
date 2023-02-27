import logging
from typing import Optional
from tempfile import NamedTemporaryFile

from openpyxl import Workbook

from django.contrib import admin, messages
from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext_lazy as _
from django.urls import URLPattern, path
from django.shortcuts import get_object_or_404, redirect

import django.db.utils

from adminsortable2.admin import SortableInlineAdminMixin

from simple_history.models import HistoricalRecords

from . import models

log = logging.getLogger(__name__)


@admin.register(models.QuestionSet)
class QuestionSetAdmin(admin.ModelAdmin):
    """Admin for a question set"""

    search_fields = ["name"]


@admin.register(models.FreeformQuestion)
class FreeformQuestionAdmin(admin.ModelAdmin):
    """Admin for a freeform question"""

    list_display = ["__str__", "question_set"]
    autocomplete_fields = ["question_set"]
    list_filter = ["question_set"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("question_set")


class MultipleChoiceAnswerInline(admin.TabularInline):
    """Inline for a multiple choice question"""

    model = models.MultipleChoiceAnswer
    extra = 0


@admin.register(models.MultipleChoiceQuestion)
class MultipleChoiceQuestionAdmin(admin.ModelAdmin):
    """Admin for a multiple choice question"""

    list_display = ["__str__", "question_set"]
    autocomplete_fields = ["question_set"]
    list_filter = ["question_set"]
    inlines = (MultipleChoiceAnswerInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("question_set")


class TagInline(admin.TabularInline):
    """Inline for tags in categories"""

    model = models.Tag
    extra = 0


@admin.register(models.TagCategory)
class TagCategoryAdmin(admin.ModelAdmin):
    """Admin for a tag category"""

    inlines = [TagInline]
    readonly_fields = ["system_managed"]
    list_display = [
        "__str__",
        "system_managed",
        "admin_filter_display_values",
        "admin_filter_breakout_values",
    ]

    def has_change_permission(
        self, request, obj: Optional[models.TagCategory] = None
    ) -> bool:
        if obj and obj.system_managed:
            return False

        return super().has_change_permission(request, obj)

    def has_delete_permission(
        self, request, obj: Optional[models.TagCategory] = None
    ) -> bool:
        if obj and obj.system_managed:
            return False

        return super().has_change_permission(request, obj)


@admin.register(models.Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ["category__name", "name"]
    list_display = ["__str__", "category", "created_at"]
    list_filter = ["category"]

    def has_add_permission(self, *args, **kwargs) -> bool:
        return False

    def has_change_permission(self, *args, **kwargs) -> bool:
        return False

    def has_delete_permission(self, *args, **kwargs) -> bool:
        return False


def get_tag_category_filter(category: models.TagCategory) -> admin.SimpleListFilter:
    """Get the filter for a tag category"""

    class Inner(admin.SimpleListFilter):
        title = category.name
        parameter_name = f"tag_category_{category.pk}"

        def lookups(self, request, model_admin):
            out = [
                ("exists", _("Has tag")),
                ("missing", _("Does not have tag")),
            ]

            if category.admin_filter_display_values:
                for tag in category.tags.all():
                    out.append((str(tag.pk), tag.value))

            return out

        def queryset(self, request, queryset):
            if self.value() == "exists":
                return queryset.filter(tags__category=category).distinct()

            if self.value() == "missing":
                return queryset.exclude(tags__category=category).distinct()

            if self.value():
                return queryset.filter(tags__pk=self.value())

            return queryset

    return Inner  # type: ignore


def get_tag_filter(tag: models.Tag) -> admin.SimpleListFilter:
    """Get a yes/no value for a given tag"""

    class Inner(admin.SimpleListFilter):
        title = f"{tag.category.name}: {tag.value}"
        parameter_name = f"tag_{tag.pk}"

        def lookups(self, request, model_admin):
            return (
                ("yes", _("Has tag")),
                ("no", _("Does not have tag")),
            )

        def queryset(self, request, queryset):
            if self.value() == "yes":
                return queryset.filter(tags=tag)

            if self.value() == "no":
                return queryset.exclude(tags=tag)

            return queryset

    return Inner  # type: ignore


def get_tags_for_category(category: models.TagCategory) -> list[admin.SimpleListFilter]:
    """Get a bunch of admin filters for tags"""

    out = [
        get_tag_category_filter(category),
    ]

    if category.admin_filter_breakout_values:
        for tag in category.tags.all():  # type: ignore
            out.append(get_tag_filter(tag))

    return out


def get_all_tags() -> list[admin.SimpleListFilter]:
    out = []

    try:
        for category in models.TagCategory.objects.all():
            out.extend(get_tags_for_category(category))
    except (django.db.utils.OperationalError, django.db.utils.ProgrammingError):
        log.exception("Could not generate admin tags")
        return []

    return out


@admin.register(models.Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    """Admin for individual evaluations"""

    autocomplete_fields = ["tags", "student", "question_set"]
    search_fields = ["student__given_name", "student__family_name"]
    list_display = ["__str__", "student", "completed_at"]

    list_filter = (
        "question_set",
        "created_at",
        "completed_at",
        *get_all_tags(),  # type: ignore
    )

    actions = [
        "clear_answers",
        "send_reminder_emails",
        "generate_results_report",
        "generate_status_report",
    ]

    history = HistoricalRecords()

    def get_list_filter(self, request: HttpRequest):
        base_filters = super().get_list_filter(request)

        return base_filters

    @admin.action(description="Clear answers")
    def clear_answers(self, request, objs):
        models.EvaluationMultipleChoiceAnswer.objects.filter(
            evaluation__in=objs
        ).delete()
        models.EvaluationFreeformAnswer.objects.filter(evaluation__in=objs).delete()
        objs.update(completed_at=None)

    @admin.action(description="Send reminder emails")
    def send_reminder_emails(self, request, objs):
        """Send a reminder email to the students with incomplete evaluations"""

        # TODO: Implement

    @admin.action(description="Generate results")
    def generate_results_report(self, request, objs):
        """Generate the reports for this evaluation set"""

        # TODO: Implement

    @admin.action(description="Generate status report")
    def generate_status_report(self, request, objs):
        """Generate the status reports for this evaluation set"""

        total = objs.count()
        complete = objs.filter(completed_at__isnull=False).count()
        incomplete = objs.filter(completed_at__isnull=True).count()

        complete_percent = complete / total * 100
        incomplete_percent = incomplete / total * 100

        lines = [
            f"Total evaluations: {total}",
            f"Complete evaluations: {complete} ({complete_percent:.0f}%)",
            f"Incomplete evaluations: {incomplete} ({incomplete_percent:.0f}%)",
        ]

        out = "\n".join(lines)

        resp = HttpResponse(content=out)
        resp["content-type"] = "text/plain"
        return resp


class ReportCategorizerCategoryInline(SortableInlineAdminMixin, admin.TabularInline):
    model = models.ReportCategorizerTagCategory
    extra = 0


@admin.register(models.ReportCategorizer)
class ReportCategorizerAdmin(admin.ModelAdmin):
    """Admin for report categorizer"""

    inlines = [ReportCategorizerCategoryInline]


class UploadConfigurationTagInline(admin.TabularInline):
    model = models.UploadConfigurationTagCategory
    extra = 0


@admin.register(models.UploadConfiguration)
class UploadConfigurationAdmin(admin.ModelAdmin):
    inlines = [UploadConfigurationTagInline]

    def get_urls(self) -> list[URLPattern]:
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:pk>/download",
                self.download_template,
                name="evaluations_uploadconfiguration_download_template",
            ),
            path(
                "<int:pk>/upload",
                self.upload_template,
                name="evaluations_uploadconfiguration_upload_template",
            ),
        ]

        return urls + custom_urls

    def upload_template(self, request: HttpRequest, pk: int) -> HttpResponse:
        messages.success(request, "Upload successful")

        return redirect("admin:evaluations_uploadconfiguration_change", pk)

    def download_template(self, request: HttpRequest, pk: int) -> HttpResponse:
        """Generate and download the template for uploading"""

        obj = get_object_or_404(models.UploadConfiguration, pk=pk)

        wb = Workbook()
        ws = wb.active
        ws.title = "Template"

        headers = ["Evaluation Identifier", "Student Email", "Evaluation Title"]

        for tag_category in obj.tag_categories.order_by("category__name"):
            headers.append(tag_category.category.name)

        for i, header in enumerate(headers):
            ws.cell(row=1, column=i + 1, value=header)

        with NamedTemporaryFile() as tmp:
            wb.save(tmp.name)
            tmp.seek(0)
            stream = tmp.read()

        resp = HttpResponse(
            stream,
            headers={
                "Content-Type": (
                    "application/vnd."
                    "openxmlformats-officedocument."
                    "spreadsheetml."
                    "sheet"
                ),
                "Content-Disposition": f"attachment; filename={obj.name}.xlsx",
            },
        )

        return resp
