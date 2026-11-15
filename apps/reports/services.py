import base64
import secrets
from io import BytesIO
from pathlib import Path

import qrcode
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import transaction
from django.template.loader import render_to_string

from apps.attendance.models import AttendanceSummary
from apps.files.models import ReportDocument
from apps.qr.models import QRToken
from apps.qr.services import QRVerificationService


class ReportGenerationService:
    @staticmethod
    def _image_uri(field):
        if not field:
            return ''
        try:
            return Path(field.path).resolve().as_uri()
        except (AttributeError, NotImplementedError, OSError):
            return getattr(field, 'url', '')

    @staticmethod
    def _qr_data(version):
        token = QRToken.objects.filter(report_version=version, is_active=True).first()
        if not token:
            raw, token = QRVerificationService.generate_token(report_version=version)
        else:
            raw = token.token_hash
        base_url = getattr(settings, 'PUBLIC_BASE_URL', 'http://localhost:8000').rstrip('/')
        return f'{base_url}/api/qr/verify/?token={raw}'

    @staticmethod
    def _qr_image(data):
        image = qrcode.make(data)
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"

    @staticmethod
    @transaction.atomic
    def generate(*, report_card, version=None, actor=None, save_document=True):
        version = version or report_card.current_version
        if not version or version.report_card_id != report_card.id:
            raise ValidationError('A valid report version is required.')
        enrollment = report_card.enrollment
        school = enrollment.student.school
        attendance = AttendanceSummary.objects.filter(enrollment=enrollment, report_period=report_card.report_period).first()
        context = {
            'report_card': report_card,
            'version': version,
            'student': enrollment.student,
            'enrollment': enrollment,
            'school': school,
            'attendance': attendance,
            'qr_image': ReportGenerationService._qr_image(ReportGenerationService._qr_data(version)) if report_card.status == report_card.Status.PUBLISHED else '',
            'logo_uri': ReportGenerationService._image_uri(school.logo),
            'stamp_uri': ReportGenerationService._image_uri(school.stamp),
            'signature_uri': ReportGenerationService._image_uri(school.principal_signature),
        }
        template = 'reports/kindergarten.html' if enrollment.class_section.grade_level.school_level.code == 'kindergarten' else 'reports/primary.html'
        html = render_to_string(template, context)
        try:
            from weasyprint import HTML
        except OSError as exc:
            raise ValidationError('WeasyPrint system libraries are unavailable. Install Pango, Cairo, and GObject before generating PDFs.') from exc
        pdf = HTML(string=html, base_url=str(Path(settings.BASE_DIR))).write_pdf()
        if save_document:
            checksum = __import__('hashlib').sha256(pdf).hexdigest()
            document = ReportDocument.objects.filter(report_version=version, checksum=checksum).first()
            if not document:
                document = ReportDocument.objects.create(report_version=version, backend=ReportDocument.Backend.LOCAL,
                                                         object_key=f'reports/{version.id}/v{version.version_no}.pdf', checksum=checksum, generated_by=actor)
                document.file.save(f'{version.id}-v{version.version_no}.pdf', ContentFile(pdf), save=True)
        return pdf
