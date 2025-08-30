import re
from typing import Dict, Any, List

class PersonaAnalyzer:
    def __init__(self):
        # Define specific persona profiles with relevant keywords and section patterns
        self.persona_profiles = {
            'hr professional': {
                'keywords': [
                    'hr', 'human resources', 'onboarding', 'compliance', 'recruitment',
                    'employee', 'training', 'policy', 'form', 'fillable', 'signature',
                    'document', 'contract', 'agreement', 'pdf', 'digital', 'workflow'
                ],
                'section_patterns': [
                    'onboarding', 'compliance', 'recruitment', 'training', 'policy',
                    'form', 'fillable', 'signature', 'contract', 'agreement'
                ],
                'domain': 'hr'
            },
            'food contractor': {
                'keywords': [
                    'food', 'catering', 'menu', 'recipe', 'ingredients', 'vegetarian',
                    'buffet', 'corporate', 'gathering', 'meal', 'dish', 'cuisine',
                    'cooking', 'preparation', 'service', 'nutrition', 'dietary'
                ],
                'section_patterns': [
                    'recipe', 'ingredients', 'preparation', 'cooking', 'menu',
                    'vegetarian', 'buffet', 'meal', 'dish', 'cuisine'
                ],
                'domain': 'food'
            },
            'data analyst': {
                'keywords': [
                    'data', 'analysis', 'analytics', 'reporting', 'metrics', 'kpi',
                    'dashboard', 'visualization', 'insights', 'trends', 'performance',
                    'statistics', 'excel', 'spreadsheet', 'chart', 'graph'
                ],
                'section_patterns': [
                    'analysis', 'metrics', 'kpi', 'reporting', 'dashboard',
                    'insights', 'performance', 'statistics', 'trends'
                ],
                'domain': 'data'
            },
            'business analyst': {
                'keywords': [
                    'business', 'strategy', 'process', 'requirements', 'stakeholder',
                    'workflow', 'efficiency', 'optimization', 'roi', 'feasibility',
                    'implementation', 'change management', 'gap analysis'
                ],
                'section_patterns': [
                    'strategy', 'process', 'requirements', 'stakeholder', 'workflow',
                    'efficiency', 'optimization', 'implementation', 'analysis'
                ],
                'domain': 'business'
            },
            'researcher': {
                'keywords': [
                    'research', 'study', 'methodology', 'findings', 'literature',
                    'hypothesis', 'experiment', 'data collection', 'analysis',
                    'conclusion', 'references', 'academic', 'scholarly'
                ],
                'section_patterns': [
                    'methodology', 'findings', 'literature', 'hypothesis',
                    'experiment', 'conclusion', 'references', 'analysis'
                ],
                'domain': 'research'
            },
            'legal counsel': {
                'keywords': [
                    'legal', 'law', 'contract', 'compliance', 'regulation',
                    'liability', 'agreement', 'terms', 'conditions', 'policy',
                    'governance', 'risk', 'litigation', 'intellectual property'
                ],
                'section_patterns': [
                    'legal', 'contract', 'compliance', 'regulation', 'liability',
                    'agreement', 'terms', 'conditions', 'policy', 'governance'
                ],
                'domain': 'legal'
            },
            'technical writer': {
                'keywords': [
                    'documentation', 'manual', 'guide', 'procedure', 'instruction',
                    'technical', 'specification', 'user guide', 'api', 'tutorial',
                    'reference', 'implementation', 'configuration', 'deployment'
                ],
                'section_patterns': [
                    'documentation', 'manual', 'guide', 'procedure', 'instruction',
                    'specification', 'tutorial', 'reference', 'implementation'
                ],
                'domain': 'technical'
            },
            'student': {
                'keywords': [
                    'study', 'learning', 'education', 'assignment', 'research',
                    'notes', 'lecture', 'course', 'exam', 'project', 'homework',
                    'academic', 'curriculum', 'syllabus', 'grade'
                ],
                'section_patterns': [
                    'study', 'learning', 'assignment', 'research', 'notes',
                    'lecture', 'course', 'exam', 'project', 'homework'
                ],
                'domain': 'education'
            },
            'consultant': {
                'keywords': [
                    'consulting', 'advisory', 'strategy', 'implementation', 'assessment',
                    'recommendation', 'expertise', 'solution', 'client', 'engagement',
                    'deliverable', 'methodology', 'best practice', 'framework'
                ],
                'section_patterns': [
                    'strategy', 'assessment', 'recommendation', 'solution',
                    'methodology', 'framework', 'implementation', 'deliverable'
                ],
                'domain': 'consulting'
            },
            'manager': {
                'keywords': [
                    'management', 'team', 'leadership', 'performance', 'goal',
                    'objective', 'planning', 'budget', 'resource', 'project',
                    'deadline', 'milestone', 'stakeholder', 'communication'
                ],
                'section_patterns': [
                    'management', 'team', 'leadership', 'performance', 'planning',
                    'project', 'budget', 'resource', 'communication'
                ],
                'domain': 'management'
            }
        }

        # Generic fallback for unknown personas
        self.generic_profile = {
            'keywords': ['analysis', 'information', 'content', 'document', 'section'],
            'section_patterns': ['overview', 'summary', 'details', 'information'],
            'domain': 'general'
        }

    def analyze_persona(self, persona: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, Any]:
        """Advanced persona analysis with domain-specific context"""
        persona_role = persona.get('role', '').strip().lower()
        job_task = job.get('task', '').strip()

        # Get persona profile
        profile = self._get_persona_profile(persona_role)

        # Extract job-specific keywords
        job_keywords = self._extract_job_keywords(job_task, profile['domain'])

        # Create comprehensive keyword list
        all_keywords = list(set(
            profile['keywords'] +
            job_keywords +
            self._extract_action_words(job_task)
        ))

        # Create section matching patterns
        section_patterns = self._create_section_patterns(profile, job_task)

        context = {
            'persona_role': persona_role,
            'job_task': job_task.lower(),
            'keywords': all_keywords,
            'section_patterns': section_patterns,
            'domain': profile['domain'],
            'combined_query': f"{persona_role} {job_task}".lower(),
            'persona_profile': profile,
            'relevance_weights': self._calculate_relevance_weights(profile, job_task)
        }

        return context

    def _get_persona_profile(self, persona_role: str) -> Dict[str, Any]:
        """Get the appropriate persona profile"""
        # Try exact match first
        if persona_role in self.persona_profiles:
            return self.persona_profiles[persona_role]

        # Try partial match
        for profile_name, profile in self.persona_profiles.items():
            if profile_name in persona_role or persona_role in profile_name:
                return profile

        # Return generic profile as fallback
        return self.generic_profile

    def _extract_job_keywords(self, job_task: str, domain: str) -> List[str]:
        """Extract job-specific keywords with domain context"""
        if not job_task:
            return []

        # Domain-specific keyword extraction
        domain_keywords = {
            'hr': ['onboarding', 'compliance', 'recruitment', 'training', 'policy', 'form', 'signature'],
            'food': ['vegetarian', 'buffet', 'menu', 'recipe', 'ingredients', 'corporate', 'gathering'],
            'data': ['metrics', 'kpi', 'analysis', 'reporting', 'dashboard', 'insights', 'performance'],
            'business': ['strategy', 'process', 'requirements', 'stakeholder', 'efficiency', 'optimization'],
            'research': ['methodology', 'findings', 'hypothesis', 'experiment', 'conclusion', 'literature'],
            'legal': ['contract', 'compliance', 'regulation', 'liability', 'agreement', 'terms'],
            'technical': ['documentation', 'manual', 'guide', 'procedure', 'specification', 'api'],
            'education': ['study', 'learning', 'assignment', 'research', 'course', 'exam'],
            'consulting': ['strategy', 'assessment', 'recommendation', 'solution', 'methodology'],
            'management': ['team', 'leadership', 'performance', 'planning', 'budget', 'resource']
        }

        # Extract words from job task
        words = re.findall(r'\b[a-zA-Z]{3,}\b', job_task.lower())

        # Filter relevant words based on domain
        relevant_words = []
        domain_words = domain_keywords.get(domain, [])

        for word in words:
            # Include domain-specific words
            if word in domain_words:
                relevant_words.append(word)
            # Include action-oriented words
            elif self._is_action_word(word):
                relevant_words.append(word)
            # Include specific terms (not stop words)
            elif len(word) > 4 and not self._is_stop_word(word):
                relevant_words.append(word)

        return list(set(relevant_words))

    def _extract_action_words(self, text: str) -> List[str]:
        """Extract action-oriented words from text"""
        if not text:
            return []

        action_patterns = [
            r'\b(create|convert|fill|send|change|set up|enable|prepare|analyze|review|manage|process)\b',
            r'\b(\w+ing|\w+ed|\w+er)\b',
            r'\b(\w+)\s+(forms?|documents?|files?|data)\b'
        ]

        actions = []
        for pattern in action_patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                if isinstance(matches[0], tuple):
                    actions.extend([match[0] for match in matches if match[0]])
                else:
                    actions.extend(matches)

        return list(set(actions))

    def _create_section_patterns(self, profile: Dict[str, Any], job_task: str) -> List[str]:
        """Create section matching patterns based on persona and job"""
        patterns = profile['section_patterns'].copy()

        # Add job-specific patterns
        job_lower = job_task.lower()

        if 'form' in job_lower or 'fillable' in job_lower:
            patterns.extend(['form', 'fillable', 'interactive', 'field'])
        if 'signature' in job_lower or 'sign' in job_lower:
            patterns.extend(['signature', 'sign', 'esign', 'electronic'])
        if 'vegetarian' in job_lower or 'buffet' in job_lower:
            patterns.extend(['vegetarian', 'buffet', 'menu', 'recipe'])
        if 'analysis' in job_lower or 'metrics' in job_lower:
            patterns.extend(['analysis', 'metrics', 'kpi', 'performance'])

        return list(set(patterns))

    def _calculate_relevance_weights(self, profile: Dict[str, Any], job_task: str) -> Dict[str, float]:
        """Calculate relevance weights for different content types"""
        weights = {
            'exact_match': 1.0,
            'keyword_match': 0.8,
            'domain_match': 0.6,
            'context_match': 0.4
        }

        # Adjust weights based on job complexity
        if len(job_task.split()) > 10:
            weights['context_match'] *= 1.2

        return weights

    def _is_action_word(self, word: str) -> bool:
        """Check if word is action-oriented"""
        action_suffixes = ['ing', 'ed', 'er', 'ize', 'ify', 'ate']
        return any(word.endswith(suffix) for suffix in action_suffixes)

    def _is_stop_word(self, word: str) -> bool:
        """Check if word is a stop word"""
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'should', 'could', 'can', 'may',
            'might', 'must', 'a', 'an', 'this', 'that', 'these', 'those', 'from'
        }
        return word in stop_words

    def _extract_keywords_generic(self, text: str) -> List[str]:
        if not text:
            return []
        
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'should', 'could', 'can', 'may',
            'might', 'must', 'a', 'an', 'this', 'that', 'these', 'those', 'from'
        }
        
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        meaningful_words = [word for word in words if word not in stop_words]
        
        return list(set(meaningful_words))
    
    def _extract_dynamic_actions(self, text: str) -> List[str]:
        if not text:
            return []
        
        action_patterns = [
            r'\b(\w+)\s+(?:a|an|the|some|many|all)\s+\w+',
            r'\b(\w+)\s+\w+(?:ing|ed|er|ly)\b',
            r'\b(\w+)\s+(?:and|or)\s+\w+',
        ]
        
        actions = []
        for pattern in action_patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                actions.extend(matches)
        
        verb_endings = ['ate', 'ize', 'ify', 'ise']
        filtered_actions = []
        
        for word in actions:
            if (len(word) > 3 and 
                (any(word.endswith(ending) for ending in verb_endings) or
                 word.endswith('e') or word.endswith('y'))):
                filtered_actions.append(word)
        
        return list(set(filtered_actions))
