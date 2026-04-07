# =============================================================================
# DDx Synthesis - Credibility, TempoScore, and Voting
# =============================================================================

"""
Synthesis module for diagnostic pipeline evaluation and voting.

Implements:
- TempoScore: Round-by-round performance metrics
- Dr. Reed Assessment: Agent credibility scoring
- Preferential Voting: Borda count with credibility weighting
- Diagnosis Consolidation: Normalization and deduplication
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Set
from collections import defaultdict

from ddx_sliding_context import TranscriptManager, REASONING_MARKERS


# =============================================================================
# Diagnosis Normalization
# =============================================================================

# Common abbreviation expansions
ABBREVIATIONS = {
    'mi': 'myocardial infarction',
    'stemi': 'st elevation myocardial infarction',
    'nstemi': 'non-st elevation myocardial infarction',
    'acs': 'acute coronary syndrome',
    'pe': 'pulmonary embolism',
    'dvt': 'deep vein thrombosis',
    'chf': 'congestive heart failure',
    'copd': 'chronic obstructive pulmonary disease',
    'uti': 'urinary tract infection',
    'aki': 'acute kidney injury',
    'ckd': 'chronic kidney disease',
    'cva': 'cerebrovascular accident',
    'tia': 'transient ischemic attack',
    'dm': 'diabetes mellitus',
    'htn': 'hypertension',
    'afib': 'atrial fibrillation',
    'gerd': 'gastroesophageal reflux disease',
}


def normalize_diagnosis(diagnosis: str) -> str:
    """
    Normalize a diagnosis name for comparison and deduplication.

    Steps:
    1. Remove numbering and bullets
    2. Convert to lowercase
    3. Expand abbreviations
    4. Remove extra whitespace
    5. Convert to title case
    """
    # Remove numbering and bullets
    normalized = re.sub(r'^[\d\.\-\•\*]+\s*', '', diagnosis.strip())

    # Lowercase for processing
    normalized = normalized.lower().strip()

    # Expand abbreviations
    for abbrev, expansion in ABBREVIATIONS.items():
        # Match whole word only
        pattern = r'\b' + abbrev + r'\b'
        if re.search(pattern, normalized):
            normalized = re.sub(pattern, expansion, normalized)

    # Remove extra whitespace
    normalized = ' '.join(normalized.split())

    # Title case
    normalized = normalized.title()

    return normalized


def diagnoses_similar(diag1: str, diag2: str, threshold: float = 0.6) -> bool:
    """
    Check if two diagnoses are clinically similar.

    Uses token overlap and string similarity.
    """
    norm1 = normalize_diagnosis(diag1).lower()
    norm2 = normalize_diagnosis(diag2).lower()

    if norm1 == norm2:
        return True

    # Token overlap
    tokens1 = set(norm1.split())
    tokens2 = set(norm2.split())

    if not tokens1 or not tokens2:
        return False

    overlap = len(tokens1 & tokens2)
    min_len = min(len(tokens1), len(tokens2))

    token_sim = overlap / min_len if min_len > 0 else 0

    # Check for substring containment
    if norm1 in norm2 or norm2 in norm1:
        return True

    return token_sim >= threshold


def consolidate_diagnoses(diagnoses: List[str]) -> List[str]:
    """
    Consolidate a list of diagnoses by merging similar ones.

    Returns list of unique, normalized diagnoses.
    """
    if not diagnoses:
        return []

    normalized = [normalize_diagnosis(d) for d in diagnoses]
    consolidated = []

    for diag in normalized:
        is_duplicate = False
        for existing in consolidated:
            if diagnoses_similar(diag, existing):
                is_duplicate = True
                break
        if not is_duplicate:
            consolidated.append(diag)

    return consolidated


# =============================================================================
# TempoScore
# =============================================================================

@dataclass
class TempoScore:
    """Round-by-round performance metrics"""
    round_type: str
    score: float
    components: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


def calculate_differential_tempo(responses: List[Any]) -> TempoScore:
    """
    Calculate TempoScore for differential diagnosis round.

    Formula: 1.0 + (0.1 × unique_diagnoses_count)
    """
    all_diagnoses = set()

    for resp in responses:
        if resp.structured_data and isinstance(resp.structured_data, dict):
            for diag in resp.structured_data.keys():
                all_diagnoses.add(normalize_diagnosis(diag))

    unique_count = len(all_diagnoses)
    score = 1.0 + (0.1 * unique_count)

    return TempoScore(
        round_type="differential",
        score=min(2.5, score),
        components={'unique_diagnoses': unique_count},
        metadata={'diagnoses': list(all_diagnoses)}
    )


def calculate_refinement_tempo(transcript: TranscriptManager,
                                agent_count: int) -> TempoScore:
    """
    Calculate TempoScore for refinement/debate round.

    Uses "symbolic curvature" based on high-value interactions.
    Formula: min(symbolic_curvature + 0.5, 2.5)
    """
    entries = transcript.get_all_entries("refinement") or transcript.get_all_entries("debate")

    if not entries:
        return TempoScore(round_type="refinement", score=1.0)

    # Count high-value interactions
    high_value_count = sum(1 for e in entries if e.is_high_value)

    # Count specific interaction types
    challenges = 0
    position_changes = 0
    evidence_citations = 0

    for entry in entries:
        content_lower = entry.content.lower()

        # Count challenges
        challenges += len(re.findall(r'\b(?:challenge|disagree|however|but)\b', content_lower))

        # Count position changes
        position_changes += len(re.findall(
            r'\b(?:convinced|agree now|changed? my|reconsidering|you\'re right)\b',
            content_lower
        ))

        # Count evidence citations
        evidence_citations += len(re.findall(
            r'\b(?:evidence|study|research|literature|guideline|data)\b',
            content_lower
        ))

    # Symbolic curvature
    minimum_expected = max(agent_count, 1)
    symbolic_curvature = high_value_count / minimum_expected

    score = min(symbolic_curvature + 0.5, 2.5)

    return TempoScore(
        round_type="refinement",
        score=score,
        components={
            'high_value_interactions': high_value_count,
            'symbolic_curvature': symbolic_curvature,
            'direct_challenges': challenges,
            'position_changes': position_changes,
            'evidence_citations': evidence_citations
        },
        metadata={'agent_count': agent_count}
    )


# =============================================================================
# Dr. Reed Credibility Assessment
# =============================================================================

@dataclass
class CredibilityScore:
    """Agent credibility assessment"""
    agent_name: str
    base_score: float
    valence_multiplier: float
    final_score: float
    components: Dict[str, float] = field(default_factory=dict)


# Elevating indicators for professional valence
ELEVATING_INDICATORS = [
    'evidence', 'research', 'studies', 'guidelines', 'consider',
    'alternative', 'question', 'challenge', 'disagree', 'differential',
    'pathophysiology', 'mechanism'
]


def assess_agent_credibility(agent_name: str, responses: List[Any]) -> CredibilityScore:
    """
    Assess agent credibility using Dr. Reed methodology.

    Components:
    - insight_score: Diagnostic quality (diagnoses × 3 + avg_evidence × 2)
    - synthesis_score: Diagnostic breadth (diagnoses × 4)
    - action_score: Actionability (well-evidenced first diagnosis = 20)

    Base_DES = (2.5 × insight) + (1.5 × synthesis) + (1.0 × action)
    Final = Base_DES × Professional_Valence
    """
    agent_responses = [r for r in responses if r.agent_name == agent_name]

    if not agent_responses:
        return CredibilityScore(agent_name=agent_name, base_score=0,
                                valence_multiplier=1.0, final_score=0)

    # Collect all diagnoses and evidence
    all_diagnoses = []
    total_evidence = 0

    for resp in agent_responses:
        if resp.structured_data and isinstance(resp.structured_data, dict):
            for diag, evidence in resp.structured_data.items():
                all_diagnoses.append(diag)
                if isinstance(evidence, list):
                    total_evidence += len(evidence)

    num_diagnoses = len(all_diagnoses)
    avg_evidence = total_evidence / num_diagnoses if num_diagnoses > 0 else 0

    # Calculate component scores
    insight_score = (num_diagnoses * 3) + (avg_evidence * 2)
    synthesis_score = num_diagnoses * 4

    # Action score: well-evidenced first diagnosis
    action_score = 0
    if agent_responses and agent_responses[0].structured_data:
        first_diag_data = agent_responses[0].structured_data
        if first_diag_data:
            first_key = list(first_diag_data.keys())[0]
            first_evidence = first_diag_data.get(first_key, [])
            if isinstance(first_evidence, list) and len(first_evidence) >= 2:
                action_score = 20

    # Base Diagnostic Excellence Score
    base_des = (2.5 * insight_score) + (1.5 * synthesis_score) + (1.0 * action_score)

    # Professional Valence Multiplier
    total_content = ' '.join(r.content for r in agent_responses)
    content_length = len(total_content)
    elevating_count = sum(1 for ind in ELEVATING_INDICATORS if ind in total_content.lower())

    if elevating_count >= 4 and content_length > 200:
        valence = 1.2  # Significantly elevated
    elif elevating_count >= 2 and content_length > 100:
        valence = 1.0  # Professional
    elif content_length > 50:
        valence = 0.8  # Basic
    else:
        valence = 0.6  # Minimal

    final_score = base_des * valence

    return CredibilityScore(
        agent_name=agent_name,
        base_score=base_des,
        valence_multiplier=valence,
        final_score=final_score,
        components={
            'insight_score': insight_score,
            'synthesis_score': synthesis_score,
            'action_score': action_score,
            'diagnoses_count': num_diagnoses,
            'avg_evidence': avg_evidence,
            'elevating_indicators': elevating_count
        }
    )


def assess_all_agents(agents: List[Any], responses: List[Any]) -> Dict[str, CredibilityScore]:
    """Assess credibility for all agents"""
    scores = {}
    for agent in agents:
        scores[agent.name] = assess_agent_credibility(agent.name, responses)
    return scores


# =============================================================================
# Preferential Voting with Borda Count
# =============================================================================

@dataclass
class VotingResult:
    """Results from preferential voting"""
    winner: str
    ranked_results: List[Tuple[str, float]]  # (diagnosis, weighted_score)
    borda_scores: Dict[str, int]  # Raw Borda scores
    credibility_weighted: Dict[str, float]  # After credibility weighting
    all_rankings: Dict[str, List[str]]  # Each agent's ranking
    total_votes: int
    metadata: Dict[str, Any] = field(default_factory=dict)


def tally_borda_votes(agent_votes: Dict[str, List[str]],
                       credibility_scores: Optional[Dict[str, CredibilityScore]] = None,
                       max_rank: int = 3) -> VotingResult:
    """
    Tally preferential votes using Borda count with optional credibility weighting.

    Borda points:
    - 1st choice: 3 points
    - 2nd choice: 2 points
    - 3rd choice: 1 point

    With credibility weighting:
    - Each agent's contribution is scaled by their credibility score
    - Credibility capped at 2× median to prevent dominance
    """
    if not agent_votes:
        return VotingResult(
            winner="No votes",
            ranked_results=[],
            borda_scores={},
            credibility_weighted={},
            all_rankings={},
            total_votes=0
        )

    # Normalize all diagnoses first
    normalized_votes: Dict[str, List[str]] = {}
    for agent, rankings in agent_votes.items():
        normalized_votes[agent] = [normalize_diagnosis(d) for d in rankings[:max_rank]]

    # Raw Borda tally
    borda_scores: Dict[str, int] = defaultdict(int)
    for agent, rankings in normalized_votes.items():
        for position, diagnosis in enumerate(rankings):
            points = max_rank - position  # 3, 2, 1
            borda_scores[diagnosis] += points

    # Credibility-weighted tally
    credibility_weighted: Dict[str, float] = defaultdict(float)

    if credibility_scores:
        # Calculate median for capping
        cred_values = [cs.final_score for cs in credibility_scores.values() if cs.final_score > 0]
        median_cred = sorted(cred_values)[len(cred_values) // 2] if cred_values else 1.0
        cap = 2 * median_cred

        for agent, rankings in normalized_votes.items():
            agent_cred = credibility_scores.get(agent)
            if agent_cred:
                capped_cred = min(agent_cred.final_score, cap)
            else:
                capped_cred = 1.0

            for position, diagnosis in enumerate(rankings):
                points = max_rank - position
                credibility_weighted[diagnosis] += points * capped_cred
    else:
        # Without credibility, use raw scores
        credibility_weighted = {k: float(v) for k, v in borda_scores.items()}

    # Rank by credibility-weighted score
    ranked = sorted(credibility_weighted.items(), key=lambda x: x[1], reverse=True)

    winner = ranked[0][0] if ranked else "No consensus"

    return VotingResult(
        winner=winner,
        ranked_results=ranked,
        borda_scores=dict(borda_scores),
        credibility_weighted=dict(credibility_weighted),
        all_rankings=normalized_votes,
        total_votes=len(agent_votes),
        metadata={'median_credibility': median_cred if credibility_scores else None}
    )


def extract_votes_from_responses(responses: List[Any]) -> Dict[str, List[str]]:
    """Extract preferential votes from agent responses"""
    votes = {}

    for resp in responses:
        if resp.round_type != "voting":
            continue

        rankings = []

        # Try structured data first
        if resp.structured_data and 'rankings' in resp.structured_data:
            rankings = resp.structured_data['rankings']

        # Fallback to text extraction
        if not rankings:
            content = resp.content

            # Try various patterns
            patterns = [
                r'(\d)(?:st|nd|rd|th)\s*[Cc]hoice:\s*(.+?)(?:\s+-\s|\n|$)',
                r'(\d)\.\s*(.+?)(?:\s+-\s|\n|$)',
                r'[Ff]irst[^:]*:\s*([^\n]+)',
            ]

            for pattern in patterns:
                matches = re.findall(pattern, content)
                if matches:
                    if len(matches[0]) == 2:  # (position, diagnosis) format
                        rankings = [m[1].strip() for m in matches[:3]]
                    else:
                        rankings = [m.strip() for m in matches[:3]]
                    break

        if rankings:
            votes[resp.agent_name] = rankings

    return votes


# =============================================================================
# Full Synthesis Pipeline
# =============================================================================

@dataclass
class SynthesisResult:
    """Complete synthesis results"""
    final_diagnoses: List[Tuple[str, float]]  # Top diagnoses with scores
    voting_result: Optional[VotingResult]
    tempo_scores: Dict[str, TempoScore]
    credibility_scores: Dict[str, CredibilityScore]
    consolidation_applied: bool
    metadata: Dict[str, Any] = field(default_factory=dict)


def run_synthesis(agents: List[Any],
                   all_responses: List[Any],
                   transcript: TranscriptManager,
                   voting_responses: Optional[List[Any]] = None) -> SynthesisResult:
    """
    Run full synthesis pipeline.

    1. Calculate TempoScores for each round
    2. Assess agent credibility
    3. If voting responses provided, tally with credibility weighting
    4. Consolidate final diagnosis list
    """
    # 1. TempoScores
    tempo_scores = {}

    differential_responses = [r for r in all_responses if r.round_type in ['differential', 'team_differentials']]
    if differential_responses:
        tempo_scores['differential'] = calculate_differential_tempo(differential_responses)

    tempo_scores['refinement'] = calculate_refinement_tempo(transcript, len(agents))

    # 2. Credibility assessment
    credibility_scores = assess_all_agents(agents, all_responses)

    # 3. Voting (if applicable)
    voting_result = None
    if voting_responses:
        votes = extract_votes_from_responses(voting_responses)
        if votes:
            voting_result = tally_borda_votes(votes, credibility_scores)

    # 4. Consolidate diagnoses
    # Decide consolidation level based on refinement TempoScore
    refinement_tempo = tempo_scores.get('refinement')
    aggressive_consolidation = refinement_tempo and refinement_tempo.score >= 1.5

    # Gather all diagnoses
    all_diagnoses = []
    for resp in all_responses:
        if resp.structured_data and isinstance(resp.structured_data, dict):
            all_diagnoses.extend(resp.structured_data.keys())

    consolidated = consolidate_diagnoses(all_diagnoses)

    # If we have voting results, use those rankings
    if voting_result:
        final_diagnoses = voting_result.ranked_results[:6]
    else:
        # Otherwise rank by frequency
        freq = defaultdict(int)
        for diag in all_diagnoses:
            norm = normalize_diagnosis(diag)
            freq[norm] += 1

        final_diagnoses = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:6]

    return SynthesisResult(
        final_diagnoses=final_diagnoses,
        voting_result=voting_result,
        tempo_scores=tempo_scores,
        credibility_scores=credibility_scores,
        consolidation_applied=aggressive_consolidation,
        metadata={
            'total_diagnoses_proposed': len(all_diagnoses),
            'unique_after_consolidation': len(consolidated)
        }
    )


# =============================================================================
# Testing
# =============================================================================

def test_synthesis():
    """Test synthesis components"""
    print("Testing DDx Synthesis")
    print("=" * 50)

    # Test normalization
    test_diags = ["1. MI", "STEMI", "st elevation myocardial infarction", "ACS"]
    print("\nNormalization test:")
    for d in test_diags:
        print(f"  {d} -> {normalize_diagnosis(d)}")

    # Test similarity
    print("\nSimilarity test:")
    print(f"  MI vs STEMI: {diagnoses_similar('MI', 'STEMI')}")
    print(f"  STEMI vs ST Elevation MI: {diagnoses_similar('STEMI', 'ST Elevation MI')}")

    # Test consolidation
    consolidated = consolidate_diagnoses(test_diags)
    print(f"\nConsolidated: {consolidated}")

    # Test Borda voting
    print("\nBorda voting test:")
    test_votes = {
        "Dr. Chen": ["Acute Coronary Syndrome", "Pulmonary Embolism", "Aortic Dissection"],
        "Dr. Torres": ["STEMI", "ACS", "Pericarditis"],
        "Dr. Watson": ["Myocardial Infarction", "PE", "Pneumothorax"]
    }

    result = tally_borda_votes(test_votes)
    print(f"  Winner: {result.winner}")
    print(f"  Ranked: {result.ranked_results[:3]}")

    return True


if __name__ == "__main__":
    test_synthesis()
