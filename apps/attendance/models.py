from django.db import models

from apps.academics.models import ReportPeriod
from apps.core.models import UUIDTimestampedModel
from apps.students.models import StudentEnrollment


class AttendanceSummary(UUIDTimestampedModel):
    enrollment = models.ForeignKey(StudentEnrollment, on_delete=models.PROTECT, related_name='attendance_summaries')
    report_period = models.ForeignKey(ReportPeriod, on_delete=models.PROTECT, related_name='attendance_summaries')
    present_days = models.PositiveIntegerField(default=0)
    absent_days = models.PositiveIntegerField(default=0)
    late_days = models.PositiveIntegerField(default=0)
    excused_days = models.PositiveIntegerField(default=0)
    total_school_days = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['enrollment', 'report_period']
        constraints = [models.UniqueConstraint(fields=['enrollment', 'report_period'], name='one_attendance_summary_per_period')]
        indexes = [models.Index(fields=['report_period', 'enrollment'])]

    @property
    def attendance_percentage(self):
        if not self.total_school_days:
            return None
        return round((self.present_days / self.total_school_days) * 100, 2)

    def __str__(self):
        return f'{self.enrollment} / {self.report_period} attendance'
