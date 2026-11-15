import hashlib
import json
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from apps.reports.models import ReportApproval, ReportCard, ReportCardLine, ReportCardVersion, ReportWorkflowEvent
from apps.notifications.services import NotificationService
from apps.audit.services import AuditService

from .models import Mark, MarkRevision


MANAGER_ROLES = frozenset({'admin', 'principal', 'kindergarten_principal', 'primary_principal'})


class MarkService:
    @staticmethod
    @transaction.atomic
    def enter(*, enrollment=None, section_subject=None, value, actor, reason='', mark=None):
        if mark is not None:
            enrollment = enrollment or mark.enrollment
            section_subject = section_subject or mark.section_subject
        if enrollment.class_section_id != section_subject.class_section_id:
            raise ValidationError('Mark enrollment and subject section must match.')
        existing_mark = Mark.objects.select_for_update().filter(enrollment=enrollment, section_subject=section_subject).first()
        before = {'value': existing_mark.value, 'status': existing_mark.status} if existing_mark else None
        mark, created = Mark.objects.get_or_create(
            enrollment=enrollment, section_subject=section_subject,
            defaults={'value': value, 'entered_by': actor},
        )
        if not created:
            if mark.status != Mark.Status.DRAFT:
                raise ValidationError('Only draft marks can be updated.')
            mark.value = value
            mark.entered_by = actor
            mark.save(update_fields=['value', 'entered_by', 'updated_at'])
        next_version = (mark.revisions.aggregate(maximum=Max('version_no'))['maximum'] or 0) + 1
        MarkRevision.objects.create(mark=mark, version_no=next_version, value=value, changed_by=actor, reason=reason)
        AuditService.record(action='mark_created' if created else 'mark_edited', entity_type='mark', entity_id=mark.id, actor=actor, school=enrollment.student.school, before=before, after={'value': mark.value, 'status': mark.status, 'reason': reason})
        return mark

    @staticmethod
    @transaction.atomic
    def submit(*, mark, actor):
        if mark.status != Mark.Status.DRAFT:
            raise ValidationError('Only draft marks can be submitted.')
        mark.status = Mark.Status.SUBMITTED
        mark.save(update_fields=['status', 'updated_at'])
        return mark

    @staticmethod
    @transaction.atomic
    def lock(*, mark, actor):
        if mark.status not in (Mark.Status.SUBMITTED, Mark.Status.DRAFT):
            raise ValidationError('Only draft or submitted marks can be locked.')
        mark.status = Mark.Status.LOCKED
        mark.locked_by = actor
        mark.locked_at = timezone.now()
        mark.finalized_by = actor
        mark.finalized_at = mark.locked_at
        mark.save(update_fields=['status', 'locked_by', 'locked_at', 'finalized_by', 'finalized_at', 'updated_at'])
        AuditService.record(action='mark_unlocked', entity_type='mark', entity_id=mark.id, actor=actor, school=mark.enrollment.student.school, before={'status': Mark.Status.LOCKED}, after={'status': mark.status})
        return mark

    @staticmethod
    @transaction.atomic
    def unlock(*, mark, actor):
        if mark.status != Mark.Status.LOCKED:
            raise ValidationError('Only locked marks can be unlocked.')
        mark.status = Mark.Status.DRAFT
        mark.locked_by = None
        mark.locked_at = None
        mark.finalized_by = None
        mark.finalized_at = None
        mark.save(update_fields=['status', 'locked_by', 'locked_at', 'finalized_by', 'finalized_at', 'updated_at'])
        return mark


class ReportCalculationService:
    @staticmethod
    def grade_for(mark, section_subject):
        rule = section_subject.grading_scheme.rules.filter(min_mark__lte=mark, max_mark__gte=mark).first()
        if not rule:
            raise ValidationError(f'No grading rule covers mark {mark}.')
        return rule.grade_code, rule.distinction

    @staticmethod
    def is_kindergarten(enrollment):
        return enrollment.class_section.grade_level.school_level.code == 'kindergarten'

    @staticmethod
    def calculate(values):
        numeric = [Decimal(value) for value in values]
        total = sum(numeric, Decimal('0'))
        average = (total / len(numeric)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if numeric else None
        return total.quantize(Decimal('0.01')), average


class ReportWorkflowService:
    @staticmethod
    def recalculate_rankings(*, report_period, class_section):
        cards = list(ReportCard.objects.filter(report_period=report_period, enrollment__class_section=class_section, current_version__average__isnull=False).select_related('current_version'))
        for card in cards:
            version = card.current_version
            version.rank = 1 + sum(other.current_version.average > version.average for other in cards if other.id != card.id)
            version.save(update_fields=['rank', 'updated_at'])

    @staticmethod
    def _event(report_card, actor, to_status, version=None, comment=''):
        previous = report_card.status
        ReportWorkflowEvent.objects.create(report_card=report_card, report_version=version, actor=actor, from_status=previous, to_status=to_status, comment=comment)
        report_card.status = to_status
        report_card.save(update_fields=['status', 'updated_at'])

    @staticmethod
    @transaction.atomic
    def build_version(*, enrollment, report_period, actor, teacher_comment='', principal_comment=''):
        report_card, _ = ReportCard.objects.select_for_update().get_or_create(enrollment=enrollment, report_period=report_period)
        next_version = (report_card.versions.aggregate(maximum=Max('version_no'))['maximum'] or 0) + 1
        marks = list(enrollment.marks.select_related('section_subject__subject', 'section_subject__grading_scheme').filter(section_subject__class_section=enrollment.class_section).order_by('section_subject__display_order'))
        if not marks:
            raise ValidationError('At least one mark is required to generate a report version.')
        kindergarten = ReportCalculationService.is_kindergarten(enrollment)
        total, average = ReportCalculationService.calculate([mark.value for mark in marks])
        payload = []
        line_data = []
        distinctions = []
        for mark in marks:
            grade, distinction = ReportCalculationService.grade_for(mark.value, mark.section_subject)
            distinctions.append(distinction)
            line_data.append((mark, grade, distinction))
            payload.append({'subject': str(mark.section_subject.subject_id), 'value': str(mark.value), 'grade': grade})
        content_hash = hashlib.sha256(json.dumps({'report': str(report_card.id), 'version': next_version, 'lines': payload}, sort_keys=True).encode()).hexdigest()
        version = ReportCardVersion.objects.create(
            report_card=report_card, version_no=next_version,
            total=None if kindergarten else total, average=None if kindergarten else average,
            distinction=', '.join(filter(None, sorted(set(distinctions)))), teacher_comment=teacher_comment,
            principal_comment=principal_comment, generated_by=actor, content_hash=content_hash,
        )
        for display_order, (mark, grade, distinction) in enumerate(line_data):
            ReportCardLine.objects.create(report_version=version, subject=mark.section_subject.subject, subject_code=mark.section_subject.subject.code,
                                          subject_name=mark.section_subject.subject.name, numeric_mark=None if kindergarten else mark.value,
                                          grade_code=grade, distinction=distinction, display_order=display_order)
        report_card.current_version = version
        report_card.save(update_fields=['current_version', 'updated_at'])
        if not kindergarten:
            ReportWorkflowService.recalculate_rankings(report_period=report_period, class_section=enrollment.class_section)
        return report_card, version

    @staticmethod
    @transaction.atomic
    def submit(*, report_card, actor):
        if report_card.status not in (ReportCard.Status.DRAFT, ReportCard.Status.REJECTED):
            raise ValidationError('Only draft or rejected reports can be submitted.')
        for mark in report_card.enrollment.marks.filter(section_subject__class_section=report_card.enrollment.class_section, status=Mark.Status.DRAFT):
            MarkService.submit(mark=mark, actor=actor)
            MarkService.lock(mark=mark, actor=actor)
        if not report_card.current_version:
            _, version = ReportWorkflowService.build_version(enrollment=report_card.enrollment, report_period=report_card.report_period, actor=actor)
        else:
            version = report_card.current_version
        ReportWorkflowService._event(report_card, actor, ReportCard.Status.SUBMITTED, version)
        return report_card

    @staticmethod
    @transaction.atomic
    def review(*, report_card, actor, decision, comment=''):
        if actor.role not in MANAGER_ROLES or report_card.status != ReportCard.Status.SUBMITTED:
            raise ValidationError('Only a principal or administrator can review submitted reports.')
        version = report_card.current_version
        ReportApproval.objects.create(report_version=version, approver=actor, decision=decision, comment=comment)
        target = ReportCard.Status.APPROVED if decision == ReportApproval.Decision.APPROVED else ReportCard.Status.REJECTED
        ReportWorkflowService._event(report_card, actor, target, version, comment)
        return report_card

    @staticmethod
    @transaction.atomic
    def publish(*, report_card, actor):
        if actor.role not in MANAGER_ROLES or report_card.status != ReportCard.Status.APPROVED:
            raise ValidationError('Only approved reports can be published by a principal or administrator.')
        version = report_card.current_version
        version.published_at = timezone.now()
        version.save(update_fields=['published_at', 'updated_at'])
        ReportWorkflowService._event(report_card, actor, ReportCard.Status.PUBLISHED, version)
        AuditService.record(action='report_published', entity_type='report_card', entity_id=report_card.id, actor=actor, school=report_card.enrollment.student.school, after={'status': ReportCard.Status.PUBLISHED, 'version': version.version_no})
        NotificationService.report_published(report_card=report_card)
        return report_card

