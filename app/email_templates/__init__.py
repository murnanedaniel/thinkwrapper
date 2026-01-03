"""
Email templates for ThinkWrapper Newsletter Generator.

This module provides HTML email templates for various use cases.
"""

from typing import Dict, Any


def get_newsletter_template(subject: str, content: str, **kwargs) -> str:
    """
    Generate a professional newsletter email template.
    
    Args:
        subject: Email subject line
        content: Main newsletter content (can include HTML)
        **kwargs: Additional template variables
        
    Returns:
        str: Complete HTML email
    """
    # Extract optional parameters
    preheader = kwargs.get('preheader', 'Your newsletter update')
    unsubscribe_link = kwargs.get('unsubscribe_link', '#')
    
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
        }}
        .email-container {{
            max-width: 600px;
            margin: 20px auto;
            background-color: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .email-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #ffffff;
            padding: 30px 20px;
            text-align: center;
        }}
        .email-header h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: 600;
        }}
        .email-body {{
            padding: 30px 20px;
        }}
        .email-content {{
            margin-bottom: 20px;
        }}
        .email-content h2 {{
            color: #667eea;
            font-size: 20px;
            margin-top: 20px;
            margin-bottom: 10px;
        }}
        .email-content p {{
            margin: 10px 0;
        }}
        .email-footer {{
            background-color: #f8f9fa;
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #6c757d;
            border-top: 1px solid #e9ecef;
        }}
        .email-footer a {{
            color: #667eea;
            text-decoration: none;
        }}
        .preheader {{
            display: none;
            max-width: 0;
            max-height: 0;
            overflow: hidden;
            mso-hide: all;
        }}
    </style>
</head>
<body>
    <span class="preheader">{preheader}</span>
    <div class="email-container">
        <div class="email-header">
            <h1>ThinkWrapper Newsletter</h1>
        </div>
        <div class="email-body">
            <div class="email-content">
                {content}
            </div>
        </div>
        <div class="email-footer">
            <p>&copy; 2024 ThinkWrapper. All rights reserved.</p>
            <p>
                <a href="{unsubscribe_link}">Unsubscribe</a> from this newsletter
            </p>
        </div>
    </div>
</body>
</html>
    """.strip()


def get_welcome_template(user_name: str = "Valued Subscriber") -> str:
    """
    Generate a welcome email template.
    
    Args:
        user_name: Name of the new subscriber
        
    Returns:
        str: Complete HTML email
    """
    content = f"""
        <h2>Welcome to ThinkWrapper!</h2>
        <p>Hi {user_name},</p>
        <p>Thank you for subscribing to our newsletter. We're excited to have you on board!</p>
        <p>You'll receive regular updates about:</p>
        <ul>
            <li>Latest AI and technology trends</li>
            <li>Curated insights and analysis</li>
            <li>Exclusive content and resources</li>
        </ul>
        <p>Stay curious and keep learning!</p>
        <p>Best regards,<br>The ThinkWrapper Team</p>
    """
    
    return get_newsletter_template(
        subject="Welcome to ThinkWrapper Newsletter",
        content=content,
        preheader="Welcome to ThinkWrapper! Get ready for great content."
    )


def get_test_template() -> str:
    """
    Generate a simple test email template.
    
    Returns:
        str: Complete HTML email for testing
    """
    content = """
        <h2>Test Email</h2>
        <p>This is a test email to verify SendGrid integration.</p>
        <p>If you received this email, the SendGrid API is configured correctly.</p>
    """
    
    return get_newsletter_template(
        subject="Test Email - SendGrid Integration",
        content=content,
        preheader="Testing SendGrid email delivery"
    )
