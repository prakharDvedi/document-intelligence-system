import streamlit as st
import os
import json
import time
import tempfile
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
import base64

# Import existing modules
from src.document_processor import DocumentProcessor
from src.persona_analyzer import PersonaAnalyzer
from src.relevance_scorer import RelevanceScorer
from src.output_formatter import OutputFormatter

st.set_page_config(
    page_title="Document Intelligence System",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
    }
    .result-card {
        background-color: #ffffff;
        border: 1px solid #e9ecef;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .relevance-score {
        color: #28a745;
        font-weight: bold;
        font-size: 1.1rem;
    }
</style>
""", unsafe_allow_html=True)

class StreamlitDocumentIntelligenceSystem:
    def __init__(self):
        self.doc_processor = DocumentProcessor()
        self.persona_analyzer = PersonaAnalyzer()
        self.relevance_scorer = RelevanceScorer()
        self.output_formatter = OutputFormatter()

    def process_documents(self, uploaded_files: List, persona_role: str, job_task: str) -> Dict[str, Any]:
        """Process uploaded PDF files and return analysis results"""
        start_time = time.time()

        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_paths = []

            for uploaded_file in uploaded_files:
                file_path = os.path.join(temp_dir, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                pdf_paths.append(file_path)

            documents = []
            for pdf_path in pdf_paths:
                doc_data = self.doc_processor._load_single_pdf(pdf_path)
                if doc_data:
                    documents.append(doc_data)

            if not documents:
                raise ValueError("No valid PDF documents found")

            all_sections = []
            for doc in documents:
                sections = self.doc_processor.extract_sections(doc)
                all_sections.extend(sections)

            if not all_sections:
                raise ValueError("No sections could be extracted from the documents")

            persona_context = self.persona_analyzer.analyze_persona(
                {'role': persona_role},
                {'task': job_task}
            )

            ranked_sections = self.relevance_scorer.score_sections(all_sections, persona_context)

            subsections = self.doc_processor.extract_subsections(ranked_sections[:10])

            input_config = {
                'persona': {'role': persona_role},
                'job_to_be_done': {'task': job_task},
                'documents': [{'filename': doc['filename']} for doc in documents]
            }

            output_data = self.output_formatter.format_output(
                input_config, ranked_sections, subsections, start_time
            )

            return output_data

def main():
    st.markdown('<div class="main-header">Document Intelligence System</div>', unsafe_allow_html=True)
    st.markdown("---")

    system = StreamlitDocumentIntelligenceSystem()

    with st.sidebar:
        st.header("Configuration")

        use_demo = st.checkbox(
            "Use Demo Data from Collection 2",
            help="Load pre-processed demo data instead of uploading PDFs"
        )

        if not use_demo:
            st.subheader("Upload PDF Documents")
            uploaded_files = st.file_uploader(
                "Select PDF files",
                type=["pdf"],
                accept_multiple_files=True,
                help="Upload one or more PDF documents to analyze"
            )
        else:
            uploaded_files = None
            st.info("Demo mode selected. Demo data from Collection 3 will be used.")

        st.markdown("---")

        st.subheader("Analysis Configuration")

        persona_role = st.selectbox(
            "Select Persona Role",
            [
                "General User",
                "Data Analyst",
                "Business Analyst",
                "Researcher",
                "Manager",
                "Legal Counsel",
                "Technical Writer",
                "Student",
                "Consultant",
                "Custom"
            ],
            help="Choose the role that best describes your perspective"
        )

        if persona_role == "Custom":
            persona_role = st.text_input(
                "Enter Custom Persona Role",
                placeholder="e.g., Marketing Manager, Product Designer"
            )

        job_task = st.text_area(
            "Job Task / Analysis Goal",
            placeholder="Describe what you want to extract or analyze from the documents...",
            height=100,
            help="Be specific about what information you're looking for"
        )

        st.markdown("---")
        st.subheader("Processing Options")

        max_sections = st.slider(
            "Maximum Sections to Display",
            min_value=5,
            max_value=25,
            value=15,
            help="Limit the number of top-ranked sections shown"
        )

        process_button = st.button(
            "Analyze Documents",
            type="primary",
            use_container_width=True,
            disabled=not ((uploaded_files or use_demo) and persona_role and job_task)
        )

    if not (uploaded_files or use_demo):
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            st.markdown("### Welcome to Document Intelligence!")
            st.markdown("""
            This powerful tool helps you:

            - Extract relevant sections from PDF documents
            - Rank content by importance based on your needs
            - Focus on what matters with persona-driven analysis
            - Get structured insights with detailed statistics

            Get started by:
            1. Upload your PDF documents in the sidebar
            2. Select your role and describe your analysis goal
            3. Click "Analyze Documents" to see the results!
            """)

            st.info("Tip: Upload multiple related documents for better analysis results!")

    if use_demo:
        st.markdown('<div class="section-header">Demo Documents Preview</div>', unsafe_allow_html=True)
        with open("ground_truth_collection_2.json", "r") as f:
            demo_data = json.load(f)
        st.markdown("**Available Demo PDFs:**")
        for doc in demo_data['metadata']['input_documents']:
            st.markdown(f"- {doc}")
        st.info("Select your persona and task, then click 'Analyze Documents' to explore the demo data.")

    if process_button:
        try:
            if use_demo:
                with st.spinner("Loading demo data..."):
                    with open("ground_truth_collection_2.json", "r") as f:
                        results = json.load(f)
                    # Add missing fields for compatibility
                    results['metadata']['document_count'] = len(results['metadata']['input_documents'])
                    results['metadata']['processing_time_seconds'] = 1.23  # Dummy value for demo
                    sections = results['extracted_sections']
                    for section in sections:
                        if 'word_count' not in section:
                            section['word_count'] = len(section['section_title'].split())  # Estimate word count
                    for i, subsection in enumerate(results.get('subsection_analysis', [])):
                        # Map subsections to their corresponding section titles for collection 2
                        if subsection['document'] == "Learn Acrobat - Fill and Sign.pdf":
                            if i == 0 or i == 2:  # First and third subsections
                                subsection['source_section'] = "Change flat forms to fillable (Acrobat Pro)"
                            elif i == 1 or i == 3:  # Second and fourth
                                subsection['source_section'] = "Fill and sign PDF forms"
                        elif subsection['document'] == "Learn Acrobat - Request e-signatures_1.pdf":
                            subsection['source_section'] = "Send a document to get signatures from others"
                        else:
                            subsection['source_section'] = subsection['document'].replace('.pdf', '')
                        subsection['text_length'] = len(subsection['refined_text'])
                    results['statistics'] = {
                        'total_sections_found': len(sections),
                        'sections_included': len(sections),
                        'subsections_included': len(results.get('subsection_analysis', [])),
                        'total_words_analyzed': sum(s['word_count'] for s in sections),
                        'average_relevance_score': sum(s['relevance_score'] for s in sections) / len(sections) if sections else 0,
                        'max_relevance_score': max(s['relevance_score'] for s in sections) if sections else 0,
                        'min_relevance_score': min(s['relevance_score'] for s in sections) if sections else 0
                    }
                    # Create dummy uploaded_files for display
                    uploaded_files = [type('obj', (object,), {'name': doc})() for doc in results['metadata']['input_documents']]
            else:
                with st.spinner("Processing documents... This may take a few moments."):
                    system.output_formatter.max_sections = max_sections

                    results = system.process_documents(uploaded_files, persona_role, job_task)

            display_results(results, uploaded_files)

        except Exception as e:
            st.error(f"Error processing documents: {str(e)}")
            st.exception(e)

    st.markdown("---")
    st.markdown(
        '<div style="text-align: center; color: #666; font-size: 0.8rem;">'
        'Document Intelligence System - Powered by AI | Built with Streamlit'
        '</div>',
        unsafe_allow_html=True
    )

def display_results(results: Dict[str, Any], uploaded_files: List):
    """Display analysis results in an organized manner"""

    st.markdown('<div class="section-header">Analysis Summary</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Documents Processed", results['metadata']['document_count'])

    with col2:
        st.metric("Sections Found", results['statistics']['total_sections_found'])

    with col3:
        st.metric("Top Sections", results['statistics']['sections_included'])

    with col4:
        st.metric("Processing Time", f"{results['metadata']['processing_time_seconds']:.2f}s")

    with st.expander("Detailed Statistics", expanded=False):
        stats_data = {
            'Metric': [
                'Total Sections Found',
                'Sections Included',
                'Subsections Included',
                'Total Words Analyzed',
                'Average Relevance Score',
                'Max Relevance Score',
                'Min Relevance Score'
            ],
            'Value': [
                int(results['statistics']['total_sections_found']),
                int(results['statistics']['sections_included']),
                int(results['statistics']['subsections_included']),
                int(results['statistics']['total_words_analyzed']),
                float(results['statistics']['average_relevance_score']),
                float(results['statistics']['max_relevance_score']),
                float(results['statistics']['min_relevance_score'])
            ]
        }
        stats_df = pd.DataFrame(stats_data)
        st.dataframe(stats_df, use_container_width=True)

    st.markdown('<div class="section-header">Analysis Results</div>', unsafe_allow_html=True)

    sections = results['extracted_sections']

    if not sections:
        st.warning("No sections were extracted from the documents.")
    else:
        st.info(f"Found {len(sections)} relevant sections")

        sections.sort(key=lambda x: x['relevance_score'], reverse=True)

        section_to_details = {}
        if results.get('subsection_analysis'):
            for subsection in results['subsection_analysis']:
                key = f"{subsection['source_section']}_{subsection['document']}"
                section_to_details[key] = subsection

        for i, section in enumerate(sections):
            section_key = f"{section['section_title']}_{section['document']}"

            with st.container():
                with st.expander(f"**{i+1}. {section['section_title']}** — Score: {section['relevance_score']:.3f}", expanded=False):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**Document:** {section['document']}")
                        st.markdown(f"**Page:** {section['page_number']}")
                        st.markdown(f"**Words:** {section['word_count']}")
                    with col2:
                        st.metric("Relevance Score", f"{section['relevance_score']:.3f}")

                    if section_key in section_to_details:
                        st.markdown("---")
                        st.markdown("### Detailed Analysis")
                        detail = section_to_details[section_key]
                        st.markdown(f"""
                        **Enhanced Analysis:**
                        - **Text Length:** {detail['text_length']} characters
                        - **Analysis Type:** AI-powered refinement
                        """)
                        st.write(detail['refined_text'])
                    else:
                        st.info("No detailed analysis available for this section.")

    st.markdown('<div class="section-header">Export Results</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        json_data = json.dumps(results, indent=2)
        st.download_button(
            label="Download JSON",
            data=json_data,
            file_name=f"document_analysis_{int(time.time())}.json",
            mime="application/json",
            use_container_width=True
        )

    with col2:
        if sections:
            sections_df = pd.DataFrame(sections)
            csv_data = sections_df.to_csv(index=False)
            st.download_button(
                label="Download Sections CSV",
                data=csv_data,
                file_name=f"sections_analysis_{int(time.time())}.csv",
                mime="text/csv",
                use_container_width=True
            )

    with col3:
        summary_text = f"""
        Document Intelligence Analysis Report
        =====================================

        Analysis Configuration:
        - Persona: {results['metadata']['persona']}
        - Task: {results['metadata']['job_to_be_done']}
        - Documents: {', '.join(results['metadata']['input_documents'])}
        - Processing Time: {results['metadata']['processing_time_seconds']:.2f} seconds

        Summary Statistics:
        - Total Sections Found: {results['statistics']['total_sections_found']}
        - Sections Included: {results['statistics']['sections_included']}
        - Average Relevance Score: {results['statistics']['average_relevance_score']:.3f}

        Top 5 Sections:
        """
        for i, section in enumerate(sections[:5]):
            summary_text += f"\n{i+1}. {section['section_title'][:50]}... (Score: {section['relevance_score']:.3f})"

        st.download_button(
            label="Download Summary",
            data=summary_text,
            file_name=f"analysis_summary_{int(time.time())}.txt",
            mime="text/plain",
            use_container_width=True
        )

if __name__ == "__main__":
    main()
