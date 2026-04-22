from .models import *
def search_db(offset, limit):
    qs = CoresignalPreview.objects.filter(is_list=True)
    return [obj.data for obj in qs[offset:offset + limit]]

# services.py
import requests

API_URL = "https://api.coresignal.com/cdapi/v2/employee_multi_source/search/es_dsl/preview"
API_KEY = "ZVDg8OGeOuvBk24DDYJvYfDqMBZTTzhq"

def fetch_from_api(payload, page):
    print(",,,,,,,,,,,,,,,,,,,,,,,,,,,,,")
    headers = {
        "Content-Type": "application/json",
        "apikey": API_KEY
    }
    response = requests.post(
        f"{API_URL}?page={page}",
        headers=headers,
        json=payload,
        timeout=15
    )
    response.raise_for_status()
    return response.json() or []
