from common.mail_utils import ApiIntegrationRequestMailer
from letters.serializers import GeneratedLetterSerializer
from account.models import Account, Company
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from openai import OpenAI
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
import json

api_key = settings.OPENAI_API_KEY
client = OpenAI(api_key=api_key)
from .utils import generate_and_save_letter
from .models import ApiIntegrationRequest, LetterSettings, GeneratedLetter, LetterCreditPackage, LetterCreditWallet, LetterCreditTransaction
from .serializers import (
    ApiIntegrationRequestSerializer, LetterSettingsSerializer, GeneratedLetterSerializer,
    LetterCreditPackageSerializer, LetterCreditWalletSerializer, LetterCreditTransactionSerializer, ToolRequestSerializer
)

class OfferLetterGeneratorView(APIView):
    def post(self, request, id=None):
        data = request.data
        

        prompt = f"""You are an expert HR documentation assistant.

            Your task is to generate a professional, legally clean, and well-formatted Offer Letter
            using ONLY the data provided in the input fields.

            IMPORTANT RULES (STRICT):
            1. Follow the exact structure, headings, numbering, and tone of the provided sample offer letter.
            2. Do NOT add, remove, or assume any information that is not present in the input fields.
            3. Use formal corporate English suitable for Indian IT companies.
            4. Maintain consistent formatting: headings in bold, numbered sections, and clean spacing.
            5. Convert numbers into readable formats where required (example: INR 1000000 → INR 1,000,000).
            6. Dates must appear in proper sentence format (example: 12 January 2026).
            7. Use the candidate’s first name in the greeting and full name in the address section.
            8. Ensure the final output is ready to be directly converted into a PDF.

            --------------------------------
            INPUT DATA (FIELDS)
            --------------------------------

            Candidate Full Name: {data.get('candidate_full_name')}
            Candidate First Name: {data.get('candidate_first_name')}
            Candidate Address: {data.get('candidate_address')}

            Offer Date: {data.get('offer_date')}
            Acceptance Deadline: {data.get('acceptance_deadline')}

            Company Name: {data.get('company_name')}
            Role Title: {data.get('role_title')}
            Department: {data.get('department')}

            Reporting Manager: {data.get('reporting_manager')}
            Work Location: {data.get('work_location')}
            Work Model: {data.get('work_model')}
            Employment Type: {data.get('employment_type')}

            Proposed Start Date: {data.get('start_date')}
            Probation Duration (months): {data.get('probation_months')}

            CTC (INR per annum): {data.get('ctc_amount')}

            Work Days (per week): {data.get('work_days')}
            Work Hours (per day): {data.get('work_hours')}
            Work Timing: {data.get('work_timing')}
            Weekly Off: {data.get('weekly_off')}

            Signatory Name: {data.get('signatory', {}).get('name', data.get('signatory_name', ''))}
            Signatory Title: {data.get('signatory', {}).get('title', data.get('signatory_title', ''))}
            Signatory Email: {data.get('signatory', {}).get('email', data.get('signatory_email', ''))}
            Signature Phone: {data.get('signatory', {}).get('phone', data.get('Signature_Phone', ''))}

            --------------------------------
            OUTPUT FORMAT (MANDATORY)
            --------------------------------

            Company Name  
            Work Location  

            Date: {data.get('offer_date')}

            To:  
            Candidate Full Name  
            Candidate Address (if provided)

            Subject: Offer of Employment for the position of {data.get('role_title')}

            Dear {data.get('candidate_first_name')},

            Introductory paragraph confirming the offer.

            1. Role and Start Details  
            (Include role title, department, reporting manager, employment type, work model, location, start date, probation) and this should be in bold and 
            e.g Role Title: **Senior Python Developer**
            Department/Function: **Web Development**
            Reporting to: **Name**
            Employment Type: **Full-time**
            Work Model: **Hybrid**
            Work Location: **city**
            Proposed Start Date: **2 February 2026**
            Probation Period: 3 months format.

            2. Compensation  
            (Mention CTC clearly in INR format)

            3. Working Hours and Leave  
            (Include work days, hours, weekly off) and this should be in bold and format like e.g
            Work Days: **day**
            Work Hours: **hour**
            Work Timing: **timing**
            Weekly Off: **week day like e.g saturday, sunday**
            Leave entitlements as per company policy applicable to your role.


            4. Pre-Joining Requirements  
            (Standard document verification paragraph)

            5. Confidentiality and Conduct  
            (Standard confidentiality and policy compliance paragraph)

            6. Acceptance of Offer  
            (Mention acceptance deadline clearly)

            Closing & Sign-off section with signatory details.

            --------------------------------
            FINAL CHECK
            --------------------------------
            - No placeholders should remain
            - No grammatical errors
            - No extra content
            - Professional HR-ready output only"""

        
        candidate_name = data.get('candidate_full_name')
        offer_letter, error = generate_and_save_letter(request, 'offer', prompt, data, candidate_name, 'letters', id)
        
        if error:
            return Response({'status': 'error', 'message': error}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response({   
            'status': 'success',
            'offer_letter': json.dumps(offer_letter)
        }, status=status.HTTP_200_OK)

class AppointmentLetterGeneratorView(APIView):
    # permission_classes = [IsAuthenticated]

    def post(self, request, id=None):
        data = request.data
        prompt = f"""You are an expert HR documentation assistant with deep knowledge of Indian employment laws.

            Your task is to generate a professional, legally compliant, and well-formatted Appointment Letter
            using ONLY the data provided in the input fields.

            IMPORTANT RULES (STRICT):
            1. Follow the exact structure, clause order, headings, numbering, and tone of the provided sample appointment letter.
            2. Do NOT add, remove, assume, or infer any information not present in the input fields.
            3. Use formal corporate English suitable for Indian companies.
            4. Maintain consistent formatting: bold headings, numbered clauses, clean spacing.
            5. Convert numbers into readable formats where required (example: INR 1000000 → INR 1,000,000).
            6. Dates must appear in DD/MM/YYYY format.
            7. Use the employee’s first name in the greeting and full name in the address and acceptance sections.
            8. If any optional field is empty, omit that line or sentence cleanly.
            9. Ensure the final output is ready to be directly converted into a PDF.
            10. Output ONLY the final appointment letter text.

            --------------------------------
            INPUT DATA (FIELDS)
            --------------------------------

            Company Name: {data.get('company_name')}
            Company Registered Address: {data.get('company_registered_address')}
            Company Email: {data.get('company_email')}
            Company Phone: {data.get('company_phone')}
            CIN: {data.get('cin_corporate_identification_number')}
            GSTIN: {data.get('gstin')}

            Appointment Letter Date: {data.get('appointment_letter_date')}
            Reference Number: {data.get('reference_number')}

            Jurisdiction City: {data.get('jurisdiction_city')}
            Include Arbitration Clause: {data.get('include_arbitration_clause')}
            Arbitration City: {data.get('arbitration_city')}

            Employee Full Name: {data.get('employee_full_name')}
            Employee First Name: {data.get('employee_first_name')}
            Employee Address: {data.get('employee_address')}
            Acceptance Date: {data.get('acceptance_date')}

            Role Title / Designation: {data.get('role_title_designation')}
            Department: {data.get('department')}
            Reporting Manager: {data.get('reporting_manager_name_title')}
            Employment Type: {data.get('employment_type')}
            Work Model: {data.get('work_model')}
            Work Location: {data.get('work_location')}
            Date of Joining: {data.get('date_of_joining')}

            Probation Duration (months): {data.get('probation_duration_months')}
            Max Probation Extension (months): {data.get('max_probation_extension_months')}

            Work Days: {data.get('work_days')}
            Work Hours: {data.get('work_hours')}
            Weekly Off: {data.get('weekly_off')}

            CTC (INR per annum): {data.get('ctc_inr_per_annum')}
            Attach Salary Annexure: {data.get('attach_salary_annexure')}
            Salary Breakup Details: {data.get('salary_breakup_details_if_annexure')}

            Notice Period During Probation (days): {data.get('notice_period_during_probation_days')}
            Notice Period Post Confirmation (days): {data.get('notice_period_post_confirmation_days')}

            Non-Solicitation Period (months): {data.get('non_solicitation_period_months')}

            Signatory Name: {data.get('signatory', {}).get('name', data.get('signatory_name', ''))}
            Signatory Title: {data.get('signatory', {}).get('title', data.get('signatory_title', ''))}
            Signatory Email: {data.get('signatory', {}).get('email', data.get('signatory_email', ''))}
            Signatory Phone: {data.get('signatory', {}).get('phone', data.get('signatory_phone', ''))}

            --------------------------------
            OUTPUT FORMAT (MANDATORY)
            --------------------------------

            Company Name  
            Company Registered Address  
            Email: Company Email | Phone: Company Phone  
            (CIN and GSTIN only if provided)

            Date: Appointment Letter Date  
            Ref: Reference Number  

            To:  
            Employee Full Name  
            Employee Address  

            Subject: Letter of Appointment for the position of Role Title / Designation

            Dear Employee First Name,

            Introductory paragraph confirming appointment and acceptance date.

            1. Appointment Details  
            (Include designation, department, reporting manager)  
            Employment Type: **value**  
            Work Model: **value**  
            Work Location: **value**  
            Date of Joining: **value**

            2. Probation Period  
            (Mention probation duration, notice during probation, and extension only if provided)

            3. Compensation  
            (Mention annual CTC in INR format; mention Annexure A only if applicable)

            4. Working Hours and Leave  
            Work Days: **value**  
            Work Hours: **value**  
            Weekly Off: **value**  
            Leave entitlements as per company policy.

            5. Company Policies  
            (Standard company policy paragraph)

            6. Confidentiality and Data Protection  
            (Standard confidentiality clause)

            7. Intellectual Property  
            (Standard IP ownership clause)

            8. Conflict of Interest  
            (Standard conflict of interest clause)

            9. Non-Solicitation  
            (Mention non-solicitation duration)

            10. Company Property  
            (Standard company property clause)

            11. Termination and Notice Period  
            (Mention post-confirmation notice period)

            12. Full and Final Settlement  
            (Standard settlement clause)

            13. Governing Law and Jurisdiction  
            (Indian law, jurisdiction city; include arbitration only if enabled)

            14. Entire Agreement  
            (Standard entire agreement clause)

            Closing paragraph requesting signed acceptance.

            Warm regards,

            Signatory Name  
            Signatory Title  
            Company Name  
            Email: Signatory Email  
            Phone: Signature Phone  

            ---
            EMPLOYEE ACCEPTANCE

            I, Employee Full Name, accept this appointment and agree to the terms stated above.

            Signature: ____________________  
            Date: ____________________  

            ---
            Disclaimer paragraph in professional legal tone.

            --------------------------------
            FINAL CHECK
            --------------------------------
            - No placeholders should remain
            - No grammatical errors
            - Exact clause numbering (1–14)
            - No extra content
            - Professional HR-ready output only
            """

        employee_name = data.get('employee_full_name')
        appointment_letter, error = generate_and_save_letter(request, 'appointment', prompt, data, employee_name,"letters", id)
        
        if error:
            return Response({'status': 'error', 'message': error}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'success',    
            'appointment_letter': appointment_letter
        }, status=status.HTTP_200_OK)

class ConfirmationLetterGeneratorView(APIView):
    def post(self,request,id=None):
        data = request.data
        prompt = f"""
            You are an expert HR documentation assistant with strong knowledge of Indian employment practices.

            Your task is to generate a professional, well-structured, and legally appropriate **Employee Confirmation Letter**
            using ONLY the data provided in the input fields.

            IMPORTANT RULES (STRICT):
            1. Follow the exact structure, clause order, headings, numbering, and professional tone of the provided confirmation letter sample.
            2. Do NOT add, remove, assume, or infer any information not present in the input fields.
            3. Use formal corporate English suitable for Indian companies.
            4. Maintain consistent formatting: clear spacing, bold names/titles where appropriate, numbered sections.
            5. Convert numbers into readable format where required (example: 1000000 → 1,000,000).
            6. Dates must appear in DD/MM/YYYY format.
            7. Use the employee’s first name in the greeting and full name in address and acknowledgment sections.
            8. If any optional field is empty, omit that line or sentence cleanly.
            9. Ensure the final output is ready for direct PDF generation on company letterhead.
            10. Output ONLY the final confirmation letter text.

            --------------------------------
            INPUT DATA (FIELDS)
            --------------------------------

            Company Name: {data.get('company_name')}
            Company Address: {data.get('company_address')}
            Company Email: {data.get('company_email')}
            Company Phone: {data.get('company_phone')}

            Confirmation Letter Date: {data.get('confirmation_date')}

            Employee Full Name: {data.get('employee_full_name')}
            Employee First Name: {data.get('employee_first_name')}
            Employee Address: {data.get('employee_address')}

            Role Title / Designation: {data.get('role_title_or_designation')}
            Department: {data.get('department')}
            Reporting Manager: {data.get('reporting_manager')}
            Work Location: {data.get('work_location')}
            Work Model (Onsite/Hybrid/Remote): {data.get('work_model')}

            Original Appointment Letter Date: {data.get('original_appointment_letter_date')}
            Confirmation Effective Date: {data.get('confirmation_effective_date')}

            Notice Period (days): {data.get('notice_period_days')}
            Current Annual CTC (INR): {data.get('current_ctc_inr_per_annum')}

            Signatory Name: {data.get('signatory', {}).get('name', data.get('signatory_name', ''))}
            Signatory Title: {data.get('signatory', {}).get('title', data.get('signatory_title', ''))}
            Signatory Email: {data.get('signatory', {}).get('email', data.get('signatory_email', ''))}
            Signatory Phone: {data.get('signatory', {}).get('phone', data.get('signatory_phone', ''))}

            --------------------------------
            OUTPUT FORMAT (MANDATORY)
            --------------------------------

            Company Name  
            Company Address  
            Company Email | Company Phone  

            Date: Confirmation Letter Date  

            To:  
            Employee Full Name  
            Employee Address  

            Subject: Confirmation of Employment as Role Title / Designation

            Dear Employee First Name,

            Opening paragraph referencing successful completion of probation and original appointment letter date.

            1. Confirmation Details  
            Confirm employment as **Role Title / Designation** in the **Department** department effective **Confirmation Effective Date**.  
            State reporting manager, work location, and work model.

            2. Terms of Employment  
            State that all terms from the original appointment letter dated **Original Appointment Letter Date** remain applicable.  
            Mention current annual CTC in INR format.

            3. Notice Period  
            Clearly mention notice period in days.

            4. Policies and Confidentiality  
            Standard statement confirming continued adherence to company policies, code of conduct, and confidentiality obligations.

            5. Acknowledgment  
            Request the employee to sign and return a copy of the letter.

            Professional closing paragraph appreciating employee contribution and expressing continued association.

            Warm regards,

            Signatory Name  
            Signatory Title  
            Company Name  
            Signatory Email | Signatory Phone  

            ---
            EMPLOYEE ACKNOWLEDGMENT

            I, Employee Full Name, acknowledge receipt of this confirmation letter and accept the terms mentioned above.

            Signature: ____________________  
            Date: ____________________  

            ---
            Disclaimer: This confirmation letter is issued as a standard employment document and should be reviewed by a qualified HR or legal professional to ensure compliance with applicable labor laws.

            --------------------------------
            FINAL CHECK
            --------------------------------
            - No placeholders remain
            - Professional HR tone maintained
            - Proper clause numbering (1–5)
            - No extra sections added
            - Clean formatting for PDF generation
            """

        
        employee_name = data.get('employee_full_name')
        confirmation_letter, error = generate_and_save_letter(request, 'confirmation', prompt, data, employee_name,"letters", id)
        
        if error:
            return Response({'status': 'error', 'message': error}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'success',
            'confirmation_letter': json.dumps(confirmation_letter)
        }, status=status.HTTP_200_OK)

class ExperienceLetterGeneratorView(APIView):
    def post(self,request,id=None):
        data = request.data
        prompt = f"""
                You are an expert HR documentation assistant with strong knowledge of Indian employment documentation standards.

                Your task is to generate a professional, well-structured, and legally appropriate **Employee Experience Letter**
                using ONLY the data provided in the input fields.

                IMPORTANT RULES (STRICT):
                1. Follow a formal Indian corporate HR letter format with proper spacing and professional paragraph structure.
                2. Do NOT add, remove, assume, or infer any information that is not present in the input fields.
                3. Use professional business English suitable for Indian companies.
                4. Maintain clean formatting with bold where appropriate (Company Name, Employee Name, Role Title).
                5. Use the provided Pronoun exactly as given (He/She/They) and ensure grammatical correctness throughout.
                6. Dates must appear exactly as provided (do not reformat unless specified).
                7. Use the employee’s full name in the opening paragraph and first name in the closing sentence.
                8. If any optional field is empty, omit that sentence or line cleanly without leaving blanks.
                9. The letter must be written in third-person format.
                10. Output ONLY the final experience letter text, ready for direct PDF generation on company letterhead.

                --------------------------------
                INPUT DATA (FIELDS)
                --------------------------------

                Company Name: {data.get('company_name', '')}
                Company Address: {data.get('company_address', '')}
                Company Email: {data.get('company_email', '')}
                Company Phone: {data.get('company_phone', '')}

                Experience Letter Date: {data.get('experience_letter_date', '')}

                Employee Full Name: {data.get('employee_full_name', '')}
                Employee First Name: {data.get('employee_first_name', '')}

                Role Title / Designation: {data.get('role_title_designation', '')}
                Department: {data.get('department', '')}
                Date of Joining: {data.get('date_of_joining', '')}
                Last Working Date: {data.get('last_working_date', '')}
                Reporting Manager: {data.get('reporting_manager', '')}

                Key Responsibilities: {data.get('key_responsibilities', '')}

                Pronoun (He/She/They): {data.get('pronoun', '')}
                Conduct Description: {data.get('conduct_description', '')}

                Signatory Name: {data.get('signatory', {}).get('name', data.get('signatory_name', ''))}
                Signatory Title: {data.get('signatory', {}).get('title', data.get('signatory_title', ''))}
                Signatory Email: {data.get('signatory', {}).get('email', data.get('signatory_email', ''))}
                Signatory Phone: {data.get('signatory', {}).get('phone', data.get('signatory_phone', ''))}

                --------------------------------
                OUTPUT FORMAT (MANDATORY)
                --------------------------------

                **Company Name**  
                Company Address  
                Company Email | Company Phone  

                Date: Experience Letter Date  

                TO WHOM IT MAY CONCERN  

                This is to certify that **Employee Full Name** was employed with **Company Name** from **Date of Joining** to **Last Working Date**.

                During this period, Pronoun served as **Role Title / Designation** in the **Department** department, reporting to Reporting Manager.

                Pronoun key responsibilities included:  
                Key Responsibilities

                Throughout Pronoun tenure with us, Employee First Name demonstrated Conduct Description. Pronoun made valuable contributions to the team and organization.

                We wish Employee First Name all the best in Pronoun future endeavors.

                For **Company Name**

                Signatory Name  
                Signatory Title  
                Signatory Email | Signatory Phone  

                --------------------------------
                FINAL CHECK
                --------------------------------
                - No placeholders remain
                - Pronouns are used correctly and consistently
                - Professional HR tone maintained
                - No extra assumptions added
                - Clean formatting suitable for PDF generation
                """
        
        employee_name = data.get('employee_full_name')
        experience_letter, error = generate_and_save_letter(request, 'experience', prompt, data, employee_name,'letters', id)
        
        if error:
            return Response({'status': 'error', 'message': error}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'success',
            'experience_letter': json.dumps(experience_letter)
        }, status=status.HTTP_200_OK)

class IncrementLetterGeneratorView(APIView):
    def post(self,request,id=None):
        data = request.data
        prompt = f"""
                You are an expert HR documentation assistant with strong knowledge of Indian employment practices.

                Your task is to generate a professional, well-structured, and legally appropriate **Employee Salary Increment Letter**
                using ONLY the data provided in the input fields.

                IMPORTANT RULES (STRICT):
                1. Follow a formal Indian corporate HR letter format with clear structure, headings, and numbered clauses.
                2. Do NOT add, remove, assume, or infer any information not present in the input fields.
                3. Use professional business English suitable for Indian companies.
                4. Maintain consistent formatting: proper spacing, bold names/titles where appropriate, numbered sections.
                5. Convert numbers into readable INR format with commas (example: 300000 → 3,00,000).
                6. Dates must appear in DD/MM/YYYY format.
                7. Use the employee’s first name in the greeting and full name in the address and acknowledgment sections.
                8. If any optional field is empty, omit that line or sentence cleanly.
                9. Ensure the final output is ready for direct PDF generation on company letterhead.
                10. Output ONLY the final increment letter text.

                --------------------------------
                INPUT DATA (FIELDS)
                --------------------------------

                Company Name: {data.get('company_name', '')}
                Company Address: {data.get('company_address', '')}
                Company Email: {data.get('company_email', '')}
                Company Phone: {data.get('company_phone', '')}

                Increment Letter Date: {data.get('increment_letter_date', '')}

                Employee Full Name: {data.get('employee_full_name', '')}
                Employee First Name: {data.get('employee_first_name', '')}
                Employee Address: {data.get('employee_address', '')}

                Role Title / Designation: {data.get('role_title', '')}
                Department: {data.get('department', '')}

                Increment Effective Date: {data.get('increment_effective_date', '')}
                Previous CTC (INR per annum): {data.get('previous_ctc_inr_per_annum', '')}
                Revised CTC (INR per annum): {data.get('revised_ctc_inr_per_annum', '')}

                Attach Salary Annexure (Yes/No): {data.get('attach_salary_annexure', '')}
                Salary Breakup Details: {data.get('salary_breakup_details', '')}

                Signatory Name: {data.get('signatory', {}).get('name', data.get('signatory_name', ''))}
                Signatory Title: {data.get('signatory', {}).get('title', data.get('signatory_title', ''))}
                Signatory Email: {data.get('signatory', {}).get('email', data.get('signatory_email', ''))}
                Signatory Phone: {data.get('signatory', {}).get('phone', data.get('signatory_phone', ''))}

                --------------------------------
                OUTPUT FORMAT (MANDATORY)
                --------------------------------

                Company Name  
                Company Address  
                Company Email | Company Phone  

                Date: Increment Letter Date  

                To:  
                Employee Full Name  
                Employee Address  

                Subject: Salary Revision – Role Title / Designation

                Dear Employee First Name,

                Opening paragraph appreciating the employee’s contribution, performance, and value to the organization.

                1. Revised Compensation  
                Clearly state that the employee’s annual CTC has been revised to **Revised CTC (INR per annum)** effective **Increment Effective Date**.  
                Mention that this is an increase from the previous CTC of **Previous CTC (INR per annum)**.

                2. Statutory Deductions  
                State that statutory deductions such as Provident Fund (PF), ESI (if applicable), and Professional Tax will be applied as per government regulations.

                3. Other Terms and Conditions  
                Mention that all other terms and conditions of employment remain unchanged and continue to be applicable.

                4. Salary Structure Annexure (CONDITIONAL)  
                Include this section ONLY if Attach Salary Annexure = "Yes".  
                Add heading: **Annexure A – Salary Structure**  
                Neatly present Salary Breakup Details in structured format (table-style or bullet breakdown).

                5. Acknowledgment  
                Request the employee to sign and return a copy of the letter as confirmation of acceptance.

                Professional closing paragraph expressing appreciation and wishing continued success with the organization.

                Warm regards,

                Signatory Name  
                Signatory Title  
                Company Name  
                Signatory Email | Signatory Phone  

                ---
                EMPLOYEE ACKNOWLEDGMENT

                I, Employee Full Name, acknowledge receipt of this salary revision letter and accept the revised compensation structure.

                Signature: ____________________  
                Date: ____________________  

                ---
                Disclaimer: This salary revision letter is issued as a standard employment document and should be reviewed by a qualified HR or legal professional to ensure compliance with applicable labor laws.

                --------------------------------
                FINAL CHECK
                --------------------------------
                - No placeholders remain
                - Professional HR tone maintained
                - Proper clause numbering (1–5)
                - Annexure included only if required
                - Clean formatting for PDF generation
                """
        
        employee_name = data.get('employee_full_name')
        increment_letter, error = generate_and_save_letter(request, 'increment', prompt, data, employee_name,'letters', id)
        
        if error:
            return Response({'status': 'error', 'message': error}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'success',
            'increment_letter': json.dumps(increment_letter)
        }, status=status.HTTP_200_OK)

class RelievingLetterGeneratorView(APIView):
    def post(self,request,id=None):
        data = request.data
        prompt = f"""
                You are an expert HR documentation assistant with strong knowledge of Indian employment practices.

                Your task is to generate a professional, well-structured, and legally appropriate **Employee Relieving Letter**
                using ONLY the data provided in the input fields.

                IMPORTANT RULES (STRICT):
                1. Follow a formal Indian corporate HR letter format with clear structure, headings, and numbered clauses.
                2. Do NOT add, remove, assume, or infer any information not present in the input fields.
                3. Use professional business English suitable for Indian companies.
                4. Maintain consistent formatting: proper spacing, bold names/titles where appropriate, numbered sections.
                5. Dates must appear in DD/MM/YYYY format.
                6. Use the employee’s first name in the greeting and full name in the address section.
                7. If any optional field is empty, omit that line or sentence cleanly.
                8. Ensure the final output is ready for direct PDF generation on company letterhead.
                9. Include the Non-Solicitation clause ONLY if explicitly instructed.
                10. Output ONLY the final relieving letter text.

                --------------------------------
                INPUT DATA (FIELDS)
                --------------------------------

                Company Name: {data.get('company_name', '')}
                Company Address: {data.get('company_address', '')}
                Company Email: {data.get('company_email', '')}
                Company Phone: {data.get('company_phone', '')}

                Relieving Letter Date: {data.get('resignation_date', '')}

                Employee Full Name: {data.get('employee_full_name', '')}
                Employee First Name: {data.get('employee_first_name', '')}
                Employee Address: {data.get('employee_address', '')}

                Role Title / Designation: {data.get('role_title', '')}
                Resignation Date: {data.get('resignation_date', '')}
                Last Working Date: {data.get('last_working_date', '')}
                Handover To (Name & Title): {data.get('handover_to_name_title', '')}

                Include Non-Solicitation Reminder (Yes/No): {data.get('include_non_solicitation_reminder', '')}

                Signatory Name: {data.get('signatory', {}).get('name', data.get('signatory_name', ''))}
                Signatory Title: {data.get('signatory', {}).get('title', data.get('signatory_title', ''))}
                Signatory Email: {data.get('signatory', {}).get('email', data.get('signatory_email', ''))}
                Signatory Phone: {data.get('signatory', {}).get('phone', data.get('signatory_phone', ''))}

                --------------------------------
                OUTPUT FORMAT (MANDATORY)
                --------------------------------

                Company Name  
                Company Address  
                Company Email | Company Phone  

                Date: Relieving Letter Date  

                To:  
                Employee Full Name  
                Employee Address  

                Subject: Relieving Letter – Role Title / Designation  

                Dear Employee First Name,

                Opening paragraph formally acknowledging the employee’s resignation and expressing appreciation for their service.

                1. Acknowledgment of Resignation  
                Confirm receipt of resignation dated Resignation Date.

                2. Relieving from Duties  
                State that the employee has been relieved from their duties as Role Title / Designation effective Last Working Date, after completion of the notice period and required formalities.

                3. Handover and Company Property  
                Mention that the employee has completed the handover of responsibilities to Handover To (Name & Title).  
                Confirm that company property/assets have been returned (without listing items unless provided).

                4. Full and Final Settlement  
                State that full and final settlement, including pending salary, leave encashment (if applicable), and other dues, will be processed as per company policy subject to clearance procedures.

                5. Continuing Obligations  
                Remind the employee that confidentiality and data protection obligations continue even after separation.

                6. Non-Solicitation Reminder (CONDITIONAL)  
                Include this section ONLY if Include Non-Solicitation Reminder = "Yes".  
                Remind the employee of their obligation not to solicit clients, employees, or business associates as per employment agreement terms.

                Final Confirmation Paragraph  
                State that this letter serves as formal confirmation that the employee has been relieved from Company Name with effect from Last Working Date.  
                Thank them for their contributions and wish them success in future endeavors.

                Warm regards,

                Signatory Name  
                Signatory Title  
                Company Name  
                Signatory Email | Signatory Phone  

                ---
                Disclaimer: This relieving letter is issued as a standard employment document and should be reviewed by a qualified HR or legal professional to ensure compliance with applicable labor laws.

                --------------------------------
                FINAL CHECK
                --------------------------------
                - No placeholders remain
                - Professional HR tone maintained
                - Proper clause numbering
                - Conditional clause included only if required
                - Clean formatting for PDF generation
                """
        
        employee_name = data.get('employee_full_name')
        relieving_letter, error = generate_and_save_letter(request, 'relieving', prompt, data, employee_name,'letters', id)
        
        if error:
            return Response({'status': 'error', 'message': error}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'success',
            'relieving_letter': json.dumps(relieving_letter)
        }, status=status.HTTP_200_OK)

class LeavePolicyGeneatorView(APIView):
    def post(self, request, id=None):
        data = request.data
        prompt = f"""
                You are an expert HR policy documentation assistant with strong knowledge of Indian employment practices.

                Your task is to generate a **formal, well-structured Employee Leave Policy document**
                using ONLY the data provided in the input fields.

                ⚠️ STRICT INSTRUCTIONS:
                1. Do NOT assume or invent any information that is not present in the variables.
                2. If a field is empty, omit that specific detail gracefully without mentioning it is missing.
                3. Use professional corporate HR language suitable for Indian companies.
                4. Keep the tone aligned with: "{data.get('tone')}" (e.g., Formal, Friendly, Strict, Supportive).
                5. The document must be cleanly formatted with headings, numbering, and spacing suitable for an official PDF.
                6. The output must look like a real company policy document — not like AI output.

                ---

                ### 📌 COMPANY & POLICY DETAILS
                Company Name: {data.get('company_name')}  
                Policy Effective Date: {data.get('effective_date')}  
                Applicable To: {data.get('applicable_to')}  
                Department Name: {data.get('department_name')}  
                Location / State: {data.get('location_state')}  
                Policy Owner: {data.get('policy_owner')}  
                Approving Authority: {data.get('approving_authority')}  

                ---
    
                ### 📌 LEAVE STRUCTURE INPUTS
                Leave Year Definition: {data.get('leave_year_definition')}  
                Casual Leave Per Year: {data.get('casual_leave_days')}  
                Sick Leave Per Year: {data.get('sick_leave_days')}  
                Earned/Privilege Leave Per Year: {data.get('earned_leave_days')}  
                Maternity Leave Applicable: {data.get('maternity_applicable')}  
                Paternity Leave Days: {data.get('paternity_leave_days')}  
                Bereavement Leave Days: {data.get('bereavement_leave_days')}  
                Comp Off Rule: {data.get('comp_off_rule')}  

                ---

                ### 📌 LEAVE RULES & ELIGIBILITY
                Probation Leave Eligibility: {data.get('probation_leave_eligibility')}  
                Half Day Leave Allowed: {data.get('half_day_allowed')}  
                Sandwich Rule: {data.get('sandwich_rule')}  
                Medical Certificate Required After (days): {data.get('medical_cert_days')}  
                Peak Period / Blackout Dates: {data.get('blackout_dates')}  

                ---

                ### 📌 APPLICATION & APPROVAL PROCESS
                Leave Request Channel: {data.get('leave_request_channel')}  
                Approval Workflow: {data.get('approval_workflow')}  
                Notice Required for Planned Leave (days): {data.get('notice_required_days')}  
                Leave During Notice Period Rule: {data.get('leave_during_notice_rule')}  

                ---

                ### 📌 BALANCE, CARRY FORWARD & ENCASHMENT
                Leave Carry Forward Allowed: {data.get('leave_carry_forward_allowed')}  
                Maximum Carry Forward Days: {data.get('max_carry_forward_days')}  
                Leave Encashment Allowed: {data.get('leave_encashment_allowed')}  

                ---

                ### 📌 DISCIPLINE
                Unapproved Absence Consequence: {data.get('unapproved_absence_consequence')}  

                ---

                ### 📄 DOCUMENT STRUCTURE TO FOLLOW

                Generate the policy using this structure:

                1. **Title Section**
                - “Leave Policy”
                - Company Name
                - Effective Date

                2. **Purpose**

                3. **Scope & Applicability**

                4. **Leave Year & Definitions**
                - Define each leave type clearly

                5. **Types of Leave & Entitlement**
                - Casual Leave
                - Sick Leave
                - Earned/Privilege Leave
                - Maternity Leave (if applicable)
                - Paternity Leave (if applicable)
                - Bereavement Leave
                - Compensatory Off

                6. **Leave Application & Approval Process**
                - How to apply
                - Notice requirements
                - Approval authority
                - Emergency leave handling

                7. **Leave Rules & Conditions**
                - Probation rules
                - Sandwich rule
                - Half-day leave
                - Medical documents
                - Blackout periods
                - Leave during notice period

                8. **Carry Forward & Encashment Rules**

                9. **Unapproved Leave & Disciplinary Action**

                10. **FAQs Section**
                Include ONLY if: {data.get('include_faqs')} = Yes  
                Add 4–6 helpful HR-style FAQs based strictly on provided data.

                11. **Policy Ownership Statement**
                Mention Policy Owner and Approving Authority

                12. **Closing Statement**
                Professional disclaimer about company’s right to amend policy

                ---

                Return only the final formatted Leave Policy document.
                Do not include explanations, notes, or AI commentary.
                """
        
        leave_policy, error = generate_and_save_letter(request, 'leave_policy', prompt, data, None, 'policies', id)
        
        if error:
            return Response({'status': 'error', 'message': error}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'success',
            'leave_policy': json.dumps(leave_policy)
        }, status=status.HTTP_200_OK)

class WFHHybridPolicyGeneatorView(APIView):
    def post(self, request, id=None):
        data = request.data
        
        prompt = f"""
            You are an expert HR policy documentation assistant with strong knowledge of corporate workplace policies.

            Your task is to generate a professional, well-structured **Work From Home (WFH) / Hybrid Work Policy document**
            using ONLY the data provided in the input fields.

            IMPORTANT RULES (STRICT):
            1. Follow a formal corporate HR policy tone.
            2. Do NOT add, remove, assume, or invent any information not present in the input fields.
            3. Use clear section headings, numbered clauses, and professional policy language.
            4. The document must read like an official internal company policy suitable for PDF distribution.
            5. If a field is empty, omit that specific detail naturally without inserting placeholders.
            6. If "Include_FAQs_Section" is "Yes", include an FAQs section at the end. If "No", omit it.
            7. If "Include_Confidentiality_Reminder" is "Yes", include a confidentiality reminder clause under Security.
            8. Keep the structure consistent and logically ordered.

            --------------------------------------------------

            DOCUMENT TITLE

            WORK FROM HOME / HYBRID WORK POLICY  
            {data.get('company_name')}  
            Effective Date: {data.get('effective_date')}

            --------------------------------------------------

            1. PURPOSE & SCOPE  
            Describe the purpose of the policy and clearly state that it applies to: {data.get('applicable_to')}.  
            Mention that the company operates under a {data.get('work_model')} model.

            --------------------------------------------------

            2. POLICY OWNERSHIP & APPROVAL  
            State that the policy is owned by {data.get('policy_owner')} and approved by {data.get('approving_authority')}.

            --------------------------------------------------

            3. WORK HOURS, AVAILABILITY & OFFICE PRESENCE  
            Include the following details:
            - Core Working Hours: {data.get('core_hours')}  
            - Availability Expectations: {data.get('availability_expectations')}  
            - Office Days Per Week: {data.get('office_days_per_week')}  
            - Location Constraints: {data.get('location_constraints')}  
            - Attendance Tracking Method: {data.get('attendance_tracking')}

            --------------------------------------------------

            4. COMMUNICATION & MEETING NORMS  
            Explain expectations using:
            - Meeting Norms: {data.get('meeting_norms')}  
            Include standards for professional communication and responsiveness during working hours.

            --------------------------------------------------

            5. PRODUCTIVITY & PERFORMANCE TRACKING  
            Describe how employee performance and deliverables are monitored using:
            - Productivity Reporting Method: {data.get('productivity_reporting')}

            --------------------------------------------------

            6. EQUIPMENT & DEVICE USAGE  
            Provide rules regarding work devices:
            - Company Device Provided: {data.get('device_provided')}  
            - Allowed Devices: {data.get('allowed_devices')}

            --------------------------------------------------

            7. DATA SECURITY & INTERNET REQUIREMENTS  
            Include the following:
            - Data Security Rules: {data.get('security_rules')}  
            - WiFi Requirement: {data.get('wifi_requirement')}

            If Include_Confidentiality_Reminder = "Yes", add a professional reminder that employees must protect confidential and proprietary company information at all times.

            --------------------------------------------------

            8. REIMBURSEMENTS & EXPENSES  
            Explain reimbursement eligibility, approval requirements, and process using:
            - Reimbursements: {data.get('reimbursements')}

            --------------------------------------------------

            9. POLICY MISUSE & CONSEQUENCES  
            Clearly state disciplinary consequences for policy violations using:
            - Misuse Consequence: {data.get('misuse_consequence')}

            --------------------------------------------------

            10. EXCEPTIONS & ENFORCEMENT  
            State that any exceptions to this policy require written approval from the Policy Owner and that violations may result in disciplinary or corrective action.

            --------------------------------------------------

            11. FAQs (Include only if Include_FAQs_Section = "Yes")  
            Generate 3–4 professional FAQ questions and answers strictly based on the policy details provided above. Do not introduce new rules.

            --------------------------------------------------

            STYLE REQUIREMENTS:
            - Use formal HR policy language
            - Use numbered headings and bullet points where appropriate
            - Keep paragraphs clear, professional, and concise
            - Ensure the final output looks like an official company policy document ready for PDF formatting

            Generate the final policy document now.
            """

        
        wfh_policy, error = generate_and_save_letter(request, 'wfh_policy', prompt, data, None, 'policies', id)
        
        if error:
            return Response({'status': 'error', 'message': error}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'success',
            'wfh_policy': json.dumps(wfh_policy)
        }, status=status.HTTP_200_OK)

class FreelancerContractGeneratorView(APIView):
    def post(self, request, id=None):
        data = request.data
        prompt = f"""
                You are an expert Legal Documentation and HR Contracts assistant with strong knowledge of Indian freelance and consultancy agreements.

                Your task is to generate a professional, well-structured, and legally appropriate **Freelancer / Consultant Services Agreement**
                using ONLY the data provided in the input fields.

                IMPORTANT RULES (STRICT):
                1. Follow a formal Indian corporate legal agreement format with clear structure, headings, and numbered clauses.
                2. Do NOT add, remove, assume, or infer any information not present in the input fields.
                3. Use professional legal business English suitable for Indian companies.
                4. Maintain consistent formatting: bold section headings, numbered clauses, proper spacing between sections.
                5. Dates must appear in DD/MM/YYYY format.
                6. Clearly establish an **Independent Contractor** relationship — not employment.
                7. If any optional field is empty, omit that line or sentence cleanly.
                8. Ensure the final output is ready for direct PDF generation on company letterhead.
                9. Output ONLY the final agreement text — no explanations or AI commentary.

                --------------------------------
                INPUT DATA (FIELDS)
                --------------------------------

                Company Name: {data.get('company_name')}
                Company Address: {data.get('company_address', data.get('company_registered_address'))}
                Company Representative: {data.get('company_representative')}
                Representative Title: {data.get('signatory', {}).get('title')}

                Freelancer Name: {data.get('freelancer_name', data.get('freelancer_full_name'))}
                Freelancer Address: {data.get('freelancer_address')}
                Freelancer Email: {data.get('freelancer_email')}
                Freelancer Phone: {data.get('freelancer_phone')}
                Freelancer PAN: {data.get('freelancer_pan')}
                Freelancer GST: {data.get('freelancer_gst')}

                Effective Date: {data.get('effective_date')}

                Service Type: {data.get('service_type')}
                Scope of Work: {data.get('scope_of_work')}
                Deliverables: {data.get('deliverables')}

                Timeline Start Date: {data.get('start_date')}
                Timeline End Date: {data.get('end_date')}

                Working Mode: {data.get('working_mode')}
                Reporting Contact (Name & Title): {data.get('reporting_contact')}

                Fee Type: {data.get('fee_type')}
                Fee Amount: {data.get('fee_amount')}
                Payment Frequency: {data.get('payment_frequency')}
                Payment Due Days After Invoice: {data.get('payment_due_days')}
                Reimbursement Terms: {data.get('reimbursement_terms')}
                TDS Applicable (Yes/No): {data.get('tds_applicable')}

                Confidentiality Required (Yes/No): {data.get('confidentiality_required')}
                IP Ownership: {data.get('ip_ownership')}

                Non-Solicitation Period: {data.get('non_solicitation_period')}

                Termination Notice (Days): {data.get('termination_notice', data.get('termination_notice_days'))}
                Termination for Cause Clause: {data.get('termination_for_cause')}

                Governing Law State: {data.get('governing_law_state')}
                Jurisdiction City: {data.get('jurisdiction_city')}

                Dispute Resolution Method: {data.get('dispute_resolution')}
                Arbitration City: {data.get('arbitration_city')}

                --------------------------------
                OUTPUT FORMAT (MANDATORY)
                --------------------------------

                **FREELANCER / CONSULTANT SERVICES AGREEMENT**

                **1. PARTIES AND PURPOSE**  
                State the agreement date (Effective Date), company details, freelancer details (including PAN/GST if provided), and purpose of engaging the freelancer for Service Type.

                **2. DEFINITIONS**  
                Define:
                - Services (based on Service Type and Scope of Work)  
                - Deliverables  
                - Confidential Information  

                **3. SCOPE OF SERVICES AND DELIVERABLES**  
                Describe scope of work, deliverables, working mode, and reporting contact.

                **4. TERM AND TIMELINE**  
                Mention start date, end date, and that timelines apply to agreed deliverables.

                **5. FEES, INVOICING, PAYMENT TERMS & TAXES**  
                Specify fee type, fee amount, payment frequency, invoice due days, reimbursement terms, TDS applicability, and GST responsibility (if GST provided).

                **6. INDEPENDENT CONTRACTOR STATUS**  
                Clearly state freelancer is not an employee and not entitled to employee benefits.

                **7. CONFIDENTIALITY & DATA PROTECTION**  
                Include ONLY if Confidentiality Required = "Yes".  
                Cover non-disclosure, restricted use, and survival after termination.

                **8. INTELLECTUAL PROPERTY OWNERSHIP**  
                State ownership of deliverables as per IP Ownership input.

                **9. NON-SOLICITATION**  
                Include restriction for the specified Non-Solicitation Period.

                **10. CONFLICT OF INTEREST**  
                Freelancer must disclose conflicts and avoid competing obligations.

                **11. TERMINATION**  
                Include termination notice period and termination for cause clause.

                **12. RETURN OF PROPERTY & DATA DELETION**  
                Freelancer must return company materials and delete confidential data upon termination.

                **13. LIMITATION OF LIABILITY**  
                Standard limitation excluding indirect and consequential damages.

                **14. GOVERNING LAW & JURISDICTION**  
                Use Governing Law State and Jurisdiction City.

                **15. DISPUTE RESOLUTION**  
                Mention dispute resolution method and arbitration city if applicable.

                **16. ENTIRE AGREEMENT**  
                Standard entire agreement clause.

                **SIGNATURE BLOCKS**

                For {data.get('company_name')}:  
                Name: {data.get('company_representative')}  
                Title: {data.get('signatory', {}).get('title')}  
                Signature: ___________________________
                Date:  ___________________________

                For {data.get('freelancer_name', data.get('freelancer_full_name'))}:  
                Name: {data.get('freelancer_name', data.get('freelancer_full_name'))}  
                Signature:  ___________________________
                Date:  ___________________________

                --------------------------------
                FINAL CHECK
                --------------------------------
                - No placeholders remain  
                - Professional legal tone maintained  
                - Proper clause numbering  
                - Conditional clauses included only if required  
                - Clean formatting for PDF generation
                """
        
        freelancer_name = data.get('freelancer_name', data.get('freelancer_full_name'))
        contract, error = generate_and_save_letter(request, 'freelancer_contract', prompt, data, freelancer_name, "contracts", id)
        
        if error:
            return Response({'status': 'error', 'message': error}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'success',
            'freelancer_contract': json.dumps(contract)
        }, status=status.HTTP_200_OK)

class NDAContractGeneratorView(APIView):
    def post(self, request, id=None):
        data = request.data
        prompt = f"""You are an expert legal documentation assistant.

                Your task is to generate a professional, legally structured, and well-formatted
                NON-DISCLOSURE AGREEMENT (NDA) using ONLY the data provided in the input fields.

                IMPORTANT RULES (STRICT):
                1. Follow the exact structure, clause order, headings, and tone of a formal corporate NDA.
                2. Do NOT add, remove, or assume any information that is not present in the input fields.
                3. Use formal legal English suitable for Indian corporate agreements.
                4. Maintain consistent formatting: clause headings in bold, numbered sections, clean spacing.
                5. Dates must appear in proper sentence format (example: 12 January 2026).
                6. Where durations are mentioned, display them clearly in months (example: 24 months).
                7. If a field is blank, write the clause in a neutral legal way WITHOUT inserting assumptions.
                8. Ensure the final output is ready to be directly converted into a PDF.

                --------------------------------
                INPUT DATA (FIELDS)
                --------------------------------
                
                Company Name: {data.get('company_name')}
                Company Registered Address: {data.get('company_address')}
                Company Representative Name & Title: {data.get('company_representative')}

                Counterparty Full Name: {data.get('counterparty_name')}
                Counterparty Type (Individual/Company/Consultant/etc.): {data.get('counterparty_type')}
                Counterparty Address: {data.get('counterparty_address')}

                Effective Date: {data.get('effective_date')}
                NDA Type (One-way/Mutual): {data.get('nda_type')}
                Purpose of Disclosure: {data.get('purpose_of_disclosure')}

                Confidentiality Term (months): {data.get('confidentiality_term_months')}
                Survival After Termination (months): {data.get('survival_months')}

                Permitted Use of Information: {data.get('permitted_use')}
                Permitted Recipients: {data.get('permitted_recipients')}
                Security Measures Required: {data.get('security_measures')}

                Return or Destroy Clause: {data.get('return_on_request')}
                Exclusion of Public Domain Information Clause: {data.get('exclude_public_info')}
                Include Injunctive Relief Clause: {data.get('include_injunctive_relief')}

                Governing Law State: {data.get('governing_law_state')}
                Jurisdiction City: {data.get('jurisdiction_city')}
                Dispute Resolution Method: {data.get('dispute_resolution')}
                Arbitration City (if applicable): {data.get('arbitration_city')}

                --------------------------------
                OUTPUT FORMAT (MANDATORY)
                --------------------------------

                **NON-DISCLOSURE AGREEMENT**

                **1. PARTIES AND PURPOSE**  
                This Non-Disclosure Agreement (“Agreement”) is entered into as of **{data.get('effective_date')}** (“Effective Date”) by and between **{data.get('company_name')}**, having its registered office at **{data.get('company_address')}**, represented by **{data.get('company_representative')}** (hereinafter referred to as the “Disclosing Party”), and **{data.get('counterparty_name')}**, a **{data.get('counterparty_type')}** having its registered address at **{data.get('counterparty_address')}** (hereinafter referred to as the “Receiving Party”).  
                The purpose of this Agreement is **{data.get('purpose_of_disclosure')}**.

                **2. DEFINITION OF CONFIDENTIAL INFORMATION**  
                (Standard legal definition paragraph for confidential information in corporate NDAs.)

                **3. OBLIGATIONS OF THE RECEIVING PARTY**  
                a) Use the Confidential Information strictly for **{data.get('permitted_use')}**  
                b) Protect the information using **{data.get('security_measures')}**  
                c) Disclose only to **{data.get('permitted_recipients')}** on a need-to-know basis

                **4. PERMITTED DISCLOSURES**  
                (Standard permitted disclosure paragraph tied to authorized recipients.)

                **5. EXCLUSIONS**  
                Confidential Information does not include information that:  
                a) {data.get('exclude_public_info')}  
                b) Was already lawfully known  
                c) Was independently developed  
                d) Is disclosed under legal obligation with prior notice

                **6. SECURITY MEASURES AND BREACH NOTIFICATION**  
                (Standard data protection and breach notification clause.)

                **7. RETURN OR DESTRUCTION OF INFORMATION**  
                Upon request or termination, the Receiving Party shall **{data.get('return_on_request')}**.

                **8. NO LICENSE OR TRANSFER OF RIGHTS**  
                (Standard clause clarifying no IP transfer.)

                **9. TERM AND SURVIVAL**  
                This Agreement remains valid for **{data.get('confidentiality_term_months')} months** from the Effective Date.  
                Confidentiality obligations survive termination for **{data.get('survival_months')} months**.

                **10. REMEDIES**  
                {data.get('include_injunctive_relief')}

                **11. GOVERNING LAW AND JURISDICTION**  
                This Agreement shall be governed by the laws of **{data.get('governing_law_state')}**, India.  
                Courts in **{data.get('jurisdiction_city')}** shall have jurisdiction.  
                Disputes shall be resolved through **{data.get('dispute_resolution')}**, and where arbitration applies, the seat of arbitration shall be **{data.get('arbitration_city')}**.

                --------------------------------
                SIGNATURE BLOCKS
                --------------------------------

                For **{data.get('company_name')}** (Disclosing Party)  
                Name: __________________________  
                Title: __________________________  
                Signature: ______________________  
                Date: ___________________________

                For **{data.get('counterparty_name')}** (Receiving Party)  
                Name: __________________________  
                Title: __________________________  
                Signature: ______________________  
                Date: ___________________________

                --------------------------------
                FINAL CHECK
                --------------------------------
                - No placeholders should remain
                - No grammatical errors
                - No extra clauses or commentary
                - Professional legal document output only
                """
        
        receiving_party_name = data.get('counterparty_name')
        nda, error = generate_and_save_letter(request, 'nda', prompt, data, receiving_party_name, "contracts", id)
        
        if error:
            return Response({'status': 'error', 'message': error}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'success',
            'nda': json.dumps(nda)
        }, status=status.HTTP_200_OK)

class OnbordingEmployerBrandingGeneatorView(APIView):
    def post(self, request, id=None):
        data = request.data
        prompt = f"""You are an expert HR documentation assistant with strong knowledge of structured employee onboarding and performance planning practices.

            Your task is to generate a professional, structured, and well-formatted **Employee Onboarding & 30-60-90 Day Success Plan**
            using ONLY the data provided in the input fields.

            IMPORTANT RULES (STRICT):
            1. Follow the exact structure, section order, headings, and tone defined in the OUTPUT FORMAT below.
            2. Do NOT add, remove, assume, or infer any information not present in the input fields.
            3. Use a formal, welcoming, and performance-focused corporate tone.
            4. Maintain consistent formatting with bold section headings and clean spacing.
            5. The document must read like an official onboarding success plan prepared by HR and the Reporting Manager.
            6. Do NOT mention variable names, placeholders, or instructions in the final output.
            7. If any optional field is empty, omit that line or section cleanly without breaking formatting.
            8. Output must be clean and ready for direct PDF generation.
            9. Output ONLY the final onboarding document text.

            --------------------------------
            INPUT DATA (FIELDS)
            --------------------------------

            Employee Full Name: {data.get("employee_full_name")}
            Role Title: {data.get("role_title")}
            Department: {data.get("department")}
            Reporting Manager: {data.get('manager_name_title')}
            Start Date: {data.get('start_date')}
            Work Model: {data.get('work_model')}
            Work Location: {data.get('work_location')}
            Seniority Level: {data.get('seniority_level')}

            Role Purpose: {data.get('why_this_role_exists')}
            Top 90-Day Outcomes: {data.get('top_outcomes_90_days')}
            Key Responsibilities: {data.get('key_responsibilities')}
            Key Stakeholders: {data.get('key_stakeholders')}
            Tools & Systems Needed: {data.get('tools_access_needed')}
            Training Topics: {data.get('training_topics')}
            First Week Meetings: {data.get('first_week_meetings')}

            --------------------------------
            OUTPUT FORMAT (MANDATORY)
            --------------------------------

            **ONBOARDING & 30-60-90 DAY SUCCESS PLAN**

            **1. ROLE SNAPSHOT**  
            Employee Name:  
            Role Title:  
            Department:  
            Reporting Manager:  
            Start Date:  
            Work Model:  
            Work Location:  
            Seniority Level:  

            **2. ROLE PURPOSE**  
            (Clear explanation of why this role exists in the organization)

            **3. FIRST 90 DAYS — SUCCESS OUTCOMES**  
            (Summary of the top outcomes expected within the first 90 days)

            **4. KEY RESPONSIBILITIES**  
            (Bullet list of primary responsibilities)

            **5. KEY STAKEHOLDERS TO CONNECT WITH**  
            (List of important individuals, teams, or departments)

            **6. TOOLS & SYSTEM ACCESS REQUIRED**  
            (List of tools, software, or systems required for the role)

            **7. TRAINING & LEARNING PLAN**  
            (List of training topics and knowledge areas for development)

            **8. FIRST WEEK PRIORITY MEETINGS**  
            (List of key meetings or introductions to be scheduled in Week 1)

            **9. 30-60-90 DAY PROGRESSION PLAN**

            **30 DAYS – LEARN & ORIENT**  
            Focus Areas:  
            Expected Contributions:  
            Manager Support:  

            **60 DAYS – CONTRIBUTE & COLLABORATE**  
            Focus Areas:  
            Expected Contributions:  
            Manager Support:  

            **90 DAYS – OWN & DELIVER**  
            Focus Areas:  
            Expected Contributions:  
            Manager Support:  

            Closing statement expressing support, encouragement, and excitement about the employee’s journey with the organization.

            --------------------------------
            FINAL CHECK
            --------------------------------
            - No placeholders should remain  
            - No assumptions beyond provided inputs  
            - No grammatical errors  
            - All sections included in correct order  
            - Professional HR-ready output only  
            """

        
        employee_name = data.get('employee_full_name')
        onboarding_plan, error = generate_and_save_letter(request, 'onboarding', prompt, data, employee_name, "employerbranding", id)
        
        if error:
            return Response({'status': 'error', 'message': error}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'success',
            'onboarding_plan': json.dumps(onboarding_plan)
        }, status=status.HTTP_200_OK)


class EVPBuilderEmployerBrandingGeneatorView(APIView):
    def post(self, request, id=None):
        data = request.data
        prompt = f"""
                You are an expert Employer Branding and HR Communications specialist.

                Your task is to create a compelling, professional, and inspiring **Employee Value Proposition (EVP) Letter**
                using ONLY the information provided in the input fields.

                The final output must be **well-structured, emotionally engaging, and professionally formatted** so it can be directly converted into a PDF document.

                ━━━━━━━━━━━━━━━━━━━━
                🔒 STRICT RULES
                ━━━━━━━━━━━━━━━━━━━━
                1. Use ONLY the details provided in the input fields. Do NOT assume or add extra facts.
                2. Keep the tone inspiring, human, and brand-positive — not overly corporate or robotic.
                3. Write in clear, natural language that appeals to potential candidates.
                4. Structure the document with clean headings and spacing for professional PDF presentation.
                5. Do NOT include placeholders, instructions, or explanations in the final output.
                6. Do NOT mention “AI” anywhere in the letter.

                ━━━━━━━━━━━━━━━━━━━━
                📌 INPUT FIELDS
                ━━━━━━━━━━━━━━━━━━━━
                Company Name: {data.get('company_name')}  
                Industry: {data.get('industry')}  
                Company Stage: {data.get('company_stage')}  
                Location: {data.get('location')}  
                Work Model: {data.get('work_model')}  
                Top 3 Reasons to Join: {data.get('top_3_reasons_to_join')}  
                Growth & Learning Promises: {data.get('growth_learning_promises')}  
                Culture Words: {data.get('culture_words')}  
                Leadership Style: {data.get('leadership_style')}  
                Non-Negotiables: {data.get('non_negotiables')}  
                Target Role Family: {data.get('target_role_family')}

                ━━━━━━━━━━━━━━━━━━━━
                📄 REQUIRED OUTPUT FORMAT
                ━━━━━━━━━━━━━━━━━━━━

                **EVP – [Company Name] – [Target Role Family]**

                **1. EVP STATEMENT**  
                Write a powerful 3–4 sentence opening that introduces the company, its stage, industry, and overall opportunity. Mention the work model and location naturally.

                **2. EVP PILLARS**  
                Create 5–6 short bullet points (each with a bold title + 1 line description) based on:
                - Growth & Learning  
                - Culture  
                - Leadership Style  
                - Impact  
                - Flexibility / Work Model  
                - Recognition or Purpose (if supported by inputs)

                **3. WHAT YOU CAN EXPECT HERE**  
                Write a warm, engaging paragraph describing the day-to-day experience, team environment, leadership approach, and growth opportunities.

                **4. WHO THRIVES HERE**  
                Describe the type of people who will succeed in this environment, aligned with the culture words, leadership style, and non-negotiables.

                **5. TAGLINE OPTIONS**  
                Provide 3 short employer-brand style tagline options aligned with the EVP tone.

                ━━━━━━━━━━━━━━━━━━━━
                🎯 WRITING STYLE
                ━━━━━━━━━━━━━━━━━━━━
                • Inspirational but professional  
                • Human and warm  
                • Clear and benefit-focused  
                • Short paragraphs, easy to read  
                • Suitable for employer branding PDF

                Now generate the complete EVP letter.
                """
        
        evp_letter, error = generate_and_save_letter(request, 'evp', prompt, data, None, 'employerbranding', id)
        
        if error:
            return Response({'status': 'error', 'message': error}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'success',
            'evp_builder': json.dumps(evp_letter)
        }, status=status.HTTP_200_OK)

class EmployerBrandingEmployerBrandingGeneratorView(APIView):
    def post(self, request, id=None):
        data = request.data
        prompt = f"""You are an expert Employer Branding and Talent Marketing content specialist.

                Your task is to generate a professional, engaging, and brand-aligned **Employer Branding Post**
                using ONLY the data provided in the input fields.

                The content must reflect a strong employer value proposition, highlight growth, culture, and opportunities,
                and be suitable for publishing on the specified platform. The final output should be cleanly formatted
                and ready to be exported as a PDF.

                IMPORTANT RULES (STRICT):
                1. Follow the storytelling style and structure similar to a modern employer branding post (like the provided sample PDF).
                2. Do NOT add, remove, or assume any information that is not present in the input fields.
                3. Match the tone exactly as specified in the "Tone" field (e.g., professional, friendly, inspiring, bold).
                4. Adapt writing style and format to suit the "Platform" (LinkedIn = professional narrative, Instagram = short and energetic, etc.).
                5. Respect the "Post_Length" instruction (Short / Medium / Long).
                6. Use natural, human, and warm employer-brand language — NOT like a job description.
                7. Incorporate the "Post_Theme" and "Key_Message" as the central focus of the content.
                8. Use "Proof_Points" to add credibility such as culture, flexibility, learning, career growth, team environment, etc.
                9. End with a strong and motivating "Call_to_Action".
                10. The final output must be clean, well-spaced, and ready for direct PDF conversion.
                11. Do NOT include headings like “INPUT” or “OUTPUT” in the final result.
                12. Do NOT include placeholders, explanations, or variable labels in the final content.

                --------------------------------
                INPUT DATA (FIELDS)
                --------------------------------

                Company Name: {data.get('company_name')}
                Platform: {data.get('platform')}
                Post Type: {data.get('post_type')}
                Tone: {data.get('tone')}
                Post Length: {data.get('post_length')}
                Post Theme: {data.get('post_theme')}
                Target Role/Audience: {data.get('role')}
                Key Message: {data.get('key_message')}
                Proof Points: {data.get('proof_points')}
                Call to Action: {data.get('call_to_action')}

                --------------------------------
                OUTPUT FORMAT (MANDATORY)
                --------------------------------

                Generate a platform-ready Employer Branding Post that:

                • Starts with an engaging opening line aligned with the Post Theme  
                • Highlights how the company supports employee growth, culture, or opportunity  
                • Naturally connects the Key Message with Proof Points  
                • Mentions the Target Role/Audience in a brand-focused way (not as a job description)  
                • Ends with a compelling Call to Action  

                The post should feel inspiring, people-first, and aligned with modern employer branding trends.

                --------------------------------
                FINAL CHECK
                --------------------------------
                - No placeholders should remain  
                - No extra assumptions or added benefits  
                - Tone matches the input  
                - Platform style is respected  
                - Content is engaging and human  
                - Ready-to-publish Employer Branding Post only
                """
        
        post, error = generate_and_save_letter(request, 'branding_post', prompt, data, None, 'employerbranding', id)
        
        if error:
            return Response({'status': 'error', 'message': error}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'success',
            'branding_post': json.dumps(post)
        }, status=status.HTTP_200_OK)

class LetterSettingsView(APIView):
    # permission_classes = [IsAuthenticated]

    def get_company(self, request):
        if hasattr(request.user, 'company'):
            return request.user.company
        return None

    def get(self, request):
        # company = self.get_company(request)
        company = Company.objects.get(id=request.user.company_id)
        if not company:
            return Response({'error': 'Company not found for user'}, status=status.HTTP_404_NOT_FOUND)
        
        settings, created = LetterSettings.objects.get_or_create(company=company)
        serializer = LetterSettingsSerializer(settings)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        # company = self.get_company(request)
        company = Company.objects.get(id=request.user.company_id)
        if not company:
            return Response({'error': 'Company not found for user'}, status=status.HTTP_404_NOT_FOUND)
        
        settings, created = LetterSettings.objects.get_or_create(company=company)
        serializer = LetterSettingsSerializer(settings, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GeneratedLetterView(APIView):
    def get(self,request, id =None):
        if id:
            letter = GeneratedLetter.objects.get(id=id)
            serializer = GeneratedLetterSerializer(letter)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            letters= GeneratedLetter.objects.filter(company=request.user.company_id)
            serializer = GeneratedLetterSerializer(letters, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self,request,id):
        letter = GeneratedLetter.objects.get(id=id)
        letter.delete()
        return Response({'status': 'success', 'message': 'Letter deleted successfully'}, status=status.HTTP_200_OK)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LETTERS BILLING SYSTEM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import razorpay
from decimal import Decimal
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


class LetterCreditPackageListView(APIView):
    """
    GET /letters/billing/packages/
    Returns all active letter credit packages.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        packages = LetterCreditPackage.objects.filter(is_active=True)
        serializer = LetterCreditPackageSerializer(packages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class LetterCreditWalletView(APIView):
    """
    GET /letters/billing/wallet/
    Returns the authenticated company's letter credit wallet balance.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = Company.objects.filter(id=request.user.company_id).first()
        if not company:
            return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)

        wallet, _ = LetterCreditWallet.objects.get_or_create(company=company)
        serializer = LetterCreditWalletSerializer(wallet)
        return Response(serializer.data, status=status.HTTP_200_OK)


class LetterCreditTransactionListView(APIView):
    """
    GET /letters/billing/transactions/
    Returns the credit transaction history for the company.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = Company.objects.filter(id=request.user.company_id).first()
        if not company:
            return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)

        transactions = LetterCreditTransaction.objects.filter(company=company, transaction_type='deduction').order_by('-created')
        serializer = LetterCreditTransactionSerializer(transactions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class LetterCreateOrderView(APIView):
    """
    POST /letters/billing/create-order/
    Body: { "package_id": <int> }
    Creates a Razorpay order for purchasing letter credits.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        package_id = request.data.get('package_id')
        if not package_id:
            return Response({'error': 'package_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            package = LetterCreditPackage.objects.get(id=package_id, is_active=True)
        except LetterCreditPackage.DoesNotExist:
            return Response({'error': 'Credit package not found or inactive'}, status=status.HTTP_404_NOT_FOUND)

        # Price including 18% GST
        final_price = Decimal(str(package.effective_price())) * Decimal('1.18')
        amount_paise = int(final_price * 100)  # Razorpay expects paise as integer

        RAZORPAY_MODE = getattr(settings, 'RAZORPAY_MODE', 'test')
        if RAZORPAY_MODE == 'live':
            RAZORPAY_KEY_ID = settings.RAZORPAY_LIVE_MODE_KEY_ID
            RAZORPAY_KEY_SECRET = settings.RAZORPAY_LIVE_MODE_KEY_SECRET
        else:
            RAZORPAY_KEY_ID = settings.RAZORPAY_TEST_MODE_KEY_ID
            RAZORPAY_KEY_SECRET = settings.RAZORPAY_TEST_MODE_KEY_SECRET

        try:
            rzp_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
            order = rzp_client.order.create({
                'amount': amount_paise,
                'currency': 'INR',
                'payment_capture': '1',
            })
        except Exception as e:
            return Response({'error': f'Razorpay error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'razorpay_order_id': order['id'],
            'razorpay_key_id': RAZORPAY_KEY_ID,
            'amount': float(final_price),
            'currency': 'INR',
            'package': LetterCreditPackageSerializer(package).data,
        }, status=status.HTTP_201_CREATED)


@method_decorator(csrf_exempt, name='dispatch')
class LetterPaymentSuccessView(APIView):
    """
    POST /letters/billing/payment-success/
    Body: { razorpay_order_id, razorpay_payment_id, razorpay_signature, package_id }
    Verifies payment, adds credits to wallet, logs transaction.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_signature = data.get('razorpay_signature')
        package_id = data.get('package_id')

        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature, package_id]):
            return Response(
                {'error': 'razorpay_order_id, razorpay_payment_id, razorpay_signature and package_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            package = LetterCreditPackage.objects.get(id=package_id)
        except LetterCreditPackage.DoesNotExist:
            return Response({'error': 'Credit package not found'}, status=status.HTTP_404_NOT_FOUND)

        RAZORPAY_MODE = getattr(settings, 'RAZORPAY_MODE', 'test')
        if RAZORPAY_MODE == 'live':
            RAZORPAY_KEY_ID = settings.RAZORPAY_LIVE_MODE_KEY_ID
            RAZORPAY_KEY_SECRET = settings.RAZORPAY_LIVE_MODE_KEY_SECRET
        else:
            RAZORPAY_KEY_ID = settings.RAZORPAY_TEST_MODE_KEY_ID
            RAZORPAY_KEY_SECRET = settings.RAZORPAY_TEST_MODE_KEY_SECRET

        rzp_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

        try:
            rzp_client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature,
            })
        except Exception:
            return Response({'error': 'Payment verification failed. Invalid signature.'}, status=status.HTTP_400_BAD_REQUEST)

        # Verified – credit the wallet
        company = Company.objects.filter(id=request.user.company_id).first()
        if not company:
            return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)

        wallet, _ = LetterCreditWallet.objects.get_or_create(company=company)
        wallet.total_credits += package.credits
        wallet.save()

        final_price = Decimal(str(package.effective_price())) * Decimal('1.18')

        LetterCreditTransaction.objects.create(
            company=company,
            wallet=wallet,
            transaction_type='purchase',
            credits=package.credits,
            package=package,
            razorpay_order_id=razorpay_order_id,
            razorpay_payment_id=razorpay_payment_id,
            razorpay_signature=razorpay_signature,
            amount_paid=final_price,
        )

        return Response({
            'status': 'success',
            'message': f'{package.credits} added to your wallet.',
            'wallet': LetterCreditWalletSerializer(wallet).data,
        }, status=status.HTTP_200_OK)


class ToolRequestView(APIView):
    """
    API endpoint to request a tool and send email notification to superuser
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def post(self, request, format=None):
        data = request.data
        
        # Validate required fields
        tool_name = data.get('tool_name', '').strip()
        description = data.get('description', '').strip()
        category = data.get('category', '').strip()
        use_case = data.get('use_case', '').strip()
        
        if not tool_name or not description or not category:
            return Response({
                'status': 'error',
                'message': 'Tool name, description, and category are required fields.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create tool request instance
        from .models import ToolRequest
        tool_request = ToolRequest.objects.create(
            tool_name=tool_name,
            description=description,
            category=category,
            use_case=use_case,
            requested_by=request.user
        )
        
        return Response({
            'status': 'success',
            'message': 'Tool request submitted successfully. Admin will be notified.',
            'request': ToolRequestSerializer(tool_request).data
        }, status=status.HTTP_201_CREATED)



class ApiIntegrationRequestApi(APIView):
    """
    API for API Integration Requests
    
    GET: Retrieve all API integration requests
    POST: Create a new API integration request (sends email to superuser)
    """
    
    def get(self, request):
        """Get all API integration requests"""
        try:
            requests = ApiIntegrationRequest.objects.all().order_by('created')
            serializer_data = ApiIntegrationRequestSerializer(requests, many=True)
            return Response({
                'code': 200,
                'msg': 'Success',
                'data': serializer_data.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'code': 500,
                'msg': f'Error retrieving requests: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Create a new API integration request and notify superusers"""
        try:
            data = request.data
            
            # Validate required fields
            platform = data.get('platform')
            ai_tools = data.get('ai_tools', [])
            note = data.get('note', '').strip()
            
            # Handle platform being "null" string or None
            if platform == "null" or platform is None:
                platform = None
            else:
                platform = str(platform).strip() if platform else None
            
            # Ensure ai_tools is a list
            if not isinstance(ai_tools, list):
                ai_tools = [ai_tools] if ai_tools else []
            
            # Filter out empty/null values from ai_tools
            ai_tools = [tool for tool in ai_tools if tool]
            
            if not platform and not ai_tools:
                return Response({
                    'code': 400,
                    'msg': 'Either platform or ai_tools must be provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create the API integration request
            api_request = ApiIntegrationRequest.objects.create(
                platform=platform,
                ai_tools=ai_tools,
                note=note if note else None
            )
            
            # Send email to superusers
            superuser_emails = list(Account.objects.filter(
                is_superuser=True, 
                is_active=True
            ).values_list('email', flat=True))
            
            if superuser_emails:
                mailer = ApiIntegrationRequestMailer(api_request, superuser_emails)
                mailer.start()
            
            # Return the created request data
            serializer_data = ApiIntegrationRequestSerializer(api_request)
            return Response({
                'code': 201,
                'msg': 'API integration request created successfully',
                'data': serializer_data.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                'code': 500,
                'msg': f'Error creating request: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)