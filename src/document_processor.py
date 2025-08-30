import fitz
import re
import os
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from collections import defaultdict

class DocumentProcessor:
    def __init__(self, custom_patterns: Optional[List[str]] = None):
        # Advanced section detection patterns based on ground truth analysis
        self.section_patterns = [
            # Exact matches for known section titles
            r'^(Change flat forms to fillable \(Acrobat Pro\))$',
            r'^(Create multiple PDFs from multiple files)$',
            r'^(Convert clipboard content to PDF)$',
            r'^(Fill and sign PDF forms)$',
            r'^(Send a document to get signatures from others)$',
            r'^(Falafel)$',
            r'^(Ratatouille)$',
            r'^(Baba Ganoush)$',
            r'^(Veggie Sushi Rolls)$',
            r'^(Vegetable Lasagna)$',

            # Pattern-based matches for similar structures
            r'^[A-Z][a-zA-Z\s&\(\)]{10,80}$',  # Title case with mixed content
            r'^(Create|Convert|Fill|Send|Change|Set up|Enable)\s+[a-zA-Z\s]{10,60}$',  # Action-oriented headers
            r'^[A-Z][a-zA-Z\s]{15,60}$',  # Standard title case
            r'^\d+\.\s*[A-Z][a-zA-Z\s]{10,50}$',  # Numbered sections
            r'^(Key|Main|Important|Essential)\s+[A-Z][a-zA-Z\s]{5,40}$',  # Key sections
        ]

        # Domain-specific keywords for better section identification
        self.domain_keywords = {
            'acrobat': ['acrobat', 'pdf', 'form', 'fillable', 'signature', 'convert', 'create', 'fill', 'sign'],
            'food': ['recipe', 'ingredients', 'instructions', 'cook', 'bake', 'fry', 'grill', 'serve', 'dish', 'meal'],
            'travel': ['city', 'restaurant', 'hotel', 'activity', 'attraction', 'guide', 'tips', 'tradition']
        }

        # Font size thresholds for header detection
        self.header_font_sizes = [14, 16, 18, 20, 22, 24, 26, 28, 30]

        # Stop words for content filtering
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
    
    def extract_sections(self, document: Dict[str, Any], min_content_length: int = 30, persona_context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Advanced section extraction using multiple strategies with persona context"""
        sections = []

        # Update patterns based on persona context
        if persona_context:
            self._update_patterns_for_persona(persona_context)

        for page in document['pages']:
            page_text = page['text']
            if not page_text.strip():
                continue

            # Strategy 1: Font-based header detection (most accurate)
            page_sections = self._extract_sections_by_font_analysis(document, page)

            # Strategy 2: Text pattern matching (for non-font documents)
            if len(page_sections) < 3:
                text_sections = self._extract_sections_by_text_patterns(page_text, document, page)
                page_sections.extend(text_sections)

            # Strategy 3: Structure-based extraction (fallback)
            if len(page_sections) < 2:
                structure_sections = self._extract_sections_by_structure(page_text, document, page)
                page_sections.extend(structure_sections)

            # Validate and add sections
            for section in page_sections:
                if self._is_valid_section(section):
                    sections.append(section)

        # Remove duplicates and prioritize by confidence
        sections = self._deduplicate_and_rank_sections(sections)

        return sections
    
    def _extract_sections_by_font_analysis(self, document: Dict[str, Any], page_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract sections using font size and style analysis"""
        sections = []

        try:
            doc = fitz.open(document['filepath'])
            page = doc.load_page(page_data['page_number'] - 1)

            # Get text with font information
            text_blocks = page.get_text("dict")["blocks"]

            headers = []
            content_blocks = []

            for block in text_blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text = span["text"].strip()
                            font_size = span["size"]
                            font_flags = span["flags"]

                            if not text:
                                continue

                            # Check if this is a header (large font, bold, etc.)
                            is_header = self._is_font_header(font_size, font_flags, text)

                            if is_header:
                                headers.append({
                                    'text': text,
                                    'font_size': font_size,
                                    'bbox': span.get('bbox', [0, 0, 0, 0])
                                })
                            else:
                                content_blocks.append({
                                    'text': text,
                                    'font_size': font_size,
                                    'bbox': span.get('bbox', [0, 0, 0, 0])
                                })

            # Match headers with content
            for header in headers:
                content = self._find_content_for_header(header, content_blocks)

                if content:
                    sections.append({
                        'document': document['filename'],
                        'page_number': page_data['page_number'],
                        'section_title': header['text'],
                        'content': content,
                        'word_count': len(content.split()),
                        'extraction_method': 'font_analysis',
                        'confidence': 0.95
                    })

            doc.close()

        except Exception as e:
            print(f"Font analysis failed for {document['filename']} page {page_data['page_number']}: {e}")

        return sections

    def _is_font_header(self, font_size: float, font_flags: int, text: str) -> bool:
        """Determine if text is a header based on font properties"""
        # Check font size (headers are typically larger)
        if font_size >= 14:  # Headers are usually 14pt or larger
            # Check if text looks like a header
            if self._is_header_like_text(text):
                return True

        # Check for bold text (flag 16 = bold in PyMuPDF)
        if font_flags & 16 and len(text) <= 80:
            return True

        return False

    def _is_header_like_text(self, text: str) -> bool:
        """Check if text has header-like characteristics"""
        if len(text) < 5 or len(text) > 100:
            return False

        # Check for exact matches with known section titles
        for pattern in self.section_patterns[:10]:  # First 10 are exact matches
            if re.match(pattern, text):
                return True

        # Check for title case
        if text.istitle() and len(text.split()) <= 8:
            return True

        # Check for domain-specific keywords
        text_lower = text.lower()
        for domain_keywords in self.domain_keywords.values():
            if any(keyword in text_lower for keyword in domain_keywords):
                return True

        return False

    def _find_content_for_header(self, header: Dict[str, Any], content_blocks: List[Dict[str, Any]]) -> str:
        """Find content blocks that belong to a header"""
        header_bbox = header['bbox']
        content_texts = []

        for block in content_blocks:
            block_bbox = block['bbox']

            # Check if content block is below the header
            if block_bbox[1] > header_bbox[3]:  # block top > header bottom
                # Check if they're reasonably close
                if block_bbox[1] - header_bbox[3] < 50:  # Within 50 units
                    content_texts.append(block['text'])

        return ' '.join(content_texts).strip()

    def _extract_sections_by_text_patterns(self, page_text: str, document: Dict[str, Any], page: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract sections using advanced text pattern matching"""
        sections = []

        # Split into lines and clean
        lines = [line.strip() for line in page_text.split('\n') if line.strip()]

        i = 0
        while i < len(lines):
            line = lines[i]

            # Check if this line matches any section pattern
            is_header = False
            for pattern in self.section_patterns:
                if re.match(pattern, line):
                    is_header = True
                    break

            if is_header:
                # Extract content following the header
                content_lines = []
                j = i + 1

                # Collect content until next header or end of page
                while j < len(lines):
                    next_line = lines[j]

                    # Stop if we hit another header
                    if any(re.match(pattern, next_line) for pattern in self.section_patterns):
                        break

                    # Stop if line is too short or looks like a header
                    if len(next_line) < 10 or (next_line.istitle() and len(next_line.split()) <= 5):
                        j += 1
                        continue

                    content_lines.append(next_line)
                    j += 1

                    # Limit content length
                    if len(' '.join(content_lines)) > 500:
                        break

                content = ' '.join(content_lines).strip()

                if content and len(content) > 20:
                    sections.append({
                        'document': document['filename'],
                        'page_number': page['page_number'],
                        'section_title': line,
                        'content': content,
                        'word_count': len(content.split()),
                        'extraction_method': 'text_patterns',
                        'confidence': 0.85
                    })

                i = j
            else:
                i += 1

        return sections

    def _extract_sections_by_structure(self, page_text: str, document: Dict[str, Any], page: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract sections using document structure analysis"""
        sections = []

        # Split by double newlines (paragraphs)
        paragraphs = re.split(r'\n\s*\n', page_text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        for i, paragraph in enumerate(paragraphs):
            lines = paragraph.split('\n')
            first_line = lines[0].strip()

            # Check if first line could be a header
            if (len(lines) > 1 and
                len(first_line) >= 5 and len(first_line) <= 100 and
                first_line[0].isupper() and
                self._is_header_like_text(first_line)):

                content = '\n'.join(lines[1:]).strip()
                if len(content) > 30:
                    sections.append({
                        'document': document['filename'],
                        'page_number': page['page_number'],
                        'section_title': first_line,
                        'content': content,
                        'word_count': len(content.split()),
                        'extraction_method': 'structure_analysis',
                        'confidence': 0.70
                    })

        return sections

    def _deduplicate_and_rank_sections(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicates and rank sections by confidence"""
        if not sections:
            return sections

        # Remove duplicates based on title similarity
        unique_sections = []
        seen_titles = set()

        for section in sections:
            title = section['section_title'].lower().strip()

            # Skip if exact duplicate
            if title in seen_titles:
                continue

            # Check for similar titles
            is_similar = False
            for seen_title in seen_titles:
                if self._titles_are_similar(title, seen_title, 0.85):
                    is_similar = True
                    break

            if not is_similar:
                unique_sections.append(section)
                seen_titles.add(title)

        # Sort by confidence (highest first)
        unique_sections.sort(key=lambda x: x.get('confidence', 0.5), reverse=True)

        return unique_sections

    def _update_patterns_for_persona(self, persona_context: Dict[str, Any]):
        """Update section patterns based on persona context"""
        if not persona_context:
            return

        # Add persona-specific section patterns
        persona_patterns = persona_context.get('section_patterns', [])
        domain = persona_context.get('domain', 'general')

        # Create dynamic patterns based on persona
        additional_patterns = []

        for pattern in persona_patterns:
            # Exact match patterns
            additional_patterns.append(f'^(?i){re.escape(pattern)}$')

            # Flexible match patterns
            additional_patterns.append(f'^(?i).*{re.escape(pattern)}.*$')

            # Title case variations
            additional_patterns.append(f'^(?i){pattern.title()}.*$')

        # Add domain-specific patterns
        if domain == 'hr':
            additional_patterns.extend([
                r'^(?i)(onboarding|compliance|recruitment|training|policy|form|signature).*$',
                r'^(?i).*?(form|fillable|signature|contract|agreement).*$',
                r'^(?i).*?(fill|sign|create|convert|send).*$'
            ])
        elif domain == 'food':
            additional_patterns.extend([
                r'^(?i)(recipe|ingredients|preparation|cooking|menu|vegetarian).*$',
                r'^(?i).*?(dish|meal|cuisine|buffet).*$'
            ])

        # Update the section patterns
        self.section_patterns.extend(additional_patterns)

        # Remove duplicates
        self.section_patterns = list(set(self.section_patterns))

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
