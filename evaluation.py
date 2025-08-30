#!/usr/bin/env python3
"""
Document Intelligence Model Evaluation Script

This script evaluates the performance of the document intelligence system
by comparing model predictions against ground truth data.

Metrics calculated:
- Accuracy: Overall correctness of predictions
- Recall: Ability to find relevant sections
- F1 Score: Harmonic mean of precision and recall
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
import pandas as pd
from sklearn.metrics import accuracy_score, recall_score, f1_score, precision_score

# Add src to path
sys.path.append('src')

from src.document_processor import DocumentProcessor
from src.persona_analyzer import PersonaAnalyzer
from src.relevance_scorer import RelevanceScorer
from src.output_formatter import OutputFormatter


class ModelEvaluator:
    def __init__(self):
        """Initialize the evaluator with model components"""
        self.doc_processor = DocumentProcessor()
        self.persona_analyzer = PersonaAnalyzer()
        self.relevance_scorer = RelevanceScorer()
        self.output_formatter = OutputFormatter()

    def load_ground_truth(self, ground_truth_file: str) -> Dict[str, Any]:
        """Load ground truth data from JSON file"""
        with open(ground_truth_file, 'r') as f:
            return json.load(f)

    def process_documents(self, pdf_folder: str, persona_role: str, job_task: str) -> Dict[str, Any]:
        """Process documents using the model (same as app.py)"""
        # Load documents
        documents = self.doc_processor.load_pdfs(pdf_folder)

        if not documents:
            raise ValueError("No PDF documents found")

        # Analyze persona and job requirements FIRST
        persona_context = self.persona_analyzer.analyze_persona(
            {'role': persona_role},
            {'task': job_task}
        )

        # Extract sections with persona context
        all_sections = []
        for doc in documents:
            sections = self.doc_processor.extract_sections(doc, persona_context=persona_context)
            all_sections.extend(sections)

        if not all_sections:
            raise ValueError("No sections could be extracted")

        # Score and rank sections
        ranked_sections = self.relevance_scorer.score_sections(all_sections, persona_context)

        # Extract subsections
        subsections = self.doc_processor.extract_subsections(ranked_sections[:10])

        # Format output
        input_config = {
            'persona': {'role': persona_role},
            'job_to_be_done': {'task': job_task},
            'documents': [{'filename': doc['filename']} for doc in documents]
        }

        return self.output_formatter.format_output(input_config, ranked_sections, subsections, 0)

    def evaluate_predictions(self, predictions: Dict[str, Any], ground_truth: Dict[str, Any]) -> Dict[str, float]:
        """
        Evaluate model predictions against ground truth

        Returns metrics dictionary with accuracy, recall, f1_score
        """
        pred_sections = predictions.get('extracted_sections', [])
        gt_sections = ground_truth.get('extracted_sections', [])

        # Create mapping of section titles to scores
        pred_scores = {section['section_title']: section['relevance_score'] for section in pred_sections}
        gt_scores = {section['section_title']: section['relevance_score'] for section in gt_sections}

        # Find common sections (exact match + partial match)
        common_sections = set()

        # First, try exact matches
        exact_matches = set(pred_scores.keys()) & set(gt_scores.keys())
        common_sections.update(exact_matches)

        # Then, try partial matches for sections that weren't exact matches
        for pred_title in pred_scores.keys():
            if pred_title not in exact_matches:
                for gt_title in gt_scores.keys():
                    if gt_title not in exact_matches:
                        # Check for partial matches
                        if self._are_titles_similar(pred_title, gt_title):
                            common_sections.add((pred_title, gt_title))
                            break

        if not common_sections:
            print("WARNING: No common sections found between predictions and ground truth")
            return {
                'accuracy': 0.0,
                'recall': 0.0,
                'f1_score': 0.0,
                'common_sections': 0,
                'total_predicted': len(pred_sections),
                'total_ground_truth': len(gt_sections)
            }

        # Prepare data for metrics calculation
        y_true = []
        y_pred = []

        for section_title in common_sections:
            # Convert scores to binary classification (relevant/not relevant)
            # Using 0.5 as threshold
            gt_relevant = 1 if gt_scores[section_title] >= 0.5 else 0
            pred_relevant = 1 if pred_scores[section_title] >= 0.5 else 0

            y_true.append(gt_relevant)
            y_pred.append(pred_relevant)

        # Calculate metrics
        accuracy = accuracy_score(y_true, y_pred)
        recall = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)

        return {
            'accuracy': accuracy,
            'recall': recall,
            'f1_score': f1,
            'common_sections': len(common_sections),
            'total_predicted': len(pred_sections),
            'total_ground_truth': len(gt_sections)
        }

    def detailed_comparison(self, predictions: Dict[str, Any], ground_truth: Dict[str, Any]) -> pd.DataFrame:
        """Create detailed comparison DataFrame"""
        pred_sections = predictions.get('extracted_sections', [])
        gt_sections = ground_truth.get('extracted_sections', [])

        pred_dict = {s['section_title']: s for s in pred_sections}
        gt_dict = {s['section_title']: s for s in gt_sections}

        all_sections = set(pred_dict.keys()) | set(gt_dict.keys())

        comparison_data = []
        for section_title in all_sections:
            pred_score = pred_dict.get(section_title, {}).get('relevance_score', 0.0)
            gt_score = gt_dict.get(section_title, {}).get('relevance_score', 0.0)

            comparison_data.append({
                'section_title': section_title,
                'predicted_score': pred_score,
                'ground_truth_score': gt_score,
                'score_difference': abs(pred_score - gt_score),
                'in_predictions': section_title in pred_dict,
                'in_ground_truth': section_title in gt_dict
            })

        return pd.DataFrame(comparison_data).sort_values('score_difference', ascending=False)

    def _are_titles_similar(self, title1: str, title2: str, threshold: float = 0.6) -> bool:
        """Check if two section titles are similar enough to be considered matches"""
        if not title1 or not title2:
            return False

        # Normalize titles
        t1 = title1.lower().strip()
        t2 = title2.lower().strip()

        # Exact match
        if t1 == t2:
            return True

        # Check for common keywords
        keywords1 = set(t1.split())
        keywords2 = set(t2.split())

        # Remove common stop words
        stop_words = {'the', 'and', 'or', 'a', 'an', 'to', 'of', 'in', 'on', 'for', 'with'}
        keywords1 = keywords1 - stop_words
        keywords2 = keywords2 - stop_words

        if not keywords1 or not keywords2:
            return False

        # Calculate Jaccard similarity
        intersection = len(keywords1.intersection(keywords2))
        union = len(keywords1.union(keywords2))

        similarity = intersection / union if union > 0 else 0

        # Also check for substring matches
        if title1.lower() in title2.lower() or title2.lower() in title1.lower():
            similarity = max(similarity, 0.8)

        return similarity >= threshold


def main():
    """Main evaluation function"""
    if len(sys.argv) != 4:
        print("Usage: python evaluation.py <pdf_folder> <ground_truth_file> <persona_role>")
        print("Example: python evaluation.py 'Collection 1/PDFs' ground_truth.json 'Data Analyst'")
        sys.exit(1)

    pdf_folder = sys.argv[1]
    ground_truth_file = sys.argv[2]
    persona_role = sys.argv[3]

    # Job task (you can modify this or make it a parameter)
    job_task = "Analyze and extract key insights from the documents"

    print("Starting Document Intelligence Model Evaluation")
    print(f"PDF Folder: {pdf_folder}")
    print(f"Ground Truth: {ground_truth_file}")
    print(f"Persona: {persona_role}")
    print("-" * 60)

    # Initialize evaluator
    evaluator = ModelEvaluator()

    try:
        # Load ground truth
        print("Loading ground truth data...")
        ground_truth = evaluator.load_ground_truth(ground_truth_file)
        print(f"Loaded {len(ground_truth.get('extracted_sections', []))} ground truth sections")

        # Process documents with model
        print("Processing documents with model...")
        predictions = evaluator.process_documents(pdf_folder, persona_role, job_task)
        print(f"Model predicted {len(predictions.get('extracted_sections', []))} sections")

        # Evaluate predictions
        print("Calculating evaluation metrics...")
        metrics = evaluator.evaluate_predictions(predictions, ground_truth)

        # Display results
        print("\n" + "="*60)
        print("EVALUATION RESULTS")
        print("="*60)
        print(".4f")
        print(".4f")
        print(".4f")
        print(f"Common Sections Analyzed: {metrics['common_sections']}")
        print(f"Total Predictions: {metrics['total_predicted']}")
        print(f"Total Ground Truth: {metrics['total_ground_truth']}")

        # Detailed comparison
        print("\n" + "-"*60)
        print("DETAILED COMPARISON (Top 10 by score difference)")
        print("-"*60)

        comparison_df = evaluator.detailed_comparison(predictions, ground_truth)
        print(comparison_df.head(10).to_string(index=False))

        # Save detailed results
        output_file = f"evaluation_results_{int(__import__('time').time())}.csv"
        comparison_df.to_csv(output_file, index=False)
        print(f"\nDetailed results saved to: {output_file}")

    except Exception as e:
        print(f"Error during evaluation: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()