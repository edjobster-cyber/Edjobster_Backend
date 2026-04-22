# utils.py
import re
import urllib.parse

def parse_query(query: str) -> dict:
    if not query or not isinstance(query, str):
        return {
            "education": [],
            "experienceRange": None,
            "jobTitles": [],
            "location": [],
            "skills": []
        }

    query = urllib.parse.unquote_plus(query).strip()

    exp_min = exp_max = None
    range_match = re.search(r'(\d+)\s*[-–]\s*(\d+)', query)
    if range_match:
        exp_min, exp_max = map(int, range_match.groups())
        query = query.replace(range_match.group(0), "")
    else:
        single_match = re.search(r'(\d+)\s*\+?\s*years?', query)
        if single_match:
            exp_min = exp_max = int(single_match.group(1))
            query = query.replace(single_match.group(0), "")

    experience_range = f"{exp_min}-{exp_max}" if exp_min else None

    loc_match = re.search(r'\b(?:in|at|near)\s+([A-Za-z\s]+)', query)
    location = [loc_match.group(1).strip()] if loc_match else []

    title_match = re.match(
        r'^(senior|junior|lead)?\s*[A-Za-z\s]+?(manager|developer|engineer|designer|scientist)',
        query,
        re.I
    )
    job_titles = [title_match.group(0).title()] if title_match else []

    skills = [
        s.strip() for s in re.split(r',|and|\|', query)
        if len(s.strip()) > 1
    ]

    return {
        "education": [],
        "experienceRange": experience_range,
        "jobTitles": job_titles,
        "location": location,
        "skills": skills
    }
