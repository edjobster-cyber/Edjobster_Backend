from django.conf import settings
from openai import OpenAI
import json
from settings.decorators import handle_career_site_ai_credits
# import google.genai as genai

def check_assessment(user_answers, client_assessment, company=None, job_id=None):
    if isinstance(user_answers, str):
        user_answers = json.loads(user_answers)
    if isinstance(client_assessment, str):
        client_assessment = json.loads(client_assessment)

    # Handle both list of attempts and single attempt dict
    if isinstance(user_answers, list):
        if not user_answers:
            return []
        user_payload = user_answers[0]
    else:
        user_payload = user_answers

    user_questions = user_payload.get("data", {}).get("questions", [])
    results = []
    disqualified = False

    for q in user_questions:
        qid = q["id"]
        candidate_answer = q["candidateAnswer"]

        # find client question
        client_q = next((item for item in client_assessment if item["id"] == qid), None)
        if not client_q:
            continue

        q_type = client_q["type"]
        options = client_q.get("options", [])
        max_points = client_q.get("max_points", 10)
        scoring_config = client_q.get("scoring_config", {})
        weightage = scoring_config.get("weightage", 0)
        knockout = scoring_config.get("knockout", False)
        q_type_flag = scoring_config.get("type", "")

        points_earned = 0
        status = "N/A"
        selected_option = None
        selected_options = []

        # MULTIPLE_CHOICE_SINGLE
        if q_type == "MULTIPLE_CHOICE_SINGLE":
            matched = next((opt for opt in options if opt["text"] == candidate_answer), None)
            if matched:
                points_earned = matched.get("points", 0)
                selected_option = {"text": matched.get("text"), "points": points_earned}
                if points_earned == max_points:
                    status = "✅ Correct"
                elif points_earned > 0:
                    status = "⚠️ Partial"
                else:
                    status = "❌ Wrong"

            if (knockout or q_type_flag == "must_have") and points_earned == 0:
                disqualified = True
                status = "🚫 Knockout"

        # MULTIPLE_CHOICE_MULTI
        elif q_type == "MULTIPLE_CHOICE_MULTI":
            total_points = 0
            if isinstance(candidate_answer, list):
                for ans in candidate_answer:
                    matched = next((opt for opt in options if opt["text"] == ans), None)
                    if matched:
                        total_points += matched.get("points", 0)
                        selected_options.append({
                            "text": matched.get("text"),
                            "points": matched.get("points", 0)
                        })
            points_earned = min(total_points, max_points)
            if points_earned == max_points:
                status = "✅ Perfect"
            elif points_earned > 0:
                status = "⚠️ Partial"
            else:
                status = "❌ Wrong"


        # OPEN_ENDED (AI scoring)
        elif q_type == "OPEN_ENDED":
            keywords = (client_q.get("ai_scoring", {}) or client_q.get("scoring_config", {})).get("keywords", [])
            try:
                feedback = ""
                # Use the api_key defined in the module
                # Pass company/job_id to AIScoringService for decorator context
                # Pass company/job_id to AIScoringService for decorator context
                ai_service = AIScoringService(api_key=settings.OPENAI_API_KEY, company=company, job_id=job_id)
                ai_result = ai_service.score_open_ended(
                    question_text=client_q["question"],
                    candidate_answer=candidate_answer,
                    expected_keywords=keywords,
                    max_points=max_points
                )
                points_earned = ai_result["points"]
                feedback = ai_result["feedback"]
                status = "✅ Good" if points_earned >= (max_points * 0.6) else "⚠️ Needs improvement"
            except Exception as e:
                # Fallback to simple logic if AI fails
                points_earned = 8 if any(k in candidate_answer.lower() for k in keywords) else 5
                status = "✅ Good" if points_earned >= (max_points * 0.6) else "⚠️ Needs improvement"
                feedback = "AI scoring failed, used keyword-based fallback."

        # calculate achieved weightage
        achieved_weightage = round((points_earned / max_points) * weightage, 2) if max_points > 0 else 0.0

        results.append({
            "id": qid,
            "type": q_type,
            "question": client_q["question"],
            # include full options list so UI can render choices alongside results
            "options": options,
            "candidate_answer": candidate_answer,
            # echo back the resolved selection(s) with points for clarity/persistence
            "selected_option": selected_option,
            "selected_options": selected_options,
            "points_earned": points_earned,
            "max_points": max_points,
            "weightage": weightage,
            "achieved_weightage": achieved_weightage,
            "status": status,
            # "feedback": feedback
        })

    # summary
    total_points = sum(item.get("points_earned", 0) for item in results)
    total_max_points = sum(item.get("max_points", 0) for item in results)
    total_weightage = sum(item.get("weightage", 0) for item in results)
    total_achieved_weightage = sum(item.get("achieved_weightage", 0) for item in results)

    percentage = round((total_points / total_max_points) * 100, 2) if total_max_points > 0 else 0.0
    weighted_percentage = round((total_achieved_weightage / total_weightage) * 100, 2) if total_weightage > 0 else 0.0

    results.append({
        "status": "SUMMARY",
        "total_points": total_points,
        "total_max_points": total_max_points,
        "percentage": percentage,
        "total_weightage": total_weightage,
        "total_achieved_weightage": total_achieved_weightage,
        "weighted_percentage": weighted_percentage,
        "disqualified": disqualified
    })

    return results

# api_key = "..." removed for security

# from openai import OpenAI
# import json

class AIScoringService:
    """
    A reusable class for AI-powered scoring of open-ended answers.
    Uses OpenAI GPT models to evaluate candidate responses intelligently.
    """

    def __init__(self, api_key=None, model="gpt-4o-mini-2024-07-18", company=None, job_id=None):
        if api_key is None:
            api_key = settings.OPENAI_API_KEY
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.company = company
        self.job_id = job_id

    @handle_career_site_ai_credits(usage_codes=["assessment_check"])
    def score_open_ended(self, question_text, candidate_answer, expected_keywords=None, max_points=10):
        """
        Evaluates an open-ended answer using AI and returns a structured result.
        Returns:
            {
                "points": float,
                "feedback": str
            }
        """
        if expected_keywords is None:
            expected_keywords = []

        # Build rubric: if keywords are provided, use them; otherwise, score by relevance, correctness, completeness
        if expected_keywords:
            prompt = f"""
            You are an expert evaluator scoring job candidate answers.
            Evaluate the following answer objectively against the expected keywords.

            Question: {question_text}
            Candidate's Answer: {candidate_answer}

            Expected key ideas or keywords: {expected_keywords}

            Rules:
            - Score strictly between 0 and {max_points}.
            - 0 = irrelevant or empty.
            - {max_points} = excellent, detailed, and highly relevant, covering most keywords.
            - Provide only JSON output like:
              {{
                "points": <float>,
                "feedback": "<short constructive feedback>"
              }}
            """
        else:
            prompt = f"""
            You are an expert evaluator scoring job candidate answers.
            No keyword rubric is provided. Score based on:
            - Relevance to the question (primary)
            - Factual correctness and clarity
            - Completeness (addresses the main aspects implied by the question)

            Question: {question_text}
            Candidate's Answer: {candidate_answer}

            Rules:
            - Score strictly between 0 and {max_points}.
            - 0 = irrelevant or empty.
            - {max_points} = excellent, fully relevant, correct, and complete.
            - Provide only JSON output like:
              {{
                "points": <float>,
                "feedback": "<short constructive feedback>"
              }}
            """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            # API_KEY = "..." removed for security
            gemini_api_key = settings.GOOGLE_API_KEY
            # client_gemini = genai.Client(api_key=API_KEY)
            # # Convert to Gemini format
            # # combined_prompt = "\n\n".join([m["content"] for m in messages])
            # response_gemini = client_gemini.models.generate_content(
            #     model="gemini-2.5-flash-lite",
            #     contents=prompt
            # )

            try:
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens

                # 🔹 Cost (update if pricing changes)
                # gpt-4o-mini: $0.150 / 1M input, $0.600 / 1M output (approx)
                input_cost = (input_tokens / 1_000_000) * 0.15
                output_cost = (output_tokens / 1_000_000) * 0.60
                

                print(
                    f"Job Assessment check → in:{input_tokens} out:{output_tokens} "
                    f"cost:${input_cost + output_cost:.6f}",
                    # { 'gemini_usage': response_gemini.usage_metadata,'gemini_data': response_gemini.text}
                )
            except Exception as log_e:
                print(f"Logging usage failed: {log_e}")
            
            text = response.choices[0].message.content.strip()
            # Clean up potential markdown formatting if not using json_object mode or if model adds it anyway
            if text.startswith("```json"):
                text = text.replace("```json", "").replace("```", "").strip()
            elif text.startswith("```"):
                text = text.replace("```", "").strip()
                
            result = json.loads(text)
        except Exception as e:
            result = {
                "points": 0,
                "feedback": f"AI scoring failed: {str(e)[:80]}"
            }

        # Normalize points
        try:
            points_val = result.get("points", 0)
            if isinstance(points_val, str):
                # Try to extract number if string
                import re
                match = re.search(r"(\d+(\.\d+)?)", points_val)
                points_val = float(match.group(1)) if match else 0
                
            result["points"] = min(max(float(points_val), 0), max_points)
        except Exception:
            result["points"] = 0

        return result
