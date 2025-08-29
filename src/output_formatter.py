import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

class OutputFormatter:
    def __init__(self, max_sections: int = 15, max_subsections: int = 10, max_text_length: int = 500):
        self.max_sections = max_sections
        self.max_subsections = max_subsections
        self.max_text_length = max_text_length
    
    def format_output(self, input_config: Dict[str, Any], 
                     ranked_sections: List[Dict[str, Any]],
                     subsections: List[Dict[str, Any]], 
                     start_time: float,
                     additional_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        
        input_documents = self._extract_document_list(input_config, ranked_sections)
        
        metadata = self._build_metadata(input_config, input_documents, start_time, additional_metadata)
        
        extracted_sections = self._format_sections(ranked_sections)
        
        subsection_analysis = self._format_subsections(subsections)
        
        statistics = self._build_statistics(ranked_sections, subsections, input_documents)
        
        return {
            "metadata": metadata,
            "statistics": statistics,
            "extracted_sections": extracted_sections,
            "subsection_analysis": subsection_analysis
        }
    
    def _extract_document_list(self, input_config: Dict[str, Any], ranked_sections: List[Dict[str, Any]]) -> List[str]:
        input_documents = []
        
        if 'documents' in input_config and input_config['documents']:
            for doc in input_config['documents']:
                if isinstance(doc, dict):
                    filename = doc.get('filename', doc.get('title', doc.get('name', '')))
                else:
                    filename = str(doc)
                if filename:
                    input_documents.append(filename)
        
        if not input_documents and ranked_sections:
            input_documents = list(set(section.get('document', 'Unknown') for section in ranked_sections))
            input_documents.sort()
        
        return input_documents
    
    def _build_metadata(self, input_config: Dict[str, Any], input_documents: List[str], 
                       start_time: float, additional_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        
        persona_info = input_config.get('persona', {})
        if isinstance(persona_info, dict):
            persona_role = persona_info.get('role', 'General User')
        else:
            persona_role = str(persona_info) if persona_info else 'General User'
        
        job_info = input_config.get('job_to_be_done', {})
        if isinstance(job_info, dict):
            job_task = job_info.get('task', 'Document Analysis')
        else:
            job_task = str(job_info) if job_info else 'Document Analysis'
        
        processing_time = time.time() - start_time
        
        metadata = {
            "input_documents": input_documents,
            "document_count": len(input_documents),
            "persona": persona_role,
            "job_to_be_done": job_task,
            "processing_timestamp": datetime.now().isoformat() + "Z",
            "processing_time_seconds": round(processing_time, 2),
            "system_version": "2.0.0-generic"
        }
        
        if 'challenge_info' in input_config:
            metadata['challenge_info'] = input_config['challenge_info']
        
        if additional_metadata:
            metadata.update(additional_metadata)
        
        return metadata
    
    def _format_sections(self, ranked_sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        extracted_sections = []
        
        for i, section in enumerate(ranked_sections[:self.max_sections]):
            section_data = {
                "document": section.get('document', 'Unknown'),
                "section_title": section.get('section_title', 'Untitled Section'),
                "importance_rank": section.get('importance_rank', i + 1),
                "page_number": section.get('page_number', 1),
                "word_count": section.get('word_count', 0),
                "relevance_score": round(section.get('relevance_score', 0.0), 3)
            }
            
            if 'extraction_method' in section:
                section_data['extraction_method'] = section['extraction_method']
            
            extracted_sections.append(section_data)
        
        return extracted_sections
    
    def _format_subsections(self, subsections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        subsection_analysis = []
        
        for subsection in subsections[:self.max_subsections]:
            refined_text = subsection.get('refined_text', '')
            
            if len(refined_text) > self.max_text_length:
                refined_text = refined_text[:self.max_text_length].rsplit(' ', 1)[0] + '...'
            
            subsection_data = {
                "document": subsection.get('document', 'Unknown'),
                "refined_text": refined_text,
                "page_number": subsection.get('page_number', 1),
                "source_section": subsection.get('source_section', 'Unknown Section'),
                "text_length": len(refined_text)
            }
            
            subsection_analysis.append(subsection_data)
        
        return subsection_analysis
    
    def _build_statistics(self, ranked_sections: List[Dict[str, Any]], 
                         subsections: List[Dict[str, Any]], 
                         input_documents: List[str]) -> Dict[str, Any]:
        
        total_sections = len(ranked_sections)
        sections_per_document = {}
        total_words = 0
        
        for section in ranked_sections:
            doc = section.get('document', 'Unknown')
            sections_per_document[doc] = sections_per_document.get(doc, 0) + 1
            total_words += section.get('word_count', 0)
        
        scores = [section.get('relevance_score', 0) for section in ranked_sections]
        avg_score = sum(scores) / len(scores) if scores else 0
        max_score = max(scores) if scores else 0
        min_score = min(scores) if scores else 0
        
        return {
            "total_sections_found": total_sections,
            "sections_included": min(total_sections, self.max_sections),
            "subsections_included": min(len(subsections), self.max_subsections),
            "total_words_analyzed": total_words,
            "average_relevance_score": round(avg_score, 3),
            "max_relevance_score": round(max_score, 3),
            "min_relevance_score": round(min_score, 3),
            "sections_per_document": sections_per_document
        }
