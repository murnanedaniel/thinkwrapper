#!/usr/bin/env python3
"""
Demo script for the Newsletter Synthesis Service

This script demonstrates the end-to-end functionality of the newsletter
synthesis service, including content generation, rendering, and previewing
the output.
"""

import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.newsletter_synthesis import (
    NewsletterSynthesizer,
    NewsletterRenderer,
    NewsletterConfig
)


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def demo_content_collection():
    """Demonstrate content collection."""
    print_section("Demo 1: Content Collection")
    
    synthesizer = NewsletterSynthesizer()
    content_items = synthesizer.collect_source_content(newsletter_id=1)
    
    print(f"Collected {len(content_items)} content items:")
    for i, item in enumerate(content_items, 1):
        print(f"\n{i}. {item['title']}")
        print(f"   Source: {item['source']}")
        print(f"   Summary: {item['summary']}")
        if 'url' in item:
            print(f"   URL: {item['url']}")


def demo_newsletter_synthesis():
    """Demonstrate newsletter synthesis."""
    print_section("Demo 2: Newsletter Synthesis")
    
    synthesizer = NewsletterSynthesizer()
    
    # Collect content
    content_items = synthesizer.collect_source_content(newsletter_id=1)
    
    print("Synthesizing newsletter...")
    print("Note: Using fallback content generation (OpenAI key not configured)")
    print()
    
    # Synthesize (will use fallback since no API key in demo)
    result = synthesizer.synthesize_newsletter(
        topic="Technology Weekly",
        content_items=content_items,
        style="professional"
    )
    
    print(f"Subject: {result['subject']}")
    print(f"\nContent Preview (first 300 chars):")
    print(result['content'][:300] + "...")


def demo_html_rendering():
    """Demonstrate HTML rendering."""
    print_section("Demo 3: HTML Rendering")
    
    renderer = NewsletterRenderer()
    
    sample_content = {
        'subject': 'Technology Weekly - Demo Edition',
        'content': """# Welcome to Technology Weekly

This week has been packed with exciting developments in the tech world.

## Top Stories

### AI Breakthroughs
Researchers have made significant progress in natural language processing.

### Cloud Computing
Major cloud providers announced new services and pricing updates.

## Conclusion

Thank you for reading this week's newsletter!"""
    }
    
    html_output = renderer.render_html(sample_content)
    
    print("HTML Output Generated:")
    print(f"Length: {len(html_output)} characters")
    print("\nPreview (first 500 chars):")
    print(html_output[:500] + "...")
    
    # Save to file for viewing
    output_file = "/tmp/demo_newsletter.html"
    with open(output_file, 'w') as f:
        f.write(html_output)
    print(f"\nFull HTML saved to: {output_file}")


def demo_text_rendering():
    """Demonstrate plain text rendering."""
    print_section("Demo 4: Plain Text Rendering")
    
    renderer = NewsletterRenderer()
    
    sample_content = {
        'subject': 'Technology Weekly - Demo Edition',
        'content': """# Welcome to Technology Weekly

This week has been packed with exciting developments.

## Top Stories

Latest updates from the tech industry.

Thank you for reading!"""
    }
    
    text_output = renderer.render_plain_text(sample_content)
    
    print("Plain Text Output:")
    print(text_output)
    
    # Save to file
    output_file = "/tmp/demo_newsletter.txt"
    with open(output_file, 'w') as f:
        f.write(text_output)
    print(f"\nFull text saved to: {output_file}")


def demo_configuration():
    """Demonstrate configuration management."""
    print_section("Demo 5: Configuration Management")
    
    # Create default configuration
    config = NewsletterConfig()
    print("Default Configuration:")
    for key, value in config.to_dict().items():
        print(f"  {key}: {value}")
    
    # Update configuration
    print("\nUpdating configuration...")
    config.from_dict({
        'schedule': 'daily',
        'delivery_format': 'both',
        'style': 'casual',
        'max_content_items': 15
    })
    
    print("\nUpdated Configuration:")
    for key, value in config.to_dict().items():
        print(f"  {key}: {value}")
    
    # Validate
    is_valid, error = config.validate()
    print(f"\nValidation: {'✓ PASSED' if is_valid else '✗ FAILED'}")
    if error:
        print(f"Error: {error}")


def demo_on_demand_generation():
    """Demonstrate on-demand newsletter generation."""
    print_section("Demo 6: On-Demand Generation")
    
    synthesizer = NewsletterSynthesizer()
    
    print("Generating newsletter on demand...")
    print("Topic: AI and Machine Learning")
    print("Style: Technical")
    print()
    
    result = synthesizer.generate_on_demand(
        newsletter_id=1,
        topic="AI and Machine Learning",
        style="technical"
    )
    
    if result['success']:
        print("✓ Generation Successful!")
        print(f"\nSubject: {result['subject']}")
        print(f"Content Items: {result['content_items_count']}")
        print(f"Generated At: {result['generated_at']}")
        print(f"Style: {result['style']}")
        print(f"\nContent Preview (first 300 chars):")
        print(result['content'][:300] + "...")
    else:
        print(f"✗ Generation Failed: {result['error']}")


def demo_full_workflow():
    """Demonstrate complete workflow."""
    print_section("Demo 7: Complete Workflow")
    
    print("Running complete newsletter generation workflow...")
    print()
    
    # Step 1: Initialize services
    print("1. Initializing services...")
    synthesizer = NewsletterSynthesizer()
    renderer = NewsletterRenderer()
    
    # Step 2: Generate newsletter
    print("2. Generating newsletter content...")
    result = synthesizer.generate_on_demand(
        newsletter_id=1,
        topic="Weekly Tech Digest",
        style="professional"
    )
    
    if not result['success']:
        print(f"   ✗ Failed: {result['error']}")
        return
    
    print(f"   ✓ Generated: {result['subject']}")
    
    # Step 3: Render in both formats
    print("3. Rendering newsletter...")
    content = {
        'subject': result['subject'],
        'content': result['content']
    }
    
    html_output = renderer.render_html(content)
    text_output = renderer.render_plain_text(content)
    
    print(f"   ✓ HTML rendered ({len(html_output)} chars)")
    print(f"   ✓ Text rendered ({len(text_output)} chars)")
    
    # Step 4: Save outputs
    print("4. Saving outputs...")
    html_file = "/tmp/complete_newsletter.html"
    text_file = "/tmp/complete_newsletter.txt"
    
    with open(html_file, 'w') as f:
        f.write(html_output)
    with open(text_file, 'w') as f:
        f.write(text_output)
    
    print(f"   ✓ HTML saved to: {html_file}")
    print(f"   ✓ Text saved to: {text_file}")
    
    print("\n✓ Complete workflow finished successfully!")


def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print("  Newsletter Synthesis Service - Demo Script")
    print("  " + str(datetime.now()))
    print("=" * 70)
    
    try:
        # Run each demo
        demo_content_collection()
        demo_newsletter_synthesis()
        demo_html_rendering()
        demo_text_rendering()
        demo_configuration()
        demo_on_demand_generation()
        demo_full_workflow()
        
        # Summary
        print_section("Demo Complete")
        print("All demos completed successfully!")
        print("\nGenerated files:")
        print("  - /tmp/demo_newsletter.html")
        print("  - /tmp/demo_newsletter.txt")
        print("  - /tmp/complete_newsletter.html")
        print("  - /tmp/complete_newsletter.txt")
        print("\nYou can open these files to view the rendered newsletters.")
        
    except Exception as e:
        print(f"\n✗ Error during demo: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
