from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.mail import send_mail


class Command(BaseCommand):
    help = "Send a test email using the configured EMAIL_BACKEND/SMTP settings."

    def add_arguments(self, parser):
        parser.add_argument(
            "--to",
            dest="to",
            required=True,
            help="Recipient email address (e.g., user@example.com)",
        )
        parser.add_argument(
            "--subject",
            dest="subject",
            default="Prueba de correo (Django)",
            help="Email subject",
        )
        parser.add_argument(
            "--message",
            dest="message",
            default="Este es un correo de prueba enviado desde Django.",
            help="Email body",
        )
        parser.add_argument(
            "--from-email",
            dest="from_email",
            default=None,
            help="Override FROM email (default: settings.DEFAULT_FROM_EMAIL)",
        )

    def handle(self, *args, **options):
        to_email: str = options["to"]
        subject: str = options["subject"]
        message: str = options["message"]
        from_email: str = options["from_email"] or settings.DEFAULT_FROM_EMAIL

        sent = send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[to_email],
            fail_silently=False,
        )

        self.stdout.write(self.style.SUCCESS(f"Email sent: {sent} (backend={settings.EMAIL_BACKEND})"))
