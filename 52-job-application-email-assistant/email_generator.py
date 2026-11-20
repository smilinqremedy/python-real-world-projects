"""
Email template compilation and substitution engine.
"""
import re


class EmailGenerator:
    DEFAULT_DEFAULTS = {
        "company": "the Company",
        "job_title": "Open Role",
        "recruiter_name": "Hiring Manager",
        "candidate_name": "Applicant",
        "candidate_skills": "Python, SQL, System Architecture",
        "years_experience": "4",
        "candidate_email": "applicant@example.com",
        "candidate_phone": "+2348000000000",
    }

    @classmethod
    def compile_template(cls, template_str: str, context: dict) -> str:
        """Replace placeholders {variable} with corresponding values from context."""
        merged_context = cls.DEFAULT_DEFAULTS.copy()
        if context:
            for k, v in context.items():
                if v is not None:
                    merged_context[k] = str(v)

        def replace_match(match):
            key = match.group(1).strip()
            return merged_context.get(key, match.group(0))

        return re.sub(r"\{([a-zA-Z0-9_]+)\}", replace_match, template_str)

    @classmethod
    def generate_application_email(cls, subject_template: str, body_template: str, context: dict) -> dict:
        """Generate subject and body strings from templates."""
        subject = cls.compile_template(subject_template, context)
        body = cls.compile_template(body_template, context)
        return {
            "subject": subject,
            "body": body,
            "recipient_email": context.get("recipient_email", ""),
            "company": context.get("company", ""),
            "job_title": context.get("job_title", ""),
        }
