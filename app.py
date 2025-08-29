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

# Configure page
st.set_page_config(
    page_title="Document Intelligence System",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
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

        # Create temporary directory for uploaded files
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_paths = []

            # Save uploaded files to temp directory
            for uploaded_file in uploaded_files:
                file_path = os.path.join(temp_dir, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                pdf_paths.append(file_path)

            # Load and process documents
            documents = []
            for pdf_path in pdf_paths:
                doc_data = self.doc_processor._load_single_pdf(pdf_path)
                if doc_data:
                    documents.append(doc_data)

            if not documents:
                raise ValueError("No valid PDF documents found")

            # Extract sections
            all_sections = []
            for doc in documents:
                sections = self.doc_processor.extract_sections(doc)
                all_sections.extend(sections)

            if not all_sections:
                raise ValueError("No sections could be extracted from the documents")

            # Analyze persona and job requirements
            persona_context = self.persona_analyzer.analyze_persona(
                {'role': persona_role},
                {'task': job_task}
            )

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

            output_data = self.output_formatter.format_output(
                input_config, ranked_sections, subsections, start_time
            )

            return output_data

def main():
    st.markdown('<div class="main-header">📄 Document Intelligence System</div>', unsafe_allow_html=True)
    st.markdown("---")

    # Initialize system
    system = StreamlitDocumentIntelligenceSystem()

    # Sidebar for inputs
    with st.sidebar:
        st.header("🔧 Configuration")

        # File upload
        st.subheader("📁 Upload PDF Documents")
        uploaded_files = st.file_uploader(
            "Select PDF files",
            type=["pdf"],
            accept_multiple_files=True,
            help="Upload one or more PDF documents to analyze"
        )

        st.markdown("---")

        # Persona and task inputs
        st.subheader("👤 Analysis Configuration")

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

        # Processing options
        st.markdown("---")
        st.subheader("⚙️ Processing Options")

        max_sections = st.slider(
            "Maximum Sections to Display",
            min_value=5,
            max_value=25,
            value=15,
            help="Limit the number of top-ranked sections shown"
        )

        # Process button
        process_button = st.button(
            "🚀 Analyze Documents",
            type="primary",
            use_container_width=True,
            disabled=not (uploaded_files and persona_role and job_task)
        )

    # Main content area
    if not uploaded_files:
        # Welcome screen
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            st.markdown("### Welcome to Document Intelligence! 🎉")
            st.markdown("""
            This powerful tool helps you:

            🔍 **Extract relevant sections** from PDF documents
            📊 **Rank content by importance** based on your needs
            🎯 **Focus on what matters** with persona-driven analysis
            📈 **Get structured insights** with detailed statistics

            **Get started by:**
            1. Upload your PDF documents in the sidebar
            2. Select your role and describe your analysis goal
            3. Click "Analyze Documents" to see the magic happen!
            """)

            st.info("💡 **Tip:** Upload multiple related documents for better analysis results!")

    elif process_button:
        try:
            with st.spinner("🔄 Processing documents... This may take a few moments."):
                # Update output formatter with user preferences
                system.output_formatter.max_sections = max_sections

                # Process documents
                results = system.process_documents(uploaded_files, persona_role, job_task)

            # Display results
            display_results(results, uploaded_files)

        except Exception as e:
            st.error(f"❌ Error processing documents: {str(e)}")
            st.exception(e)

    # Footer
    st.markdown("---")
    st.markdown(
        '<div style="text-align: center; color: #666; font-size: 0.8rem;">'
        'Document Intelligence System - Powered by AI | Built with Streamlit'
        '</div>',
        unsafe_allow_html=True
    )

def display_results(results: Dict[str, Any], uploaded_files: List):
    """Display analysis results in an organized manner"""

    # Summary metrics
    st.markdown('<div class="section-header">📊 Analysis Summary</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Documents Processed", results['metadata']['document_count'])

    with col2:
        st.metric("Sections Found", results['statistics']['total_sections_found'])

    with col3:
        st.metric("Top Sections", results['statistics']['sections_included'])

    with col4:
        st.metric("Processing Time", f"{results['metadata']['processing_time_seconds']:.2f}s")

    # Statistics details
    with st.expander("📈 Detailed Statistics", expanded=False):
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

    # Display sections with integrated detailed analysis
    st.markdown('<div class="section-header">📋 Analysis Results</div>', unsafe_allow_html=True)

    sections = results['extracted_sections']

    if not sections:
        st.warning("No sections were extracted from the documents.")
    else:
        st.info(f"Found {len(sections)} relevant sections")

        # Sort sections by relevance score (highest first)
        sections.sort(key=lambda x: x['relevance_score'], reverse=True)

        # Create mapping of sections to their detailed analysis
        section_to_details = {}
        if results.get('subsection_analysis'):
            for subsection in results['subsection_analysis']:
                key = f"{subsection['source_section']}_{subsection['document']}"
                section_to_details[key] = subsection

        for i, section in enumerate(sections):
            section_key = f"{section['section_title']}_{section['document']}"

            with st.container():
                # Main section header with expand/collapse for details
                with st.expander(f"**{i+1}. {section['section_title']}** — Score: {section['relevance_score']:.3f}", expanded=False):
                    # Basic section info
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**📄 Document:** {section['document']}")
                        st.markdown(f"**📍 Page:** {section['page_number']}")
                        st.markdown(f"**📝 Words:** {section['word_count']}")
                    with col2:
                        st.metric("Relevance Score", f"{section['relevance_score']:.3f}")

                    # Detailed analysis for this section (if available)
                    if section_key in section_to_details:
                        st.markdown("---")
                        st.markdown("### 🔍 Detailed Analysis")
                        detail = section_to_details[section_key]
                        st.markdown(f"""
                        **Enhanced Analysis:**
                        - **Text Length:** {detail['text_length']} characters
                        - **Analysis Type:** AI-powered refinement
                        """)
                        st.write(detail['refined_text'])
                    else:
                        st.info("💡 No detailed analysis available for this section.")

    # Export options
    st.markdown('<div class="section-header">💾 Export Results</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        # JSON export
        json_data = json.dumps(results, indent=2)
        st.download_button(
            label="📄 Download JSON",
            data=json_data,
            file_name=f"document_analysis_{int(time.time())}.json",
            mime="application/json",
            use_container_width=True
        )

    with col2:
        # CSV export for sections
        if sections:
            sections_df = pd.DataFrame(sections)
            csv_data = sections_df.to_csv(index=False)
            st.download_button(
                label="📊 Download Sections CSV",
                data=csv_data,
                file_name=f"sections_analysis_{int(time.time())}.csv",
                mime="text/csv",
                use_container_width=True
            )

    with col3:
        # Summary text export
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
            label="📝 Download Summary",
            data=summary_text,
            file_name=f"analysis_summary_{int(time.time())}.txt",
            mime="text/plain",
            use_container_width=True
        )

if __name__ == "__main__":
    main()