import fitz
import re
import os
from typing import List, Dict, Any, Optional

class DocumentProcessor:
    def __init__(self, custom_patterns: Optional[List[str]] = None):
        default_patterns = [
            r'^[A-Z][A-Za-z\s]{15,80}$',
            r'^[A-Z][A-Z\s]{8,60}$',
            r'^(Introduction|Overview|Summary|Conclusion|Background|Methods?|Results?|Discussion|Analysis|Recommendations?)\s*:?\s*[A-Za-z\s]*$',
            r'^(Chapter|Section|Part|Step)\s+\d+:?\s*[A-Z][A-Za-z\s]{5,50}$',
            r'^\d+(\.\d+)*\s+[A-Z][A-Za-z\s]{10,60}$',
            r'^(Key|Main|Important|Essential|Critical|Primary|Secondary)\s+[A-Za-z\s]{10,50}$',
            r'^(What|How|Why|When|Where|Which)\s+[A-Za-z\s]{10,60}\??$',
        ]
        
        self.section_patterns = custom_patterns if custom_patterns else default_patterns
        
        self.stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'should', 'could', 'can', 'may',
            'might', 'must', 'a', 'an', 'this', 'that', 'these', 'those', 'from'
        }
    
    def load_pdfs(self, pdf_path: str, recursive: bool = False) -> List[Dict[str, Any]]:
        documents = []
        
        if not os.path.exists(pdf_path):
            print(f"Warning: Path '{pdf_path}' does not exist")
            return documents
        
        if os.path.isfile(pdf_path) and pdf_path.lower().endswith('.pdf'):
            doc_data = self._load_single_pdf(pdf_path)
            if doc_data:
                documents.append(doc_data)
            return documents
        
        if os.path.isdir(pdf_path):
            pdf_files = self._find_pdf_files(pdf_path, recursive)
            
            for filepath in pdf_files:
                doc_data = self._load_single_pdf(filepath)
                if doc_data:
                    documents.append(doc_data)
        
        return documents
    
    def _find_pdf_files(self, folder_path: str, recursive: bool = False) -> List[str]:
        pdf_files = []
        
        try:
            if recursive:
                for root, dirs, files in os.walk(folder_path):
                    for filename in files:
                        if filename.lower().endswith('.pdf'):
                            pdf_files.append(os.path.join(root, filename))
            else:
                for filename in os.listdir(folder_path):
                    if filename.lower().endswith('.pdf'):
                        pdf_files.append(os.path.join(folder_path, filename))
        except Exception as e:
            print(f"Error scanning folder {folder_path}: {e}")
        
        return sorted(pdf_files)
    
    def _load_single_pdf(self, filepath: str) -> Optional[Dict[str, Any]]:
        try:
            doc = fitz.open(filepath)
            
            if len(doc) == 0:
                print(f"Warning: {os.path.basename(filepath)} appears to be empty")
                doc.close()
                return None
            
            pages = []
            total_text_length = 0
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                
                cleaned_text = self._clean_extracted_text(text)
                total_text_length += len(cleaned_text)
                
                pages.append({
                    'page_number': page_num + 1,
                    'text': cleaned_text,
                    'char_count': len(cleaned_text)
                })
            
            doc.close()
            
            if total_text_length < 100:
                print(f"Warning: {os.path.basename(filepath)} has very little text content")
                return None
            
            return {
                'filename': os.path.basename(filepath),
                'filepath': filepath,
                'pages': pages,
                'total_pages': len(pages),
                'total_chars': total_text_length,
                'avg_chars_per_page': total_text_length / len(pages) if pages else 0
            }
            
        except Exception as e:
            print(f"Error loading {os.path.basename(filepath)}: {e}")
            return None
    
    def _clean_extracted_text(self, text: str) -> str:
        if not text:
            return ""
        
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', '', text)
        
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if re.match(r'^\d+$', line) and len(line) <= 3:
                continue
                
            if len(line) < 3:
                continue
                
            cleaned_lines.append(line)
        
        return ' '.join(cleaned_lines).strip()
    
    def extract_sections(self, document: Dict[str, Any], min_content_length: int = 50) -> List[Dict[str, Any]]:
        sections = []
        
        for page in document['pages']:
            page_text = page['text']
            if not page_text.strip():
                continue
            
            page_sections = []
            
            lines = page_text.split('\n')
            page_sections.extend(self._extract_sections_by_lines(lines, document, page))
            
            if len(page_sections) < 2:
                paragraphs = self._split_into_paragraphs(page_text)
                page_sections.extend(self._extract_sections_by_paragraphs(paragraphs, document, page))
            
            if len(page_sections) == 0:
                page_sections.extend(self._extract_fallback_sections(page_text, document, page))
            
            for section in page_sections:
                if (section.get('content', '') and 
                    len(section['content']) >= min_content_length and
                    self._is_valid_section(section)):
                    sections.append(section)
        
        sections = self._deduplicate_sections(sections)
        
        return sections
    
    def _extract_sections_by_lines(self, lines: List[str], document: Dict[str, Any], page: Dict[str, Any]) -> List[Dict[str, Any]]:
        sections = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            if self._is_proper_section_header(line, lines, i):
                content = self._extract_section_content(lines, i)
                
                if content:
                    sections.append({
                        'document': document['filename'],
                        'page_number': page['page_number'],
                        'section_title': line,
                        'content': content,
                        'word_count': len(content.split()),
                        'extraction_method': 'line_analysis'
                    })
        
        return sections
    
    def _extract_sections_by_paragraphs(self, paragraphs: List[str], document: Dict[str, Any], page: Dict[str, Any]) -> List[Dict[str, Any]]:
        sections = []
        
        for i, paragraph in enumerate(paragraphs):
            if not paragraph.strip():
                continue
            
            lines = paragraph.split('\n')
            first_line = lines[0].strip()
            
            if (len(lines) > 1 and 
                self._could_be_section_header(first_line) and
                len(first_line) < 100):
                
                content = '\n'.join(lines[1:]).strip()
                if len(content) > 30:
                    sections.append({
                        'document': document['filename'],
                        'page_number': page['page_number'],
                        'section_title': first_line,
                        'content': content,
                        'word_count': len(content.split()),
                        'extraction_method': 'paragraph_analysis'
                    })
        
        return sections
    
    def _extract_fallback_sections(self, page_text: str, document: Dict[str, Any], page: Dict[str, Any]) -> List[Dict[str, Any]]:
        sections = []
        
        sentences = re.split(r'(?<=[.!?])\s+', page_text)
        
        current_chunk = []
        chunk_size = 0
        section_count = 1
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            current_chunk.append(sentence)
            chunk_size += len(sentence)
            
            if chunk_size >= 200 or len(current_chunk) >= 5:
                content = ' '.join(current_chunk)
                
                first_sentence = current_chunk[0]
                if len(first_sentence) > 100:
                    title_words = first_sentence.split()[:8]
                    title = ' '.join(title_words) + '...'
                else:
                    title = first_sentence
                
                if title.endswith('.'):
                    title = title[:-1]
                
                sections.append({
                    'document': document['filename'],
                    'page_number': page['page_number'],
                    'section_title': title,
                    'content': content,
                    'word_count': len(content.split()),
                    'extraction_method': 'fallback_chunking'
                })
                
                current_chunk = []
                chunk_size = 0
                section_count += 1
                
                if section_count > 5:
                    break
        
        if current_chunk and chunk_size >= 100:
            content = ' '.join(current_chunk)
            first_sentence = current_chunk[0]
            
            if len(first_sentence) > 100:
                title_words = first_sentence.split()[:8]
                title = ' '.join(title_words) + '...'
            else:
                title = first_sentence
                
            if title.endswith('.'):
                title = title[:-1]
            
            sections.append({
                'document': document['filename'],
                'page_number': page['page_number'],
                'section_title': title,
                'content': content,
                'word_count': len(content.split()),
                'extraction_method': 'fallback_chunking'
            })
        
        return sections
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        paragraphs = re.split(r'\n\s*\n', text)
        
        if len(paragraphs) < 3:
            paragraphs = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _could_be_section_header(self, line: str) -> bool:
        if not line or len(line) < 5 or len(line) > 150:
            return False
        
        has_title_case = line.istitle()
        has_caps = any(c.isupper() for c in line)
        starts_with_cap = line[0].isupper()
        has_colon = ':' in line
        
        header_indicators = [
            'introduction', 'overview', 'summary', 'conclusion', 'background',
            'method', 'result', 'discussion', 'analysis', 'recommendation',
            'key', 'main', 'important', 'essential', 'step', 'tip', 'guide'
        ]
        
        has_header_words = any(word.lower() in line.lower() for word in header_indicators)
        
        return (starts_with_cap and (has_title_case or has_caps or has_colon or has_header_words))
    
    def _is_valid_section(self, section: Dict[str, Any]) -> bool:
        title = section.get('section_title', '')
        content = section.get('content', '')
        
        if not title or len(title) < 5 or len(title) > 200:
            return False
        
        if not content or len(content.split()) < 5:
            return False
        
        words = content.split()
        if len(words) > 5 and all(len(word) < 15 for word in words[:10]):
            avg_word_length = sum(len(word) for word in words[:10]) / 10
            if avg_word_length < 4:
                return False
        
        return True
    
    def _deduplicate_sections(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not sections:
            return sections
        
        unique_sections = []
        seen_titles = set()
        
        for section in sections:
            title = section['section_title'].lower().strip()
            
            if title in seen_titles:
                continue
            
            is_similar = False
            for seen_title in seen_titles:
                if self._titles_are_similar(title, seen_title):
                    is_similar = True
                    break
            
            if not is_similar:
                unique_sections.append(section)
                seen_titles.add(title)
        
        return unique_sections
    
    def _titles_are_similar(self, title1: str, title2: str, threshold: float = 0.8) -> bool:
        if not title1 or not title2:
            return False
        
        words1 = set(title1.lower().split())
        words2 = set(title2.lower().split())
        
        if not words1 or not words2:
            return False
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        similarity = intersection / union if union > 0 else 0
        return similarity >= threshold
    
    def _is_proper_section_header(self, line: str, all_lines: List[str], index: int) -> bool:
        if len(line) < 5 or len(line) > 200:
            return False
        
        if line.lower().startswith(('to ', 'for ', 'with ', 'during ', 'whether ', 'and ', 'or ', 'but ', 'the ', 'this ', 'it ', 'a ', 'an ')):
            return False
        
        if line.lower().endswith((' and', ' or', ' with', ' to', ' for', ' of', ' in', ' on')):
            return False
        
        if not (line[0].isupper() or line[0].isdigit()):
            return False
        
        for pattern in self.section_patterns:
            if re.match(pattern, line):
                return self._validate_as_header(line, all_lines, index)
        
        words = line.split()
        if len(words) >= 1:
            if len(words) == 1 and len(line) >= 5 and line.istitle():
                return self._validate_as_header(line, all_lines, index)
            
            if (line.istitle() and 
                not line.endswith('.') and 
                not line.startswith('•') and
                len(line) >= 10):
                return self._validate_as_header(line, all_lines, index)
            
            structural_words = [
                'overview', 'introduction', 'summary', 'conclusion', 'background',
                'analysis', 'discussion', 'results', 'findings', 'recommendations',
                'key', 'main', 'important', 'essential', 'primary', 'secondary',
                'step', 'phase', 'stage', 'part', 'section', 'chapter',
                'guide', 'tips', 'methods', 'approach', 'strategy', 'process',
                'cities', 'cuisine', 'history', 'restaurants', 'hotels', 'things',
                'tricks', 'traditions', 'culture', 'activities', 'attractions'
            ]
            
            if (any(word.lower() in line.lower() for word in structural_words) and
                len(words) <= 12 and
                line[0].isupper()):
                return self._validate_as_header(line, all_lines, index)
            
            if (line.isupper() and 
                len(words) <= 10 and 
                len(line) <= 100):
                return self._validate_as_header(line, all_lines, index)
            
            if (len(words) >= 2 and 
                len(words) <= 8 and
                line[0].isupper() and
                not line.endswith('.') and
                any(c.isupper() for c in line[1:])):
                return self._validate_as_header(line, all_lines, index)
        
        return False
    
    def _validate_as_header(self, line: str, all_lines: List[str], index: int) -> bool:
        following_content = ""
        content_lines = 0
        
        for i in range(index + 1, min(index + 8, len(all_lines))):
            if i < len(all_lines):
                line_content = all_lines[i].strip()
                if line_content:
                    following_content += " " + line_content
                    content_lines += 1
        
        if len(following_content.strip()) < 15 or content_lines < 1:
            return False
        
        next_line = all_lines[index + 1].strip() if index + 1 < len(all_lines) else ""
        if next_line:
            if (len(next_line) > 10 and
                len(next_line) < 100 and
                (next_line.istitle() or next_line.isupper()) and
                not next_line.lower().startswith(('the ', 'this ', 'it ', 'you ', 'a ', 'an ', 'in ', 'on ', 'at ', 'to '))):
                words = next_line.split()
                if len(words) <= 6 and not next_line.endswith('.'):
                    return False
        
        return True
    
    def _extract_section_content(self, lines: List[str], header_index: int) -> str:
        content_lines = []
        
        for i in range(header_index + 1, min(header_index + 15, len(lines))):
            line = lines[i].strip()
            if not line:
                continue
            
            if (len(line) > 15 and
                (line.istitle() or line.isupper()) and
                not line.lower().startswith(('the ', 'this ', 'it ', 'you ', 'a ', 'an '))):
                break
            
            content_lines.append(line)
            
            if len(' '.join(content_lines)) > 200:
                break
        
        return self._clean_text(' '.join(content_lines))
    
    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        text = re.sub(r'^[•\-\*]\s*', '', text)
        
        return text
    
    def extract_subsections(self, top_sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        subsections = []
        
        for section in top_sections:
            content = section.get('content', '').strip()
            title = section['section_title']
            
            if not content:
                continue
            
            if len(content) > 300:
                sentences = re.split(r'(?<=[.!?])\s+', content)
                if len(sentences) >= 2:
                    selected = sentences[:3] if len(sentences) >= 3 else sentences[:2]
                    refined_text = ' '.join(selected)
                else:
                    refined_text = content[:300]
                    last_space = refined_text.rfind(' ')
                    if last_space > 250:
                        refined_text = refined_text[:last_space]
            else:
                refined_text = content
            
            subsections.append({
                'document': section['document'],
                'page_number': section['page_number'],
                'refined_text': refined_text,
                'source_section': title
            })
        
        return subsections
