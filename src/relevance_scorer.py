import numpy as np
from typing import List, Dict, Any
import re

class RelevanceScorer:
    def __init__(self):
        pass
    
    def score_sections(self, sections: List[Dict[str, Any]], 
                      persona_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        
        if not sections:
            return []
        
        scored_sections = []
        
        all_keywords = persona_context.get('keywords', [])
        combined_query = persona_context.get('combined_query', '')
        
        for section in sections:
            score = self._calculate_pure_generic_score(section, all_keywords, combined_query)
            
            section_with_score = section.copy()
            section_with_score['relevance_score'] = score
            scored_sections.append(section_with_score)
        
        scored_sections.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        balanced_sections = self._ensure_diversity(scored_sections)
        
        for i, section in enumerate(balanced_sections):
            section['importance_rank'] = i + 1
        
        return balanced_sections
    
    def _calculate_pure_generic_score(self, section: Dict[str, Any], 
                                    keywords: List[str], 
                                    query: str) -> float:
        
        section_text = f"{section['section_title']} {section.get('content', '')}".lower()
        
        keyword_score = self._calculate_keyword_overlap(section_text, keywords)
        
        query_similarity = self._calculate_word_overlap(section_text, query)
        
        quality_score = self._calculate_text_quality(section)
        
        richness_score = self._calculate_content_richness(section_text)
        
        final_score = (
            0.40 * keyword_score +
            0.30 * query_similarity +
            0.20 * quality_score +
            0.10 * richness_score
        )
        
        return final_score
    
    def _calculate_keyword_overlap(self, text: str, keywords: List[str]) -> float:
        if not keywords or not text:
            return 0.0
        
        text_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', text.lower()))
        keyword_set = set(kw.lower() for kw in keywords)
        
        direct_matches = len(text_words.intersection(keyword_set))
        
        partial_matches = 0
        for keyword in keyword_set:
            if any(keyword in word for word in text_words):
                partial_matches += 1
        
        total_keywords = len(keyword_set)
        overlap_score = (direct_matches * 2 + partial_matches) / (total_keywords * 2)
        
        return min(1.0, overlap_score)
    
    def _calculate_word_overlap(self, text1: str, text2: str) -> float:
        if not text1 or not text2:
            return 0.0
        
        words1 = set(re.findall(r'\b[a-zA-Z]{3,}\b', text1.lower()))
        words2 = set(re.findall(r'\b[a-zA-Z]{3,}\b', text2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_text_quality(self, section: Dict[str, Any]) -> float:
        title = section.get('section_title', '')
        content = section.get('content', '')
        
        quality_score = 0.0
        
        if 10 <= len(title) <= 100:
            quality_score += 0.3
        elif 5 <= len(title) <= 150:
            quality_score += 0.1
        
        if content:
            word_count = len(content.split())
            if 20 <= word_count <= 200:
                quality_score += 0.4
            elif word_count > 10:
                quality_score += 0.2
        
        if ' ' in title and not title.startswith(' '):
            quality_score += 0.3
        
        return min(1.0, quality_score)
    
    def _calculate_content_richness(self, text: str) -> float:
        if not text:
            return 0.0
        
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        unique_words = len(set(words))
        total_words = len(words)
        
        if total_words == 0:
            return 0.0
        
        richness = unique_words / total_words
        
        if total_words > 50 and richness > 0.7:
            richness += 0.2
        
        return min(1.0, richness)
    
    def _ensure_diversity(self, ranked_sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not ranked_sections:
            return []
        
        unique_docs = list(set(section['document'] for section in ranked_sections))
        total_needed = min(15, len(ranked_sections))
        per_doc = max(1, total_needed // len(unique_docs))
        
        balanced = []
        doc_counts = {}
        
        for section in ranked_sections:
            doc = section['document']
            if doc_counts.get(doc, 0) < per_doc:
                balanced.append(section)
                doc_counts[doc] = doc_counts.get(doc, 0) + 1
        
        for section in ranked_sections:
            if len(balanced) >= total_needed:
                break
            if section not in balanced:
                balanced.append(section)
        
        return balanced[:total_needed]
