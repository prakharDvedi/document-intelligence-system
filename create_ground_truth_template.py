#!/usr/bin/env python3
"""
Ground Truth Template Generator

This script helps create a template for ground truth data
that can be used to evaluate the Document Intelligence model.

Run this to see the expected format for your ground truth JSON file.
"""

import json
from pathlib import Path

def create_ground_truth_template():
    """Create a template for ground truth data"""

    template = {
        "metadata": {
            "collection_name": "Collection 1",
            "persona": "Data Analyst",
            "job_to_be_done": "Analyze quarterly sales reports and extract key performance metrics",
            "document_count": 3,
            "input_documents": [
                "South of France - Cities.pdf",
                "South of France - Cuisine.pdf",
                "South of France - History.pdf"
            ]
        },
        "extracted_sections": [
            {
                "section_title": "Sales Performance Q1 2024",
                "document": "quarterly_report.pdf",
                "page_number": 1,
                "word_count": 245,
                "relevance_score": 0.95,
                "content": "Q1 sales showed a 15% increase compared to last year..."
            },
            {
                "section_title": "Key Performance Indicators",
                "document": "kpi_dashboard.pdf",
                "page_number": 2,
                "word_count": 180,
                "relevance_score": 0.87,
                "content": "Customer acquisition cost decreased by 12%..."
            },
            {
                "section_title": "Market Analysis",
                "document": "market_report.pdf",
                "page_number": 3,
                "word_count": 320,
                "relevance_score": 0.76,
                "content": "Market share increased to 23% in the target segment..."
            }
        ],
        "statistics": {
            "total_sections_found": 15,
            "sections_included": 10,
            "subsections_included": 5,
            "total_words_analyzed": 2500,
            "average_relevance_score": 0.73,
            "max_relevance_score": 0.95,
            "min_relevance_score": 0.45
        }
    }

    # Save template
    with open('ground_truth_template.json', 'w') as f:
        json.dump(template, f, indent=2)

    print("📄 Ground Truth Template Created!")
    print("File: ground_truth_template.json")
    print("\n" + "="*60)
    print("GROUND TRUTH FORMAT EXPLANATION")
    print("="*60)
    print("""
Your ground truth JSON should contain:

1. metadata: Basic info about the collection and analysis setup
2. extracted_sections: Array of sections with their expected relevance scores
3. statistics: Summary statistics (optional, used for comparison)

For each section in extracted_sections, include:
- section_title: The title/name of the section
- document: PDF filename
- page_number: Page where section appears
- word_count: Approximate word count
- relevance_score: Expected relevance (0.0 to 1.0)
- content: The actual content (optional)

The evaluation will compare:
- Which sections your model extracts vs. ground truth
- How well relevance scores match
- Overall accuracy, recall, and F1 score
    """)

    print("\n" + "="*60)
    print("HOW TO USE YOUR EXISTING DATA")
    print("="*60)
    print("""
If you have existing output files from your system:

1. Take the JSON output from your model
2. Manually review and adjust the relevance_score values
3. Remove any sections that shouldn't be considered relevant
4. Add any missing sections that should be relevant
5. Save as ground_truth_[collection_name].json

Example workflow:
1. Run your model on Collection 1
2. Get the output JSON
3. Manually curate it to create perfect ground truth
4. Use for evaluation: python evaluation.py "Collection 1/PDFs" ground_truth_collection_1.json "Data Analyst"
    """)

if __name__ == "__main__":
    create_ground_truth_template()