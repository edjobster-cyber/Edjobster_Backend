from openai import OpenAI
from django.conf import settings
from settings.decorators import handle_career_site_ai_credits
import json
from job.models import Job
from settings.models import CandidateEvaluationCriteria
# from google import genai

client = OpenAI(api_key=settings.OPENAI_API_KEY)

DEFAULT_WEIGHTS = {
    "core_skills": 35,
    "relevant_experience": 30,
    "tools_and_technologies": 15,
    "responsibilities": 10,
    "education_certifications": 10
}

@handle_career_site_ai_credits(usage_codes=["Rjms"])
def generate_rjms(resume: str, assessment_data: str,job_id: int, company:str,sms:float):
    """
    resume: extracted resume text or structured resume JSON (string)
    job_id: Job ID
    sms_score: Screening Match Score (0–100)
    returns: dict (RJMS evaluation)
    """


    job = Job.objects.filter(id=job_id).only("dynamic_job_data").first()
    if not job:
        return {"error": "Job not found"}

    job_data = job.dynamic_job_data
    
    if isinstance(assessment_data, str):
        try:
            assessment_data = json.loads(assessment_data)
        except json.JSONDecodeError:
            return {"error": "Invalid assessment data JSON"}

    if isinstance(job_data, str):
        try:
            job_data = json.loads(job_data)
        except json.JSONDecodeError:
            return {"error": "Invalid job data JSON"}
    
        
    # 1️⃣ Fetch company-defined criteria or fallback
    try:
        criteria = CandidateEvaluationCriteria.objects.get(company=company)
        weights = criteria.prompt or DEFAULT_WEIGHTS
    except CandidateEvaluationCriteria.DoesNotExist:
        weights = DEFAULT_WEIGHTS

    # 2️⃣ Dynamic section JSON template
    section_template = ",\n            ".join(
        f'"{key}": {{ "score": 0, "explanation": [] }}'
        for key in weights.keys()
    )

    # 3️⃣ Weight description block
    weight_block = "\n".join(
        f"- {key.replace('_', ' ').title()}: {weight}%"
        for key, weight in weights.items()
    )

    # 4️⃣ Final Prompt
#     prompt = f"""
# You are an ATS evaluator.

# Evaluate RESUME vs JOB using ONLY the provided data.
# Do not infer or assume missing information.

# ────────────────────────
# SCORING SECTIONS (SYSTEM-DEFINED WEIGHTS)
# {weight_block}

# AI MUST NOT change weights.

# ────────────────────────
# EVALUATION RULES
# - Score each section from 0–100
# - Score ONLY if explicit evidence exists in resume
# - Penalize missing or weak alignment
# - Explanations must be factual, plain English
# - No assumptions, no hallucinations

# ────────────────────────
# SECTION OUTPUT FORMAT
# Each section must return:
# - score: integer (0–100)
# - explanation: 1–2 bullet points
# - Each bullet ≤ 12 words

# ────────────────────────
# CALCULATIONS (MANDATORY)
# - rjms = weighted average of all sections (rounded)
# - variance = | SMS - RJMS |
# - consistency:
#     0–10  → Consistent
#     11–20 → Review Needed
#     ≥21   → High Mismatch

# ────────────────────────
# OUTPUT FORMAT (STRICT JSON ONLY)

# {{
#   "sections": {{
#     {section_template}
#   }},
#   "rjms": 0,
#   "sms": {sms_score},
#   "variance": 0,
#   "consistency": ""
# }}

# ────────────────────────
# Assessment Data:
# {json.dumps(assessment_data, separators=(",", ":"))}

# ────────────────────────
# RESUME CONTENT:
# {resume}

# ────────────────────────
# SCREENING MATCH SCORE (SMS): {sms_score}
# """.strip()

#     prompt = f"""
# You are an ATS Assessment Verifier.

# Your task is to verify whether the CANDIDATE’S ASSESSMENT ANSWERS
# are genuinely supported by the RESUME CONTENT.

# Assessment answers are CLAIMS.
# Resume content is the ONLY VERIFICATION SOURCE.

# Evaluate ONLY based on provided data.
# Do NOT infer, assume, or hallucinate missing information.

# ────────────────────────
# SCORING SECTIONS (SYSTEM-DEFINED WEIGHTS)
# {weight_block}

# AI MUST NOT change weights.

# ────────────────────────
# EVALUATION OBJECTIVE
# - Compare each assessment question and candidate answer with resume evidence
# - Detect exaggeration, weak justification, or mismatch
# - Penalize generic or meaningless open-ended answers
# - Award score ONLY if resume clearly supports the answer

# ────────────────────────
# QUESTION-LEVEL VALIDATION (MANDATORY)
# For EACH assessment question:
# - Analyze the question
# - Analyze the candidate’s answer
# - Check resume for direct evidence
# - No resume proof = low score
# - Filler or random text = severe penalty

# ────────────────────────
# EVALUATION RULES
# - Score each section from 0–100
# - Resume is the ONLY source of truth
# - Claims without resume proof must be penalized
# - Open-ended answers must include:
#     • Role
#     • Product or responsibility
#     • Tools or methods
# - No assumptions, no inferred experience

# ────────────────────────
# SECTION OUTPUT FORMAT
# Each section must return:
# - score: integer (0–100)
# - explanation: 1–2 bullet points
# - Each bullet ≤ 12 words
# - Explanation must mention resume evidence or lack thereof

# ────────────────────────
# CALCULATIONS (MANDATORY)
# - rjms = weighted average of all section scores (rounded)
# - variance = | SMS - RJMS |
# - consistency:
#     0–10  → Consistent
#     11–20 → Review Needed
#     ≥21   → High Mismatch

# ────────────────────────
# OUTPUT FORMAT (STRICT JSON ONLY)

# {{
#   "sections": {{
#     {section_template}
#   }},
#   "rjms": 0,
#   "sms": 0,
#   "variance": 0,
#   "consistency": ""
# }}

# ────────────────────────
# JOB DESCRIPTION:
# {json.dumps(job_data, separators=(",", ":"))}

# ────────────────────────
# ASSESSMENT QUESTIONS & ANSWERS:
# {json.dumps(assessment_data, separators=(",", ":"))}

# ────────────────────────
# RESUME CONTENT:
# {resume}

# ────────────────────────
# SCREENING MATCH SCORE (SMS):   
# """.strip()

    # Choose prompt based on whether assessment data is available
    if assessment_data is None or (isinstance(assessment_data, dict) and not assessment_data):
        # Resume-only evaluation (no assessment)
        prompt = f"""
            You are an ATS Resume Verifier.

            Your task is to evaluate how well the CANDIDATE'S RESUME
            matches the JOB DESCRIPTION.

            Resume content is the ONLY evaluation source.

            Evaluate ONLY based on provided data.
            Do NOT infer, assume, or hallucinate missing information.

            ────────────────────────
            SCORING SECTIONS (SYSTEM-DEFINED WEIGHTS)
            {weight_block}

            AI MUST NOT change weights.

            ────────────────────────
            DEFINITION OF SCORE (STRICT)

            RESUME–JOB DESCRIPTION MATCH SCORE (RJMS)
            - RJMS represents how well the RESUME matches the JOB DESCRIPTION
            - RJMS MUST be derived strictly from resume evidence
            - No external assumptions allowed
            - RJMS reflects VERIFIED capability only

            ────────────────────────
            EVALUATION OBJECTIVE
            - Match resume skills, experience, and tools with job requirements
            - Penalize missing, vague, or unsupported experience
            - Award credit ONLY for explicit, proven experience

            ────────────────────────
            SECTION-LEVEL VALIDATION (MANDATORY)
            For EACH section:
            - Identify required skills from JOB DESCRIPTION
            - Check for direct evidence in RESUME
            - No resume proof = penalty
            - Generic or unclear statements = partial score

            ────────────────────────
            EVALUATION RULES
            - Score each section from 0–100
            - Resume is the ONLY source of truth
            - No assumptions, no inferred experience
            - Strong scoring requires:
                • Clear role
                • Relevant responsibility
                • Tools/technologies used

            ────────────────────────
            SECTION OUTPUT FORMAT
            Each section must return:
            - score: integer (0–100)
            - explanation: 1–2 bullet points
            - Each bullet ≤ 12 words
            - Explanation MUST cite resume evidence or its absence

            ────────────────────────
            CALCULATION (MANDATORY)

            - rjms = weighted average of section scores (rounded)

            ────────────────────────
            OUTPUT FORMAT (STRICT JSON ONLY)

            {{
            "sections": {{
                {section_template}
            }},
            "rjms": 0
            }}

            ────────────────────────
            JOB DESCRIPTION:
            {json.dumps(job_data, separators=(",", ":"))}

            ────────────────────────
            RESUME CONTENT:
            {resume}
        """.strip()
    else:
        # Full evaluation with assessment verification
        prompt = f"""
            You are an ATS Assessment Verifier.

            Your task is to verify whether the CANDIDATE'S ASSESSMENT ANSWERS
            are genuinely supported by the RESUME CONTENT.

            Assessment answers are CLAIMS.
            Resume content is the ONLY VERIFICATION SOURCE.

            Evaluate ONLY based on provided data.
            Do NOT infer, assume, or hallucinate missing information.

            ────────────────────────
            SCORING SECTIONS (SYSTEM-DEFINED WEIGHTS)
            {weight_block}

            AI MUST NOT change weights.

            ────────────────────────
            DEFINITION OF SCORES (STRICT)

            SCREENING MATCH SCORE (SMS)
            - SMS represents performance in the ASSESSMENT ONLY
            - SMS MUST be derived strictly from assessment scoring data
            - Resume content MUST NOT influence SMS
            - Use provided weighted percentage or equivalent assessment score
            - SMS reflects CLAIMED capability, not verified capability

            RESUME–JOB DESCRIPTION MATCH SCORE (RJMS)
            - RJMS represents how well the RESUME matches the JOB DESCRIPTION
            - RJMS MUST be derived strictly from resume evidence
            - Assessment answers MUST NOT influence RJMS
            - RJMS reflects VERIFIED capability

            ────────────────────────
            EVALUATION OBJECTIVE
            - Verify each assessment claim against resume evidence
            - Detect exaggeration, weak justification, or mismatch
            - Penalize generic, filler, or gibberish open-ended answers
            - Award resume credit ONLY if explicitly supported

            ────────────────────────
            QUESTION-LEVEL VALIDATION (MANDATORY)
            For EACH assessment question:
            - Analyze the question intent
            - Analyze the candidate's answer
            - Check resume for direct, explicit evidence
            - No resume proof = severe penalty
            - Random or meaningless text = near-zero score

            ────────────────────────
            EVALUATION RULES
            - Score each section from 0–100
            - Resume is the ONLY source of truth for scoring
            - Claims without resume proof MUST be penalized
            - Open-ended answers MUST include:
                • Role
                • Product or responsibility
                • Tools or methods
            - Missing any element = penalty
            - No assumptions, no inferred experience

            ────────────────────────
            SECTION OUTPUT FORMAT
            Each section must return:
            - score: integer (0–100)
            - explanation: 1–2 bullet points
            - Each bullet ≤ 12 words
            - Explanation MUST cite resume evidence or its absence

            ────────────────────────
            CALCULATIONS (MANDATORY)

            - sms = rounded assessment weighted percentage
            - rjms = weighted average of section scores (rounded)
            - variance = | SMS - RJMS |

            ────────────────────────
            CONSISTENCY CLASSIFICATION
            - 0–10   → Consistent
            - 11–20  → Review Needed
            - ≥21    → High Mismatch

            ────────────────────────
            DECISION INTELLIGENCE (MANDATORY)

            Interpret SMS vs RJMS:

            - High SMS + Low RJMS:
            → Candidate likely overstated skills
            → Validate claims aggressively in interview

            - Low SMS + High RJMS:
            → Candidate likely undervalued
            → Resume stronger than assessment

            - High SMS + High RJMS:
            → Strong alignment
            → Fast-track candidate

            - Low SMS + Low RJMS:
            → Weak alignment
            → Likely reject

            ────────────────────────
            OUTPUT FORMAT (STRICT JSON ONLY)

            {{
            "sections": {{
                {section_template}
            }},
            "rjms": 0,
            "sms": {sms},
            "variance": 0,
            "consistency": ""
            }}

            ────────────────────────
            JOB DESCRIPTION:
            {json.dumps(job_data, separators=(",", ":"))}

            ────────────────────────
            ASSESSMENT QUESTIONS & ANSWERS:
            {json.dumps(assessment_data, separators=(",", ":"))}

            ────────────────────────
            RESUME CONTENT:
            {resume}

            ────────────────────────
            SCREENING MATCH SCORE (SMS): {sms}
        """.strip()



    # print("prompt",prompt)
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "Return valid JSON only. No extra text."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
        )
        print("prompt",prompt)
        print("response",response.choices[0].message.content)
        # API_KEY = "AIzaSyAuIJJFzcq4RYX69G4_XdwFYcVWri-QNMY"
        # # client_gemini = genai.Client(api_key=API_KEY)
        # messages=[
        #         {
        #             "role": "system",
        #             "content": "Return valid JSON only. No extra text."
        #         },
        #         {
        #             "role": "user",
        #             "content": prompt
        #         }
        #     ]
        #     # Convert to Gemini format
        # combined_prompt = "\n\n".join([m["content"] for m in messages])
        # # response_gemini = client_gemini.models.generate_content(
        # #     model="gemini-2.5-flash-lite",
        # #     contents=combined_prompt
        # # )

        usage = response.usage
        input_tokens = usage.prompt_tokens
        output_tokens = usage.completion_tokens

        # 🔹 Cost (update if pricing changes)
        input_cost = (input_tokens / 1_000_000) * 5.00
        output_cost = (output_tokens / 1_000_000) * 15.00

        print(
            f"RJMS tokens → in:{input_tokens} out:{output_tokens} ",
            {'usage': f"RJMS → in:{input_tokens} out:{output_tokens} cost:${input_cost + output_cost:.6f}"},
            # { 'gemini_usage': response_gemini.usage_metadata,'gemini_data': response_gemini.text}
            {'data': response.choices[0].message.content}
            )
        

        content = response.choices[0].message.content
        return json.loads(content)

    except Exception as e:
        return {
            "error": "RJMS generation failed",
            "details": str(e)
        }
