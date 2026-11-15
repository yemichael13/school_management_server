from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Case, CharField, Count, DecimalField, F, Q, Value, When

from apps.reports.models import ReportCard


class AnalyticsService:
    @staticmethod
    def published_reports(*, user=None, school=None, academic_year=None, report_period=None, class_section=None, subject=None):
        queryset = ReportCard.objects.filter(
            status=ReportCard.Status.PUBLISHED,
            current_version__published_at__isnull=False,
        )
        if school:
            queryset = queryset.filter(enrollment__class_section__academic_year__school_id=school)
        if academic_year:
            queryset = queryset.filter(enrollment__academic_year_id=academic_year)
        if report_period:
            queryset = queryset.filter(report_period_id=report_period)
        if class_section:
            queryset = queryset.filter(enrollment__class_section_id=class_section)
        if subject:
            queryset = queryset.filter(current_version__lines__subject_id=subject)
        return queryset.select_related(
            'current_version', 'enrollment__student', 'enrollment__class_section', 'report_period',
        ).distinct()

    @staticmethod
    def _percentage(part, whole):
        if not whole:
            return Decimal('0.00')
        return (Decimal(part) * Decimal('100') / Decimal(whole)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @staticmethod
    def pass_fail(*, reports):
        counts = reports.aggregate(
            passed=Count('id', filter=Q(current_version__passed=True)),
            failed=Count('id', filter=Q(current_version__passed=False)),
        )
        evaluated = counts['passed'] + counts['failed']
        return {
            'passed': counts['passed'],
            'failed': counts['failed'],
            'evaluated': evaluated,
            'pass_rate': AnalyticsService._percentage(counts['passed'], evaluated),
            'fail_rate': AnalyticsService._percentage(counts['failed'], evaluated),
        }

    @staticmethod
    def average_distribution(*, reports):
        bucket = Case(
            When(current_version__average__lt=50, then=Value('0-49')),
            When(current_version__average__lt=60, then=Value('50-59')),
            When(current_version__average__lt=70, then=Value('60-69')),
            When(current_version__average__lt=80, then=Value('70-79')),
            When(current_version__average__lt=90, then=Value('80-89')),
            When(current_version__average__gte=90, then=Value('90-100')),
            output_field=CharField(),
        )
        rows = reports.filter(current_version__average__isnull=False).annotate(bucket=bucket).values('bucket').annotate(count=Count('id')).order_by('bucket')
        counts = {row['bucket']: row['count'] for row in rows}
        return [{'range': label, 'count': counts.get(label, 0)} for label in ('0-49', '50-59', '60-69', '70-79', '80-89', '90-100')]

    @staticmethod
    def students(*, reports, limit=10, descending=True):
        reports = reports.filter(current_version__average__isnull=False).order_by(
            '-current_version__average' if descending else 'current_version__average',
            'enrollment__student__last_name', 'enrollment__student__first_name',
        )[:limit]
        return [{
            'name': report.enrollment.student.full_name,
            'average': report.current_version.average,
            'rank': report.current_version.rank,
            'report_period': report.report_period.name,
            'class_name': report.enrollment.class_section.name,
        } for report in reports]

    @staticmethod
    def dashboard(**filters):
        limit = filters.pop('limit', 10)
        reports = AnalyticsService.published_reports(**filters)
        return {
            'pass_fail': AnalyticsService.pass_fail(reports=reports),
            'average_distribution': AnalyticsService.average_distribution(reports=reports),
            'top_students': AnalyticsService.students(reports=reports, limit=limit, descending=True),
            'lowest_students': AnalyticsService.students(reports=reports, limit=limit, descending=False),
        }
