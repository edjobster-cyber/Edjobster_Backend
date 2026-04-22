from django.core.management.base import BaseCommand
from settings.models import Feature

class Command(BaseCommand):
    help = 'Add default features for Job Post and AI Credits'

    def handle(self, *args, **options):
        features = [
            {
                'code': 'JOB_POST',
                'name': 'Job Post',
                'description': 'Feature for creating and managing job posts',
                'iscredit': True,
                'isdayli': False
            },
            {
                'code': 'AI_CREDITS',
                'name': 'AI Credits',
                'description': 'AI usage credits for various features',
                'iscredit': True,
                'isdayli': False
            }
        ]

        created_count = 0
        for feature_data in features:
            feature, created = Feature.objects.get_or_create(
                code=feature_data['code'],
                defaults=feature_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"Created feature: {feature.name}")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"Feature already exists: {feature.name}")
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully processed {len(features)} features. {created_count} new features created.')
        )
