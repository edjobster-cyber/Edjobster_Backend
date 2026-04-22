from django.core.management.base import BaseCommand
from job.models import Job

class Command(BaseCommand):
    help = 'Add job board options to all jobs'

    def handle(self, *args, **options):
        # Get all jobs
        jobs = Job.objects.all()
        # job_boards = ['edjobster', 'talent','adzuna','what_job']
        job_boards = ['adzuna']
        
        updated_count = 0
        
        for job in jobs:
            # If job_boards is None, initialize as empty list
            if job.job_boards is None:
                job.job_boards = []
            
            # Add job boards if they don't exist
            for board in job_boards:
                if board not in job.job_boards:
                    job.job_boards.append(board)
            
            job.save()
            updated_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {updated_count} jobs with job boards: {", ".join(job_boards)}')
        )
