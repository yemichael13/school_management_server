from apps.academics.models import TimetableEntry
from apps.reports.models import ReportCard


class StudentPortalService:
    @staticmethod
    def reports_for(user):
        return ReportCard.objects.filter(
            enrollment__student__user=user,
            status=ReportCard.Status.PUBLISHED,
        ).select_related('report_period', 'enrollment__class_section', 'current_version').prefetch_related('current_version__lines')

    @staticmethod
    def current_enrollment(user):
        return user.student_profile.enrollments.filter(status='active').select_related('class_section').order_by('-started_on').first()

    @staticmethod
    def timetable_for(user):
        enrollment = StudentPortalService.current_enrollment(user)
        if not enrollment:
            return TimetableEntry.objects.none()
        return TimetableEntry.objects.filter(class_section=enrollment.class_section, is_active=True).select_related(
            'section_subject__subject', 'class_section',
        ).prefetch_related('section_subject__teaching_assignments__teacher__user')

    @staticmethod
    def rankings_for(user):
        return StudentPortalService.reports_for(user).values(
            'report_period__id', 'report_period__name', 'current_version__version_no',
            'current_version__rank', 'current_version__average', 'current_version__total',
        )
