# =============================================================================
# DDx Sliding Context Windows
# =============================================================================

"""
Sliding context window system for multi-agent collaboration.

Enables genuine epistemic labor division by allowing agents to see and respond
to each other's reasoning. Context is filtered based on round type and agent
specialty to keep prompts focused and within token limits.

Key features:
- Multiple filter types (recent, high-confidence, opposing views, key exchanges)
- Round-specific filter combinations
- High-value interaction detection
- Intelligent truncation preserving complete entries
"""

import re
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum


# =============================================================================
# Transcript Entry
# =============================================================================

@dataclass
class TranscriptEntry:
    """A single entry in the global transcript"""
    round_type: str
    round_number: int
    agent_name: str
    specialty: str
    content: str
    timestamp: float
    confidence: float = 0.5
    reasoning_quality: str = "standard"  # basic, standard, high
    is_high_value: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            'round_type': self.round_type,
            'round_number': self.round_number,
            'agent_name': self.agent_name,
            'specialty': self.specialty,
            'content': self.content,
            'timestamp': self.timestamp,
            'confidence': self.confidence,
            'reasoning_quality': self.reasoning_quality,
            'is_high_value': self.is_high_value,
            'metadata': self.metadata
        }


# =============================================================================
# Filter Types
# =============================================================================

class ContextFilter(Enum):
    """Available context filters"""
    RECENT_ROUNDS = "recent_rounds"
    HIGH_CONFIDENCE = "high_confidence"
    OPPOSING_VIEWS = "opposing_views"
    KEY_EXCHANGES = "key_exchanges"
    SPECIALIST_RELEVANT = "specialist_relevant"


# Round-specific filter combinations
ROUND_FILTERS: Dict[str, List[ContextFilter]] = {
    "specialized_ranking": [ContextFilter.RECENT_ROUNDS],
    "symptom_management": [ContextFilter.RECENT_ROUNDS],
    "team_differentials": [ContextFilter.RECENT_ROUNDS],
    "master_list": [ContextFilter.HIGH_CONFIDENCE, ContextFilter.SPECIALIST_RELEVANT],
    "refinement": [ContextFilter.OPPOSING_VIEWS, ContextFilter.HIGH_CONFIDENCE, ContextFilter.KEY_EXCHANGES],
    "voting": [ContextFilter.KEY_EXCHANGES, ContextFilter.HIGH_CONFIDENCE],
    "cant_miss": [ContextFilter.OPPOSING_VIEWS, ContextFilter.HIGH_CONFIDENCE],
    # Simplified names for compatibility
    "differential": [ContextFilter.RECENT_ROUNDS],
    "debate": [ContextFilter.OPPOSING_VIEWS, ContextFilter.HIGH_CONFIDENCE, ContextFilter.KEY_EXCHANGES],
}

# Collaboration guidance per round type
COLLABORATION_GUIDANCE: Dict[str, str] = {
    "specialized_ranking": "Consider how your specialty's perspective adds to the team assessment.",
    "symptom_management": "Focus on immediate patient stabilization from your specialty's view.",
    "team_differentials": "Provide your independent differential. You'll collaborate in later rounds.",
    "master_list": "Review the team's diagnoses to identify the comprehensive differential.",
    "refinement": "Focus on statements that contradict your prior reasoning, or introduce new evidence. You may reinforce, challenge, or synthesize these perspectives.",
    "voting": "Consider which arguments were most compelling and well-supported by evidence.",
    "cant_miss": "Pay attention to any critical conditions that others may have overlooked.",
    "differential": "Provide your independent differential based on your specialty expertise.",
    "debate": "Engage with your colleagues' reasoning. Challenge, support, or refine based on clinical evidence.",
}


# =============================================================================
# High-Value Detection
# =============================================================================

# Reasoning markers that indicate high-value content
REASONING_MARKERS = [
    'evidence', 'contradict', 'disagree', 'alternative', 'challenge',
    'support', 'clinical reasoning', 'risk factor', 'unlikely',
    'more likely', 'less probable', 'consider', 'differential',
    'pathophysiology', 'mechanism', 'presentation', 'findings'
]


def detect_high_value(content: str, confidence: float) -> bool:
    """
    Detect if a response is high-value for context inclusion.

    High-value if:
    - (confidence > 0.7 AND >= 2 reasoning markers) OR
    - (>= 4 reasoning markers regardless of confidence)
    """
    content_lower = content.lower()
    marker_count = sum(1 for marker in REASONING_MARKERS if marker in content_lower)

    if confidence > 0.7 and marker_count >= 2:
        return True
    if marker_count >= 4:
        return True

    return False


def assess_reasoning_quality(content: str) -> str:
    """Assess the reasoning quality of a response"""
    content_lower = content.lower()
    marker_count = sum(1 for marker in REASONING_MARKERS if marker in content_lower)

    # Check for structured reasoning
    has_structure = any(pattern in content for pattern in [
        '1.', '2.', '- ', '• ', 'First,', 'Second,', 'Additionally,'
    ])

    if marker_count >= 5 and has_structure and len(content) > 400:
        return "high"
    elif marker_count >= 2 or len(content) > 200:
        return "standard"
    else:
        return "basic"


# =============================================================================
# Global Transcript Manager
# =============================================================================

class TranscriptManager:
    """
    Manages the global transcript and provides filtered context.

    The transcript records all agent responses across all rounds,
    enabling sliding context windows where later agents can see
    and respond to earlier contributions.
    """

    def __init__(self, max_context_length: int = 1500):
        self.entries: List[TranscriptEntry] = []
        self.max_context_length = max_context_length
        self.round_counter: Dict[str, int] = {}

    def add_entry(self, round_type: str, agent_name: str, specialty: str,
                  content: str, confidence: float = 0.5,
                  metadata: Optional[Dict] = None) -> TranscriptEntry:
        """Add a new entry to the transcript"""

        # Track round numbers
        if round_type not in self.round_counter:
            self.round_counter[round_type] = 0
        self.round_counter[round_type] += 1

        # Assess quality and high-value status
        reasoning_quality = assess_reasoning_quality(content)
        is_high_value = detect_high_value(content, confidence)

        entry = TranscriptEntry(
            round_type=round_type,
            round_number=self.round_counter[round_type],
            agent_name=agent_name,
            specialty=specialty,
            content=content,
            timestamp=time.time(),
            confidence=confidence,
            reasoning_quality=reasoning_quality,
            is_high_value=is_high_value,
            metadata=metadata or {}
        )

        self.entries.append(entry)
        return entry

    def get_filtered_context(self, round_type: str, agent_name: str,
                             agent_specialty: str) -> str:
        """
        Get filtered context for an agent based on round type.

        Applies round-specific filters and builds a context string
        that fits within token limits.
        """
        if not self.entries:
            return ""

        # Get filters for this round type
        filters = ROUND_FILTERS.get(round_type, [ContextFilter.RECENT_ROUNDS])

        # Apply filters to get relevant entries
        filtered_entries = self._apply_filters(filters, agent_name, agent_specialty)

        if not filtered_entries:
            return ""

        # Build context string
        context = self._build_context_string(round_type, filtered_entries)

        return context

    def _apply_filters(self, filters: List[ContextFilter],
                       agent_name: str, agent_specialty: str) -> List[TranscriptEntry]:
        """Apply filter combination to entries"""

        if not filters:
            return []

        # Start with all entries except the current agent's
        candidates = [e for e in self.entries if e.agent_name != agent_name]

        if not candidates:
            return []

        # Use dict keyed by timestamp for deduplication (timestamps are unique)
        filtered: Dict[float, TranscriptEntry] = {}

        for filter_type in filters:
            if filter_type == ContextFilter.RECENT_ROUNDS:
                # Last 8 entries by timestamp
                recent = sorted(candidates, key=lambda x: x.timestamp, reverse=True)[:8]
                for entry in recent:
                    filtered[entry.timestamp] = entry

            elif filter_type == ContextFilter.HIGH_CONFIDENCE:
                # Entries with confidence > 0.7
                for entry in candidates:
                    if entry.confidence > 0.7:
                        filtered[entry.timestamp] = entry

            elif filter_type == ContextFilter.OPPOSING_VIEWS:
                # Entries with contradiction indicators
                opposing_markers = ['disagree', 'however', 'alternatively', 'contradict',
                                   'unlikely', 'less likely', 'challenge', 'but']
                for entry in candidates:
                    if any(m in entry.content.lower() for m in opposing_markers):
                        filtered[entry.timestamp] = entry

            elif filter_type == ContextFilter.KEY_EXCHANGES:
                # High-value or high-confidence interactions
                for entry in candidates:
                    if entry.is_high_value or entry.confidence > 0.8:
                        filtered[entry.timestamp] = entry

            elif filter_type == ContextFilter.SPECIALIST_RELEVANT:
                # Entries mentioning this agent's specialty
                specialty_lower = agent_specialty.lower()
                specialty_terms = [specialty_lower, specialty_lower.replace(' ', '')]
                for entry in candidates:
                    if any(term in entry.content.lower() for term in specialty_terms):
                        filtered[entry.timestamp] = entry

        # Sort by timestamp (oldest first for narrative flow)
        return sorted(filtered.values(), key=lambda x: x.timestamp)

    def _build_context_string(self, round_type: str,
                              entries: List[TranscriptEntry]) -> str:
        """Build formatted context string from entries"""

        # Get collaboration guidance
        guidance = COLLABORATION_GUIDANCE.get(round_type, "")

        parts = []
        if guidance:
            parts.append(f"[Collaboration Note: {guidance}]\n")

        parts.append("Previous team discussion:\n")

        current_length = sum(len(p) for p in parts)
        entry_parts = []

        for entry in entries:
            # Truncate individual entries to 200 chars
            content_preview = entry.content[:200]
            if len(entry.content) > 200:
                content_preview += "..."

            # Add confidence/quality indicators
            indicators = ""
            if entry.confidence > 0.8:
                indicators += " [HIGH CONF]"
            if entry.is_high_value:
                indicators += " [KEY]"

            entry_str = f"• {entry.agent_name} ({entry.specialty}){indicators}:\n  {content_preview}\n"

            # Check if we'd exceed limit
            if current_length + len(entry_str) > self.max_context_length:
                parts.append("\n[... context truncated for length ...]")
                break

            entry_parts.append(entry_str)
            current_length += len(entry_str)

        parts.extend(entry_parts)
        return "\n".join(parts)

    def get_all_entries(self, round_type: Optional[str] = None) -> List[TranscriptEntry]:
        """Get all entries, optionally filtered by round type"""
        if round_type:
            return [e for e in self.entries if e.round_type == round_type]
        return self.entries.copy()

    def get_round_summary(self, round_type: str) -> Dict[str, Any]:
        """Get summary statistics for a round"""
        round_entries = self.get_all_entries(round_type)

        if not round_entries:
            return {'count': 0}

        return {
            'count': len(round_entries),
            'avg_confidence': sum(e.confidence for e in round_entries) / len(round_entries),
            'high_value_count': sum(1 for e in round_entries if e.is_high_value),
            'agents': list(set(e.agent_name for e in round_entries))
        }

    def export_transcript(self) -> List[Dict]:
        """Export full transcript as list of dicts"""
        return [e.to_dict() for e in self.entries]

    def clear(self):
        """Clear all entries"""
        self.entries = []
        self.round_counter = {}


# =============================================================================
# Testing
# =============================================================================

def test_sliding_context():
    """Test the sliding context system"""
    print("Testing Sliding Context System")
    print("=" * 50)

    manager = TranscriptManager()

    # Simulate some entries
    manager.add_entry(
        round_type="differential",
        agent_name="Dr. Chen",
        specialty="Internal Medicine",
        content="Based on the clinical presentation, I suspect acute coronary syndrome. The ST elevation and troponin rise are classic evidence of myocardial infarction.",
        confidence=0.85
    )

    manager.add_entry(
        round_type="differential",
        agent_name="Dr. Torres",
        specialty="Cardiology",
        content="I agree with the ACS assessment. However, we should also consider aortic dissection given the severity of pain. The differential includes STEMI, NSTEMI, and unstable angina.",
        confidence=0.9
    )

    manager.add_entry(
        round_type="differential",
        agent_name="Dr. Patel",
        specialty="Emergency Medicine",
        content="From an ED perspective, immediate management should focus on ruling out STEMI. The ECG findings strongly support this diagnosis.",
        confidence=0.75
    )

    print(f"Added {len(manager.entries)} entries")
    print(f"High-value entries: {sum(1 for e in manager.entries if e.is_high_value)}")

    # Get context for debate round
    context = manager.get_filtered_context(
        round_type="debate",
        agent_name="Dr. Watson",
        agent_specialty="Pulmonology"
    )

    print("\nContext for Dr. Watson (Pulmonology) in debate round:")
    print("-" * 40)
    print(context)

    # Get summary
    summary = manager.get_round_summary("differential")
    print(f"\nRound summary: {summary}")

    return True


if __name__ == "__main__":
    test_sliding_context()
