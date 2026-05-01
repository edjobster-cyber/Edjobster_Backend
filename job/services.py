from django.conf import settings
from openai import OpenAI
import json
from django.conf import settings
from typing import Dict, List, Optional
import logging
# from google import genai

logger = logging.getLogger(__name__)

# API_KEY = "..." removed for security

def _compute_pricing(model_name: Optional[str], usage_obj) -> Optional[Dict]:
    """
    Compute approximate USD cost from token usage using public model pricing.
    Rates used (per 1,000,000 tokens):
    - gpt-4o-mini: input $0.30, output $1.20, training $3.00
    - gpt-4o:      input $3.75, output $15.00, training $25.00
    - gpt-4.1-mini:input $0.80, output $3.20, training $5.00
    - gpt-4.1:     input $3.00, output $12.00, training $25.00
    """
    try:
        if not usage_obj:
            return None
        prompt_tokens = getattr(usage_obj, 'prompt_tokens', None)
        completion_tokens = getattr(usage_obj, 'completion_tokens', None)
        total_tokens = getattr(usage_obj, 'total_tokens', None)
        if prompt_tokens is None and completion_tokens is None:
            return None

        model_lower = (model_name or '').lower()
        if '4o-mini' in model_lower:
            key = 'gpt-4o-mini'
        elif '4o' in model_lower:
            key = 'gpt-4o'
        elif '4.1 mini' in model_lower or '4-1-mini' in model_lower or '4_1-mini' in model_lower:
            key = 'gpt-4.1-mini'
        elif '4.1' in model_lower or '4-1' in model_lower or '4_1' in model_lower:
            key = 'gpt-4.1'
        else:
            key = 'gpt-4o-mini'

        rates_per_million = {
            'gpt-4o-mini': {'input': 0.30, 'output': 1.20, 'training': 3.00},
            'gpt-4o': {'input': 3.75, 'output': 15.00, 'training': 25.00},
            'gpt-4.1-mini': {'input': 0.80, 'output': 3.20, 'training': 5.00},
            'gpt-4.1': {'input': 3.00, 'output': 12.00, 'training': 25.00},
        }

        model_rates = rates_per_million.get(key, rates_per_million['gpt-4o-mini'])
        pt = float(prompt_tokens or 0)
        ct = float(completion_tokens or 0)

        input_cost = (pt / 1_000_000.0) * model_rates['input']
        output_cost = (ct / 1_000_000.0) * model_rates['output']
        total_cost = input_cost + output_cost

        return {
            'model_key': key,
            'per_million': model_rates,
            'per_thousand': {
                'input': round(model_rates['input'] / 1000.0, 6),
                'output': round(model_rates['output'] / 1000.0, 6),
                'training': round(model_rates['training'] / 1000.0, 6),
            },
            'tokens': {
                'prompt_tokens': int(pt),
                'completion_tokens': int(ct),
                'total_tokens': int(total_tokens or (pt + ct)),
            },
            'cost_usd': {
                'input': round(input_cost, 6),
                'output': round(output_cost, 6),
                'total': round(total_cost, 6),
            }
        }
    except Exception:
        return None

class AIJobDescriptionService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    def generate_job_description(self, job_data: Dict) -> Dict:
        """
        Generate job description, requirements, and benefits using AI
        """
        try:
            # Extract data from input
            job_title = job_data.get('job_title', '')
            exp_min = job_data.get('exp_min', '')
            exp_max = job_data.get('exp_max', '')
            salary_min = job_data.get('salary_min', '')
            salary_max = job_data.get('salary_max', '')
            department = job_data.get('department', '')
            skills = job_data.get('skills', [])
            currency = job_data.get('currency', [])
            educations = job_data.get('educations', [])
            custom_prompt = job_data.get('custom_prompt', '')
            
            # Convert educations and currency to string for prompt
            currency_str = ", ".join(currency) if isinstance(currency, list) else str(currency)
            educations_str = ", ".join(educations) if isinstance(educations, list) else str(educations)

            # Build the AI prompt
            prompt = self._build_prompt(
                job_title, exp_min, exp_max, salary_min, 
                salary_max, department, skills, currency_str, educations_str, custom_prompt
            )

            API_KEY = "AIzaSyAuIJJFzcq4RYX69G4_XdwFYcVWri-QNMY"
            # client_gemini = genai.Client(api_key=API_KEY)

            messages = [
                {
                    "role": "system",
                    "content": "You are an expert HR professional and job description writer. Create comprehensive, professional job descriptions that are engaging and informative."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]

            # Convert to Gemini format
            combined_prompt = "\n\n".join([m["content"] for m in messages])
            # response_gemini = client_gemini.models.generate_content(
            #     model="gemini-2.5-flash-lite",
            #     contents=combined_prompt
            # )

            # print(response_gemini.text)
            
            # Call OpenAI API using new client interface
            response = self.client.chat.completions.create(
                model="gpt-4o-mini-2024-07-18",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert HR professional and job description writer. Create comprehensive, professional job descriptions that are engaging and informative."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            
            # Parse the AI response
            ai_content = response.choices[0].message.content
            parsed_content = self._parse_ai_response(ai_content)
            usage_obj = getattr(response, 'usage', None)
            token_usage = {
                'model': getattr(response, 'model', None),
                'prompt_tokens': getattr(usage_obj, 'prompt_tokens', None) if usage_obj else None,
                'completion_tokens': getattr(usage_obj, 'completion_tokens', None) if usage_obj else None,
                'total_tokens': getattr(usage_obj, 'total_tokens', None) if usage_obj else None
            }
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens

            # 🔹 Cost (update if pricing changes)
            input_cost = (input_tokens / 1_000_000) * 5.00
            output_cost = (output_tokens / 1_000_000) * 15.00

            print(
                f"Job Description → in:{input_tokens} out:{output_tokens} "
                f"cost:${input_cost + output_cost:.6f}"
            )
            
            return {
                'success': True,
                'data': parsed_content,
                # 'data_gemini': response_gemini,
                # 'usage': token_usage,
                'usage': f"Job Description → in:{input_tokens} out:{output_tokens} cost:${input_cost + output_cost:.6f}",
                # 'gemini_data': self._parse_ai_response(response_gemini.text),
                # 'gemini_usage': response_gemini.usage_metadata,
                'pricing': _compute_pricing(getattr(response, 'model', None), usage_obj)
            }
            
        except Exception as e:
            logger.error(f"Error generating job description: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _build_prompt(self, job_title: str, exp_min: str, exp_max: str, 
                     salary_min: str, salary_max: str, department: str, 
                     skills: List[str], currency: str, educations: str, custom_prompt: str) -> str:
        """
        Build the AI prompt based on job details
        """
        
        # Build experience string
        experience_str = ""
        if exp_min and exp_max:
            experience_str = f"{exp_min}-{exp_max} years"
        elif exp_min:
            experience_str = f"{exp_min}+ years"
        elif exp_max:
            experience_str = f"up to {exp_max} years"
        
        # Build salary string
        salary_str = ""
        if salary_min and salary_max:
            salary_str = f"{currency} {salary_min} - {currency} {salary_max}"
        elif salary_min:
            salary_str = f"{currency} {salary_min}+"
        
        # Build skills string
        skills_str = ", ".join(skills) if skills else ""
        
        prompt = f"""
Create a comprehensive job posting for the following position:

Job Title: {job_title}
Department: {department}
Experience Required: {experience_str}
Salary Range: {salary_str}
Currency: {currency}
Education Requirements: {educations}
Required Skills: {skills_str}
Additional Requirements: {custom_prompt}

Please provide the response in the following JSON format:
{{
    "job_description": "Detailed job description with HTML formatting",
    "requirements": "Detailed requirements with HTML formatting", 
    "benefits": "Detailed benefits package with HTML formatting"
}}

Guidelines:
1. Job Description should be engaging, comprehensive, and include:
   - Company overview context
   - Role purpose and impact
   - Key responsibilities (5-7 bullet points)
   - Team collaboration aspects

2. Requirements should include:
   - Education requirements
   - Experience requirements
   - Technical skills
   - Soft skills
   - Any certifications needed

3. Benefits should be attractive and include:
   - Competitive salary package
   - Health and wellness benefits
   - Professional development opportunities
   - Work-life balance perks
   - Career growth opportunities

Use HTML formatting like <ul>, <li>, <p>, <strong>, <br> for better presentation.
"""
        
        return prompt
    
    def _parse_ai_response(self, ai_response: str) -> Dict:
        """
        Parse AI response and extract job description components
        """
        try:
            # Try to extract JSON from the response
            start_index = ai_response.find('{')
            end_index = ai_response.rfind('}') + 1
            
            if start_index != -1 and end_index != -1:
                json_str = ai_response[start_index:end_index]
                parsed_data = json.loads(json_str)
                
                return {
                    'job_description': parsed_data.get('job_description', ''),
                    'requirements': parsed_data.get('requirements', ''),
                    'benefits': parsed_data.get('benefits', '')
                }
            else:
                # Fallback: try to split by sections
                return self._fallback_parse(ai_response)
                
        except json.JSONDecodeError:
            return self._fallback_parse(ai_response)
    
    def _fallback_parse(self, content: str) -> Dict:
        """
        Fallback parsing if JSON parsing fails
        """
        sections = content.split('\n\n')
        
        job_description = ""
        requirements = ""
        benefits = ""
        
        current_section = ""
        
        for section in sections:
            section_lower = section.lower()
            
            if 'job description' in section_lower or 'description' in section_lower:
                current_section = 'description'
                job_description = section
            elif 'requirement' in section_lower:
                current_section = 'requirements'
                requirements = section
            elif 'benefit' in section_lower:
                current_section = 'benefits'
                benefits = section
            elif current_section == 'description':
                job_description += f"\n\n{section}"
            elif current_section == 'requirements':
                requirements += f"\n\n{section}"
            elif current_section == 'benefits':
                benefits += f"\n\n{section}"
        
        return {
            'job_description': job_description or content[:500] + "...",
            'requirements': requirements or "Requirements will be based on the job title and experience level.",
            'benefits': benefits or "Competitive benefits package including health insurance, paid time off, and professional development opportunities."
        }


class AIAssessmentQuestionService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    def generate_assessment_questions(self, job_data: Dict) -> Dict:
        """
        Generate assessment questions based on job details
        """
        try:
            normalized = self._normalize_job_payload(job_data)

            # Extract data from normalized input
            job_title = normalized.get('job_title', '')
            department = normalized.get('department', '')
            exp_min = normalized.get('exp_min', '')
            exp_max = normalized.get('exp_max', '')
            skills = normalized.get('skills', [])
            description = normalized.get('description', '')
            custom_prompt = normalized.get('custom_prompt', '')
            currency = normalized.get('currency', '')
            salary_min = normalized.get('salary_min', '')
            salary_max = normalized.get('salary_max', '')
            
            # Build the AI prompt
            prompt = self._build_assessment_prompt(
                job_title, department, exp_min, exp_max, skills, description, custom_prompt, currency, salary_min, salary_max
            )
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4o-mini-2024-07-18",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert HR professional and assessment designer. Create comprehensive assessment questions that evaluate candidates' skills, experience, and fit for specific job roles. Follow the Candidate Question Scoring Framework."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=3000,
                temperature=0.7
            )
            
            API_KEY = "AIzaSyAuIJJFzcq4RYX69G4_XdwFYcVWri-QNMY"
            # client_gemini = genai.Client(api_key=API_KEY)

            messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert HR professional and assessment designer. Create comprehensive assessment questions that evaluate candidates' skills, experience, and fit for specific job roles. Follow the Candidate Question Scoring Framework."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
            ]

            # Convert to Gemini format
            combined_prompt = "\n\n".join([m["content"] for m in messages])
            # response_gemini = client_gemini.models.generate_content(
            #     model="gemini-2.5-flash-lite",
            #     contents=combined_prompt
            # )

            # Parse the AI response
            ai_content = response.choices[0].message.content
            parsed_content = self._parse_assessment_response(ai_content, job_data)
            usage_obj = getattr(response, 'usage', None)
            token_usage = {
                'model': getattr(response, 'model', None),
                'prompt_tokens': getattr(usage_obj, 'prompt_tokens', None) if usage_obj else None,
                'completion_tokens': getattr(usage_obj, 'completion_tokens', None) if usage_obj else None,
                'total_tokens': getattr(usage_obj, 'total_tokens', None) if usage_obj else None
            }

            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens

            # 🔹 Cost (update if pricing changes)
            input_cost = (input_tokens / 1_000_000) * 5.00
            output_cost = (output_tokens / 1_000_000) * 15.00

            print(
                f"Job Assessment Question → in:{input_tokens} out:{output_tokens} "
                f"cost:${input_cost + output_cost:.6f}"
            )
            
            return {
                'success': True,
                'data': parsed_content,
                # 'gemini_data': self._parse_assessment_response(response_gemini.text, job_data),
                'usage': f"Job Assessment Question → in:{input_tokens} out:{output_tokens} cost:${input_cost + output_cost:.6f}",
                # 'gemini_usage': f"Job Assessment Question → in:{input_tokens} out:{output_tokens} cost:${input_cost + output_cost:.6f}",
                # 'gemini_usage': response_gemini.usage_metadata,
                # 'pricing': _compute_pricing(getattr(response, 'model', None), usage_obj)
            }
            
        except Exception as e:
            logger.error(f"Error generating assessment questions: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _normalize_job_payload(self, job_data: Dict) -> Dict:
        """
        Normalize different incoming payload shapes into a consistent structure for prompts.
        - Flattens description fields that may come as a dict or separate keys
        - Ensures skills is a clean list of strings
        - Coerces numeric-like fields to strings (for prompt readability)
        """
        normalized: Dict = {}

        # Pass-through simple fields
        normalized['job_title'] = str(job_data.get('job_title', '') or '')
        normalized['department'] = str(job_data.get('department', '') or '')
        normalized['custom_prompt'] = str(job_data.get('custom_prompt', '') or '')

        # Experience as strings
        exp_min_val = job_data.get('exp_min', '')
        exp_max_val = job_data.get('exp_max', '')
        normalized['exp_min'] = '' if exp_min_val is None else str(exp_min_val)
        normalized['exp_max'] = '' if exp_max_val is None else str(exp_max_val)

        # Currency as strings
        currency_val = job_data.get('currency', '')
        normalized['currency'] = '' if currency_val is None else str(currency_val)

        # Salary as strings
        salary_min_val = job_data.get('salary_min', '')
        salary_max_val = job_data.get('salary_max', '')
        normalized['salary_min'] = '' if salary_min_val is None else str(salary_min_val)
        normalized['salary_max'] = '' if salary_max_val is None else str(salary_max_val)

        # Skills cleanup: could be list, comma-separated string, or numeric-indexed keys
        skills: List[str] = []
        incoming_skills = job_data.get('skills')
        if isinstance(incoming_skills, list):
            for s in incoming_skills:
                if isinstance(s, str):
                    item = s.strip()
                    if item:
                        skills.append(item)
                elif isinstance(s, dict) and 'name' in s:
                    item = str(s.get('name', '')).strip()
                    if item:
                        skills.append(item)
                else:
                    item = str(s).strip()
                    if item:
                        skills.append(item)
        elif isinstance(incoming_skills, str):
            # Split on commas if provided as string
            parts = [p.strip() for p in incoming_skills.split(',') if p.strip()]
            skills.extend(parts)
        # Also gather any numeric-indexed keys (e.g., {"0": "Skill"}) if present
        if isinstance(job_data, dict):
            numeric_keys = sorted([k for k in job_data.keys() if isinstance(k, str) and k.isdigit()], key=lambda x: int(x))
            for k in numeric_keys:
                val = job_data.get(k)
                if val is not None:
                    item = str(val).strip()
                    if item and item not in skills:
                        skills.append(item)
        normalized['skills'] = skills

        # Description may be a string, a dict with html fields, or separate top-level keys
        description = job_data.get('description')
        # If dict form: {benefits, requirements, job_description}
        if isinstance(description, dict):
            jd_html = description.get('job_description') or ''
            req_html = description.get('requirements') or ''
            ben_html = description.get('benefits') or ''
        else:
            # Top-level fields may exist separately
            jd_html = job_data.get('job_description') or ''
            req_html = job_data.get('requirements') or ''
            ben_html = job_data.get('benefits') or ''
            # If still empty and description is a string, use it
            if not (jd_html or req_html or ben_html) and isinstance(description, str):
                jd_html = description

        # Combine into a single block for better AI context
        combined_desc_parts: List[str] = []
        if jd_html:
            combined_desc_parts.append(f"Job Description:\n{jd_html}")
        if req_html:
            combined_desc_parts.append(f"Requirements:\n{req_html}")
        if ben_html:
            combined_desc_parts.append(f"Benefits:\n{ben_html}")
        normalized['description'] = "\n\n".join(combined_desc_parts).strip()

        return normalized

    def _build_assessment_prompt(self, job_title: str, department: str, exp_min: str,
                               exp_max: str, skills: List[str], description: str,
                               custom_prompt: str, currency: str, salary_min: str, salary_max: str) -> str:
        """
        Build the AI prompt for assessment question generation
        """
        
        # Build experience string
        experience_str = ""
        if exp_min and exp_max:
            experience_str = f"{exp_min}-{exp_max} years"
        elif exp_min:
            experience_str = f"{exp_min}+ years"
        elif exp_max:
            experience_str = f"up to {exp_max} years"
        
        # Build salary string
        salary_str = ""
        if salary_min and salary_max:
            salary_str = f"{currency} {salary_min} - {currency} {salary_max}"
        elif salary_min:
            salary_str = f"{currency} {salary_min}+"
        elif salary_max:
            salary_str = f"up to {currency} {salary_max}"

        # Build skills string
        skills_str = ", ".join(skills) if skills else ""
        
        prompt = f"""
Create comprehensive assessment questions for the following job position:

Job Title: {job_title}
Department: {department}
Experience Required: {experience_str}
Salary Range: {salary_str}
Currency: {currency}
Required Skills: {skills_str}
Job Description: {description}
Additional Requirements: {custom_prompt}

Please generate assessment questions following the Candidate Question Scoring Framework. Create questions in the following JSON format:

{{
    "questions": [
        {{
            "type": "MULTIPLE_CHOICE_SINGLE",
            "question": "Do you have at least 3 years of Java development experience?",
            "options": [
                {{"text": "Yes", "points": 10}},
                {{"text": "No",  "points": 0}}
            ],
            "scoring_config": {{
                
                "type": "must_have",
                "weightage": 10,
                "knockout": true,
                "max_points": 10
            }},
            "scoring_logic": "Yes = 10, No = 0. If No → auto reject",
            "impact_on_match_score": "Knockout question - No answer disqualifies candidate"
        }},
        {{
            "type": "MULTIPLE_CHOICE_SINGLE",
            "question": "Which database have you primarily worked with?",
            "options": [
                {{"text": "MySQL", "points": 10}},
                {{"text": "PostgreSQL", "points": 8}},
                {{"text": "MongoDB", "points": 6}},
                {{"text": "None", "points": 0}}
            ],
            "scoring_config": {{
                "type": "weighted",
                "max_points": 10
            }},
            "scoring_logic": "Candidate's chosen option gets assigned points",
            "impact_on_match_score": "Adds variable score based on recruiter's preference"
        }},
        {{
            "type": "MULTIPLE_CHOICE_MULTI",
            "question": "Which tools have you used for sales analytics?",
            "options": [
                {{"text": "Tableau", "points": 5}},
                {{"text": "Power BI", "points": 5}},
                {{"text": "Excel", "points": 2}},
                {{"text": "Looker", "points": 5}}
            ],
            "scoring_config": {{
                "type": "weighted",
                "max_points": 15
            }},
            "scoring_logic": "Candidate earns points for each matching option, up to max points",
            "impact_on_match_score": "Higher score if candidate possesses multiple desired skills"
        }},
        {{
            "type": "OPEN_ENDED",
            "question": "Describe your experience with cloud platforms in 2-3 sentences.",
            "scoring_config": {{
                "type": "ai_evaluation",
                "weightage": 10,
                "keywords": ["AWS", "Azure", "GCP", "cloud", "deployment", "scalability"]
            }},
            "scoring_logic": "AI evaluates similarity to expected keywords/skills and assigns points",
            "impact_on_match_score": "Adds subjective but AI-normalized score contribution"
        }}
    ]
}}

Guidelines for question generation:

1. **Multiple Choice (Single Select) Questions (including must-have):**
   - Create 2-3 must-have questions for critical requirements
   - Model must-have as Single Select with options [Yes=10, No=0] and knockout=true
   - Examples: Experience level, specific certifications, availability

2. **Multiple Choice (Single Select) Questions:**
   - Create 3-4 questions about preferred technologies/tools
   - Assign different point values based on job relevance
   - Include "None" option with 0 points

3. **Multiple Choice (Multi Select) Questions:**
   - Create 2-3 questions about skills/tools that can have multiple answers
   - Set maximum points to prevent over-scoring
   - Focus on complementary skills

4. **Open-Ended (Short Text) Questions:**
   - Create 2-3 questions for subjective evaluation
   - Define relevant keywords for AI scoring
   - Ask for specific examples or experiences

Total Questions: Generate 8-12 questions covering:
- Technical skills and experience
- Soft skills and communication
- Industry knowledge
- Problem-solving abilities
- Cultural fit indicators

Make questions specific to the job role and industry. Ensure questions are fair, unbiased, and directly relevant to job performance.
"""
        
        return prompt
    
    def _parse_assessment_response(self, ai_response: str, job_data: Dict) -> Dict:
        """
        Parse AI response and extract assessment questions
        """
        try:
            # Try to extract JSON from the response
            start_index = ai_response.find('{')
            end_index = ai_response.rfind('}') + 1
            
            if start_index != -1 and end_index != -1:
                json_str = ai_response[start_index:end_index]
                parsed_data = json.loads(json_str)
                
                # Validate and format the questions
                formatted_questions = self._format_questions(parsed_data.get('questions', []))
                # Enforce scoring rules (8-10 questions, open-ended last, max_points=10, weights sum=100 for non-must-have)
                enforced_questions, weight_meta = self._enforce_scoring_rules(formatted_questions)
                
                assessment_name = f"{job_data.get('job_title', 'Assessment')} - Screening"
                return {
                    'assessment': {
                        'name': assessment_name
                    },
                    'questions': enforced_questions,
                    'total_questions': len(enforced_questions),
                    'question_types': self._get_question_type_summary(enforced_questions),
                    'weightage': weight_meta
                }
            else:
                # Fallback: create sample questions
                return self._create_fallback_questions()
                
        except json.JSONDecodeError:
            return self._create_fallback_questions()
    
    def _format_questions(self, questions: List[Dict]) -> List[Dict]:
        """
        Format and validate questions
        """
        formatted_questions = []
        
        for i, question in enumerate(questions):
            formatted_question = {
                'id': i + 1,
                'type': question.get('type', 'BINARY'),
                'question': question.get('question', ''),
                'scoring_config': question.get('scoring_config', {}),
                'scoring_logic': question.get('scoring_logic', ''),
                'impact_on_match_score': question.get('impact_on_match_score', ''),
                'required': True, 
            }
            
            # Add options for multiple choice questions
            if question.get('type') in ['MULTIPLE_CHOICE_SINGLE', 'MULTIPLE_CHOICE_MULTI']:
                formatted_question['options'] = question.get('options', [])
            
            # Add AI scoring config for open-ended questions
            if question.get('type') == 'OPEN_ENDED':
                formatted_question['ai_scoring'] = question.get('scoring_config', {})
            
            formatted_questions.append(formatted_question)
        
        return formatted_questions
    
    def _get_question_type_summary(self, questions: List[Dict]) -> Dict:
        """
        Get summary of question types
        """
        type_counts = {}
        for question in questions:
            q_type = question.get('type', 'BINARY')
            type_counts[q_type] = type_counts.get(q_type, 0) + 1
        
        return type_counts

    def _enforce_scoring_rules(self, questions: List[Dict]) -> (List[Dict], Dict):
        """
        Enforce product rules:
        - 8-10 questions
        - OPEN_ENDED at the end
        - max_points = 10 for all questions
        - MULTIPLE_CHOICE_MULTI options sum to 10, cap at 10
        - MULTIPLE_CHOICE_SINGLE has at least one option with 10
        - Non-must-have questions' weightage sums to 100
        Returns (questions, meta)
        """
        if not questions:
            return questions, {'sum_weightage': 0, 'non_must_have_count': 0}

        # Ensure OPEN_ENDED last
        questions_sorted = sorted(questions, key=lambda q: 1 if q.get('type') == 'OPEN_ENDED' else 0)

        # Trim to max 10
        if len(questions_sorted) > 10:
            questions_sorted = questions_sorted[:10]

        # Ensure min 8 - if fewer, keep as is

        # Prepare weight calculation (exclude must-have / knockout)
        non_must_indices = []
        base_weights = []

        for idx, q in enumerate(questions_sorted):
            # Always set max points to 10 for downstream clients
            q['max_points'] = 10

            q_type = q.get('type')
            scoring_cfg = q.get('scoring_config', {}) or {}

            # Normalize single-select: ensure at least one option has 10
            if q_type == 'MULTIPLE_CHOICE_SINGLE' and q.get('options'):
                # Find current max
                mx = 0
                mx_idx = 0
                for i, opt in enumerate(q['options']):
                    pts = int(opt.get('points', 0))
                    if pts > mx:
                        mx = pts
                        mx_idx = i
                # Scale if needed
                if mx == 0:
                    q['options'][0]['points'] = 10
                else:
                    factor = 10 / mx
                    for i, opt in enumerate(q['options']):
                        new_pts = round(int(opt.get('points', 0)) * factor)
                        q['options'][i]['points'] = max(0, min(10, new_pts))
                    # Guarantee at least one 10
                    q['options'][mx_idx]['points'] = 10
                scoring_cfg['max_points'] = 10

            # Normalize multi-select: sum of options equals 10, cap 10
            if q_type == 'MULTIPLE_CHOICE_MULTI' and q.get('options'):
                total = sum(int(opt.get('points', 0)) for opt in q['options'])
                if total <= 0:
                    # Evenly spread
                    n = len(q['options'])
                    base = 10 // n
                    rem = 10 - base * n
                    for i in range(n):
                        q['options'][i]['points'] = base + (1 if i < rem else 0)
                elif total != 10:
                    factor = 10 / total
                    new_total = 0
                    for i, opt in enumerate(q['options']):
                        new_pts = int(round(int(opt.get('points', 0)) * factor))
                        q['options'][i]['points'] = new_pts
                        new_total += new_pts
                    # Adjust last to make exact 10
                    if q['options']:
                        diff = 10 - new_total
                        q['options'][-1]['points'] = q['options'][-1]['points'] + diff
                scoring_cfg['max_points'] = 10

            # Collect base weights for non-must-have
            is_must = scoring_cfg.get('knockout') or scoring_cfg.get('type') == 'must_have'
            if not is_must:
                non_must_indices.append(idx)
                # Defer weightage assignment to distribution step
                # Remove any pre-existing weightage to avoid conflicts
                if 'weightage' in scoring_cfg:
                    del scoring_cfg['weightage']
                base_weights.append(10)
            else:
                # Ensure must-have has no weightage
                if 'weightage' in scoring_cfg:
                    del scoring_cfg['weightage']

            q['scoring_config'] = scoring_cfg

        # Distribute weightage to sum 100 across non-must-have
        # Distribute equally across non-must-have to sum to 100%
        count = len(non_must_indices)
        if count > 0:
            base = 100 // count
            rem = 100 % count
            for j, idx in enumerate(non_must_indices):
                q = questions_sorted[idx]
                scoring_cfg = q.get('scoring_config', {})
                # Distribute the remainder as +1 to the first 'rem' items
                pct = base + (1 if j < rem else 0)
                scoring_cfg['weightage'] = int(pct)
                q['scoring_config'] = scoring_cfg

        return questions_sorted, {
            'sum_weightage': 100 if non_must_indices else 0,
            'non_must_have_count': len(non_must_indices)
        }
    
    def _create_fallback_questions(self) -> Dict:
        """
        Create fallback questions if AI parsing fails
        """
        fallback_questions = [
            {
                'id': 1,
                'type': 'MULTIPLE_CHOICE_SINGLE',
                'question': 'Do you have the required experience level for this position?',
                'options': [
                    {'text': 'Yes', 'points': 10},
                    {'text': 'No', 'points': 0}
                ],
                'scoring_config': {
                    'type': 'must_have',
                    'knockout': True,
                    'max_points': 10
                },
                'scoring_logic': 'Yes = 10, No = 0. If No → auto reject',
                'impact_on_match_score': 'Knockout question - No answer disqualifies candidate'
            },
            {
                'id': 2,
                'type': 'MULTIPLE_CHOICE_SINGLE',
                'question': 'What is your primary area of expertise?',
                'options': [
                    {'text': 'Frontend Development', 'points': 8},
                    {'text': 'Backend Development', 'points': 8},
                    {'text': 'Full Stack Development', 'points': 10},
                    {'text': 'Other', 'points': 5}
                ],
                'scoring_config': {
                    'type': 'weighted',
                    'max_points': 10,
                    'weightage': 50
                },
                'scoring_logic': 'Candidate\'s chosen option gets assigned points',
                'impact_on_match_score': 'Adds variable score based on job requirements'
            },
            {
                'id': 3,
                'type': 'OPEN_ENDED',
                'question': 'Describe your most challenging project and how you overcame the difficulties.',
                'scoring_config': {
                    'type': 'ai_evaluation',
                    'weightage': 50,
                    'keywords': ['problem-solving', 'challenge', 'solution', 'teamwork', 'innovation']
                },
                'scoring_logic': 'AI evaluates response quality and relevance',
                'impact_on_match_score': 'Adds subjective but AI-normalized score contribution'
            }
        ]
        
        return {
            'questions': fallback_questions,
            'total_questions': len(fallback_questions),
            'question_types': {
                'BINARY': 1,
                'MULTIPLE_CHOICE_SINGLE': 1,
                'OPEN_ENDED': 1
            }
        } 