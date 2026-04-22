# # search_payload.py
# def build_es_payload(keyword):
#     payload = {
#         "query": {
#             "bool": {
#                 "must": [],
#                 "should": [],
#                 "filter": []
#             }
#         }
#     }

#     for title in keyword.get("jobTitles", []):
#         payload["query"]["bool"]["must"].append({
#             "multi_match": {
#                 "query": title,
#                 "fields": [
#                     "headline^3",
#                     "experience.title^3",
#                     "experience.description^2",
#                     "summary^2"
#                 ],
#                 "fuzziness": "AUTO"
#             }
#         })

#     if keyword.get("skills"):
#         payload["query"]["bool"]["must"].append({
#             "multi_match": {
#                 "query": " ".join(keyword["skills"]),
#                 "fields": [
#                     "skills.name^3",
#                     "experience.description^2",
#                     "summary"
#                 ],
#                 "operator": "or"
#             }
#         })

#     if keyword.get("experienceRange"):
#         min_y, max_y = map(int, keyword["experienceRange"].split("-"))
#         payload["query"]["bool"]["filter"].append({
#             "range": {
#                 "total_experience_duration_months": {
#                     "gte": min_y * 12,
#                     "lte": max_y * 12
#                 }
#             }
#         })

#     for loc in keyword.get("location", []):
#         payload["query"]["bool"]["should"].append({
#             "multi_match": {
#                 "query": loc,
#                 "fields": [
#                     "location",
#                     "location_country",
#                     "location_region"
#                 ],
#                 "fuzziness": "AUTO"
#             }
#         })
#         payload["query"]["bool"]["minimum_should_match"] = 1

#     return payload


import re

def normalize_experience_range(exp_range: str):
    """
    Converts:
    '2 - 10 years' → (2, 10)
    '5-8' → (5, 8)
    """
    nums = list(map(int, re.findall(r"\d+", exp_range)))
    if len(nums) >= 2:
        return nums[0], nums[1]
    if len(nums) == 1:
        return nums[0], nums[0]
    return None, None


def build_es_payload(keyword):
    must = []
    filters = []

    # --------------------------------
    # 1️⃣ JOB TITLE (SAFE FIELDS ONLY)
    # --------------------------------
    for title in keyword.get("jobTitles", []):
        must.append({
            "multi_match": {
                "query": title,
                "fields": [
                    "headline^3",
                    "active_experience_title^3",
                    "experience.title^2",
                    "summary"
                ],
                "fuzziness": "AUTO"
            }
        })

    # --------------------------------
    # 2️⃣ SKILLS (SAFE MULTI_MATCH)
    # --------------------------------
    skills = keyword.get("skills", [])
    if skills:
        must.append({
            "multi_match": {
                "query": " ".join(skills),
                "fields": [
                    "skills.name^3",
                    "inferred_skills^3",
                    "historical_skills^2",
                    "experience.description^2",
                    "summary",
                    "headline"
                ],
                "operator": "or"
            }
        })

    # --------------------------------
    # 3️⃣ EXPERIENCE RANGE (FIXED)
    # --------------------------------
    if keyword.get("experienceRange"):
        min_y, max_y = normalize_experience_range(keyword["experienceRange"])
        if min_y is not None:
            filters.append({
                "range": {
                    "total_experience_duration_months": {
                        "gte": min_y * 12,
                        "lte": max_y * 12
                    }
                }
            })

    # --------------------------------
    # FINAL PAYLOAD
    # --------------------------------
    payload = {
        "query": {
            "bool": {
                "must": must,
                "filter": filters
            }
        }
    }

    return payload
