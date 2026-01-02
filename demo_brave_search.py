#!/usr/bin/env python
"""
Demo script for Brave Search API integration.

This script demonstrates how to use the Brave Search API integration
in the ThinkWrapper application.

Usage:
    python demo_brave_search.py
"""

from app import create_app, services


def main():
    """Run demo of Brave Search integration."""
    # Create Flask app context
    app = create_app({"TESTING": True})

    with app.app_context():
        print("=" * 70)
        print("Brave Search API Integration Demo")
        print("=" * 70)
        print()

        # Demo 1: Search without API key (uses mock fallback)
        print("Demo 1: Search without API key (Mock Fallback)")
        print("-" * 70)
        results = services.search_brave("artificial intelligence", count=3)
        display_results(results)
        print()

        # Demo 2: Demonstrate different result counts
        print("Demo 2: Requesting different number of results")
        print("-" * 70)
        results = services.search_brave("machine learning", count=5)
        display_results(results)
        print()

        # Demo 3: Newsletter workflow integration
        print("Demo 3: Newsletter Workflow Integration")
        print("-" * 70)
        newsletter_topic = "Python programming tutorials"
        print(f"Newsletter Topic: {newsletter_topic}")
        print()

        results = services.search_brave(newsletter_topic, count=3)

        if results["success"]:
            print("✅ Search successful! Found relevant articles:")
            print()

            for i, result in enumerate(results["results"], 1):
                print(f"{i}. {result['title']}")
                print(f"   URL: {result['url']}")
                print(f"   Summary: {result['description'][:100]}...")
                print()

            print(f"These {len(results['results'])} articles can be used to:")
            print("  • Generate newsletter content with real references")
            print("  • Provide readers with valuable external resources")
            print("  • Keep newsletter content current and relevant")
        else:
            print(f"❌ Search failed: {results['error']}")

        print()
        print("=" * 70)
        print("Demo complete!")
        print()
        print("To use Brave Search API with real data:")
        print("  1. Get API key from https://brave.com/search/api/")
        print("  2. Set environment variable: export BRAVE_SEARCH_API_KEY=your-key")
        print("  3. Re-run this demo to see real search results")
        print("=" * 70)


def display_results(results):
    """Display search results in a formatted way."""
    print(f"Source: {results['source']}")
    print(f"Query: {results['query']}")
    print(f"Success: {results['success']}")
    print(f"Total Results: {results['total_results']}")
    print()

    if results["success"] and results["results"]:
        print("Results:")
        for i, result in enumerate(results["results"], 1):
            print(f"  {i}. {result['title']}")
            print(f"     {result['url']}")
    elif not results["success"]:
        print(f"Error: {results.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
