import os
from openai import OpenAI
from flask import current_app
import sendgrid
from sendgrid.helpers.mail import Mail, From, To, Content


# Configure OpenAI client (lazy initialization to avoid errors during testing)
def get_openai_client():
    """Get or create OpenAI client instance."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        return OpenAI(api_key=api_key)
    return None


def generate_newsletter_content(topic, style="concise"):
    """
    Generate newsletter content using OpenAI.

    Args:
        topic (str): The subject of the newsletter
        style (str): Style descriptor for the content

    Returns:
        dict: Generated content with subject and body
    """
    prompt = f"""
    Create a newsletter about {topic}.
    Style: {style}
    Include:
    - An engaging subject line
    - 3-5 interesting segments with links and takeaways
    - A brief conclusion
    """

    try:
        # Get OpenAI client
        client = get_openai_client()
        if not client:
            current_app.logger.error("OpenAI API key not configured")
            return None

        # Using OpenAI v1.0+ API
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a newsletter writer."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1500,
            temperature=0.7,
        )

        # Process response to extract subject and content
        content = response.choices[0].message.content.strip()

        # Simple extraction of subject line (first line)
        lines = content.split("\n")
        subject = lines[0]
        body = "\n".join(lines[1:])

        return {"subject": subject, "content": body}
    except Exception as e:
        current_app.logger.error(f"OpenAI generation error: {str(e)}")
        return None


def send_email(to_email, subject, content):
    """
    Send email using SendGrid

    Args:
        to_email (str): Recipient email
        subject (str): Email subject line
        content (str): HTML content of the email

    Returns:
        bool: Success status
    """
    sg_api_key = os.environ.get("SENDGRID_API_KEY")
    if not sg_api_key:
        current_app.logger.error("SendGrid API key not configured")
        return False

    try:
        sg = sendgrid.SendGridAPIClient(api_key=sg_api_key)
        from_email_obj = From("newsletter@thinkwrapper.com")
        to_email_obj = To(to_email)
        content_obj = Content("text/html", content)
        mail = Mail(from_email_obj, to_email_obj, subject, content_obj)

        response = sg.client.mail.send.post(request_body=mail.get())
        return response.status_code in [200, 202]
    except Exception as e:
        current_app.logger.error(f"Email sending error: {str(e)}")
        return False


def verify_paddle_webhook(data, signature):
    """
    Verify Paddle webhook signature

    Args:
        data (dict): The webhook data
        signature (str): The webhook signature

    Returns:
        bool: Whether the signature is valid
    """
    # This is a placeholder for actual Paddle signature verification
    # In production, implement proper signature verification
    # following Paddle documentation
    return True
