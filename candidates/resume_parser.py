import json
import logging
from typing import Dict, Any, Optional
from openai import OpenAI
from django.conf import settings

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = None
if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
else:
    logger.warning('OpenAI API key not configured. Resume parsing with AI will not work.')

def extract_text_from_file(file_content: bytes, file_name: str) -> str:
    """Extract text from different file types."""
    file_name = file_name.lower()
    
    if file_name.endswith('.pdf'):
        try:
            import PyPDF2
            from io import BytesIO
            pdf_reader = PyPDF2.PdfReader(BytesIO(file_content))
            return "\n".join(page.extract_text() for page in pdf_reader.pages)
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            return ""
    
    elif file_name.endswith(('.docx', '.doc')):
        try:
            import docx2txt
            from io import BytesIO
            return docx2txt.process(BytesIO(file_content))
        except Exception as e:
            logger.error(f"Error extracting text from DOCX: {str(e)}")
            return ""
    
    try:
        return file_content.decode('utf-8')
    except UnicodeDecodeError:
        try:
            return file_content.decode('latin-1')
        except Exception as e:
            logger.error(f"Error decoding file content: {str(e)}")
            return ""

def parse_resume(resume_file) -> Optional[Dict[str, Any]]:
    """
    Parse a resume file and return extracted data.
    
    Args:
        resume_file: File-like object with read() method or bytes
        
    Returns:
        dict: Parsed resume data or None if parsing fails
    """
    if client is None:
        logger.warning("OpenAI client not initialized")
        return None

    try:
        # Read file content if it's a file-like object
        if hasattr(resume_file, 'read'):
            file_content = resume_file.read()
            file_name = getattr(resume_file, 'name', 'resume')
        else:
            file_content = resume_file
            file_name = 'resume'

        # Extract text from file
        text_content = extract_text_from_file(file_content, file_name)
        if not text_content:
            logger.warning("Could not extract text from resume")
            return None

        # Load JSON template
        try:
            with open('resume_json_format.json') as f:
                template = json.load(f)
        except Exception as e:
            logger.error(f"Error loading template: {str(e)}")
            template = {}

        # Prepare prompt
        prompt = f"""
        Extract the following information from this resume in JSON format:
        - Personal details (name, contact info)
        - Work experience (company, position, duration)
        - Education (degree, institution, year)
        - Skills
        - Certifications
        
        Return only valid JSON matching this structure:
        {json.dumps(template, indent=2)}
        
        Resume content:
        {text_content[:10000]}  # Limit content length
        """

        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[
                {"role": "system", "content": "You are a helpful resume parser. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        
        # Process response
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens

        # 🔹 Cost (update if pricing changes)
        input_cost = (input_tokens / 1_000_000) * 5.00
        output_cost = (output_tokens / 1_000_000) * 15.00

        logger.info(
            f"RJMS tokens → in:{input_tokens} out:{output_tokens} "
            f"cost:${input_cost + output_cost:.6f}"
        )
        result = response.choices[0].message.content.strip()
        if result.startswith("```"):
            result = result.split("```")[-2].strip()
        
        # Try to parse JSON
        try:
            return json.loads(result)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return None
            
    except Exception as e:
        logger.error(f"Error parsing resume: {str(e)}", exc_info=True)
        return None
    finally:
        # Reset file pointer if it's a file-like object
        if hasattr(resume_file, 'seek'):
            try:
                resume_file.seek(0)
            except:
                pass
