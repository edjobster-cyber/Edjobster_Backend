from django.core.management.base import BaseCommand
from account.models import Company
from settings.models import CandidateEvaluationCriteria

class Command(BaseCommand):
    help = 'Creates default evaluation criteria for existing companies that do not have one'

    def handle(self, *args, **options):
        # Default prompt configuration
        default_prompt = {
            "core_skills": 35,
            "relevant_experience": 30,
            "tools_and_technologies": 15,
            "responsibilities": 10,
            "education_certifications": 10
        }

        # Get all companies
        companies = Company.objects.all()
        total_companies = companies.count()
        self.stdout.write(f'Found {total_companies} companies to process...')

        created_count = 0
        skipped_count = 0

        for company in companies:
            # Check if the company already has evaluation criteria
            if not CandidateEvaluationCriteria.objects.filter(company=company).exists():
                # Create new evaluation criteria for the company
                CandidateEvaluationCriteria.objects.create(
                    company=company,
                    prompt=default_prompt
                )
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created evaluation criteria for company: {company.name}'))
            else:
                skipped_count += 1
                self.stdout.write(f'Skipped company (already has criteria): {company.name}')

        self.stdout.write(self.style.SUCCESS('\nProcessing complete!'))
        self.stdout.write(f'Total companies processed: {total_companies}')
        self.stdout.write(f'New evaluation criteria created: {created_count}')
        self.stdout.write(f'Companies already having criteria: {skipped_count}')
