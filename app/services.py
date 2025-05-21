import os
import openai # Keep this for now, might be used elsewhere or for older models
from openai import OpenAI # Import the new client
from flask import current_app
import sendgrid
from sendgrid.helpers.mail import Mail, Email, Content
import hashlib # For HMAC
import hmac    # For HMAC

# Configure OpenAI client
# openai.api_key = os.environ.get('OPENAI_API_KEY') # Old way
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

def generate_newsletter_content(topic, style="concise"):
    """
    Generate newsletter content using OpenAI.
    
    Args:
        topic (str): The subject of the newsletter
        style (str): Style descriptor for the content
        
    Returns:
        dict: Generated content with subject and body or None on error
    """
    # Ensure API key is present
    if not client.api_key:
        current_app.logger.error("OpenAI API key not configured.")
        return None

    prompt_content = f"""
    Create a newsletter about {topic}.
    Style: {style}.
    The newsletter should have:
    1. An engaging subject line (as the first line of your response).
    2. The main body of the newsletter (everything after the first line), consisting of 3-5 interesting segments. Each segment should ideally include links (use placeholders like [link_url]) and key takeaways.
    3. A brief conclusion.
    
    Example of a segment:
    **Segment Title**
    Some interesting text about the segment... [link_to_source].
    *Takeaway: A key point from this segment.*
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", # Using a common chat model
            messages=[
                {"role": "system", "content": "You are a newsletter generation assistant."},
                {"role": "user", "content": prompt_content}
            ],
            max_tokens=1500,
            temperature=0.7
        )
        
        # Process response to extract subject and content
        full_content = response.choices[0].message.content.strip()
        
        lines = full_content.split('\n', 1) # Split only on the first newline
        subject = lines[0].strip()
        body = lines[1].strip() if len(lines) > 1 else ""
        
        return {
            'subject': subject,
            'content': body
        }
    except Exception as e:
        current_app.logger.error(f"OpenAI generation error: {str(e)}")
        return None

def send_email(to_email_address: str, subject: str, html_content: str):
    """
    Send email using SendGrid
    
    Args:
        to_email_address (str): Recipient email
        subject (str): Email subject line
        html_content (str): HTML content of the email
        
    Returns:
        bool: Success status
    """
    sg_api_key = os.environ.get('SENDGRID_API_KEY')
    if not sg_api_key:
        current_app.logger.error("SendGrid API key not configured")
        return False
        
    # This should be a verified sender in your SendGrid account
    from_email_address = "newsletter@thinkwrapper.com" 

    message = Mail(
        from_email=from_email_address,
        to_emails=to_email_address,
        subject=subject,
        html_content=html_content
    )
    
    try:
        sg = sendgrid.SendGridAPIClient(api_key=sg_api_key)
        response = sg.send(message)
        # Successful status codes for v3 are 200, 201, 202. 202 is typically for accepted for delivery.
        return response.status_code in [200, 201, 202]
    except Exception as e:
        # Log the full exception for better debugging if it's not a SendGrid specific one
        if hasattr(e, 'body'): # SendGridAPIErrors often have a body attribute
            current_app.logger.error(f"SendGrid API Error: {e.status_code} {e.body} - {str(e)}")
        else:
            current_app.logger.error(f"Email sending error: {str(e)}")
        return False

def verify_paddle_webhook(request_data_raw: bytes, signature_header: str) -> bool:
    """
    Verify Paddle Billing webhook signature using HMAC-SHA256.
    Assumes Paddle Billing (not Paddle Classic).

    Args:
        request_data_raw (bytes): The raw request body.
        signature_header (str): The content of the 'Paddle-Signature' header.
                                Example: "ts=1678736028;h1=...."

    Returns:
        bool: Whether the signature is valid.
    """
    webhook_secret = os.environ.get('PADDLE_WEBHOOK_SECRET')
    if not webhook_secret:
        current_app.logger.error("Paddle webhook secret not configured.")
        return False
    if not signature_header:
        current_app.logger.warning("Missing Paddle-Signature header for webhook.")
        return False

    try:
        # The signature header is a string like "ts=timestamp;h1=hash_value"
        # Parse the timestamp (ts) and hash (h1) from the header
        parts = {p.split('=')[0]: p.split('=')[1] for p in signature_header.split(';')}
        timestamp = parts.get('ts')
        received_hash = parts.get('h1')

        if not timestamp or not received_hash:
            current_app.logger.warning("Paddle-Signature header missing 'ts' or 'h1'.")
            return False

        # Prepare the signed payload string: timestamp + '.' + raw_request_body
        signed_payload = f"{timestamp}.{request_data_raw.decode('utf-8')}"

        # Calculate the expected hash
        computed_hash = hmac.new(
            webhook_secret.encode('utf-8'),
            signed_payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        # Compare the computed hash with the received hash
        if hmac.compare_digest(computed_hash, received_hash):
            return True
        else:
            current_app.logger.warning("Paddle webhook signature mismatch.")
            return False
            
    except Exception as e:
        current_app.logger.error(f"Error verifying Paddle webhook signature: {str(e)}")
        return False 