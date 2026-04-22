import io
import uuid
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.base import ContentFile
from job.models import Job
from settings.models import ShortLink, QRModel
import qrcode


class Command(BaseCommand):
    help = "Backfill ShortLink and QRModel for existing Job records"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Recreate short link and QR even if they already exist.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would change without writing.",
        )

    def handle(self, *args, **options):
        force = options["force"]
        dry_run = options["dry_run"]

        created_links = 0
        created_qrs = 0
        updated_links = 0
        updated_job_links = 0

        jobs = Job.objects.all()
        self.stdout.write(self.style.WARNING(f"Processing {jobs.count()} jobs..."))

        for job in jobs:
            # Ensure job_link exists
            desired_job_link = f"{settings.JOB_URL}/jobs/{job.id}"
            if not job.job_link or job.job_link != desired_job_link:
                if dry_run:
                    self.stdout.write(f"Would set job_link for Job[{job.id}] -> {desired_job_link}")
                else:
                    job.job_link = desired_job_link
                    job.save(update_fields=["job_link"])  # avoid triggering full save logic
                updated_job_links += 1

            # ShortLink handling
            existing_short = ShortLink.objects.filter(job=job).first()
            if existing_short and not force:
                pass
            else:
                if dry_run:
                    if existing_short and force:
                        self.stdout.write(f"Would recreate ShortLink for Job[{job.id}] (code={existing_short.code})")
                    else:
                        self.stdout.write(f"Would create ShortLink for Job[{job.id}]")
                else:
                    # Delete existing if force
                    if existing_short and force:
                        existing_short.delete()
                    # Generate unique 6-char code
                    while True:
                        code = uuid.uuid4().hex[:6]
                        if not ShortLink.objects.filter(code=code).exists():
                            break
                    ShortLink.objects.create(code=code, long_url=desired_job_link, job=job)
                    if existing_short and force:
                        updated_links += 1
                    else:
                        created_links += 1

            # QR handling
            existing_qr = QRModel.objects.filter(job=job).first()
            if existing_qr and not force:
                continue

            if dry_run:
                if existing_qr and force:
                    self.stdout.write(f"Would recreate QR for Job[{job.id}]")
                else:
                    self.stdout.write(f"Would create QR for Job[{job.id}]")
            else:
                # Delete existing if force
                if existing_qr and force:
                    existing_qr.delete()

                # Generate QR image in memory
                qr = qrcode.QRCode(box_size=10, border=4)
                qr.add_data(desired_job_link)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")

                buffer = io.BytesIO()
                img.save(buffer, format="PNG")
                buffer.seek(0)

                qr_obj = QRModel.objects.create(url=desired_job_link, job=job)
                qr_obj.qr_image.save(f"qr_{qr_obj.id}.png", ContentFile(buffer.getvalue()), save=True)
                created_qrs += 1

        self.stdout.write(self.style.SUCCESS("Backfill completed."))
        self.stdout.write(
            self.style.SUCCESS(
                f"Updated job_link: {updated_job_links}, ShortLinks created: {created_links}, "
                f"ShortLinks updated: {updated_links}, QRs created: {created_qrs}"
            )
        )
