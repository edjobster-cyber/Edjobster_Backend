from django.contrib.sitemaps import Sitemap
from urllib.parse import quote
from .models import Job
from django.conf import settings

class JobSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9

    def items(self):
        return Job.objects.filter(published=True, active=True).order_by('-created')

    def get_urls(self, page=1, site=None, protocol=None):
        urls = []
        for item in self.paginator.page(page).object_list:
            title_slug = quote(str(item.title))  # Ensure title is converted to string
            job_url = f"{settings.JOB_URL}/jobs/{item.id}/"
            urls.append({
                'location': job_url,
                'lastmod': item.updated if item.updated else None,
                'changefreq': self.changefreq,
                'priority': self.priority,
            })
        return urls
