# =============================================================================
# DDx Rounds - Full 7-Round Pipeline
# =============================================================================

"""
Complete 7-round diagnostic pipeline implementation.

Rounds:
1. Specialized Ranking - Prioritize specialties for case
2. Symptom Management - Immediate triage protocols
3. Team Differentials - Independent diagnosis generation
4. Master List - Consolidate all diagnoses
5. Refinement & Debate - 3 sub-rounds of structured debate
6. Preferential Voting - Borda count consensus
7. Can't Miss - Critical diagnosis safety check

Each round builds on previous rounds through sliding context windows.
"""

import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable

from ddx_core import DDxAgent, AgentResponse
from ddx_sliding_context import TranscriptManager
from ddx_synthesis import (
    normalize_diagnosis, consolidate_diagnoses,
    extract_votes_from_responses, tally_borda_votes,
    assess_all_agents
)


# =============================================================================
# Round Types
# =============================================================================

class RoundType(Enum):
    """The 7 diagnostic rounds"""
    SPECIALIZED_RANKING = "specialized_ranking"
    SYMPTOM_MANAGEMENT = "symptom_management"
    TEAM_DIFFERENTIALS = "team_differentials"
    MASTER_LIST = "master_list"
    REFINEMENT = "refinement"
    VOTING = "voting"
    CANT_MISS = "cant_miss"


# Round execution order
ROUND_ORDER = [
    RoundType.SPECIALIZED_RANKING,
    RoundType.SYMPTOM_MANAGEMENT,
    RoundType.TEAM_DIFFERENTIALS,
    RoundType.MASTER_LIST,
    RoundType.REFINEMENT,
    RoundType.VOTING,
    RoundType.CANT_MISS,
]


# =============================================================================
# Round Results
# =============================================================================

@dataclass
class RoundResult:
    """Result from a single round"""
    round_type: RoundType
    responses: List[AgentResponse]
    duration: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return len(self.responses) > 0


# =============================================================================
# Round Executors
# =============================================================================

class RoundExecutor:
    """
    Executes diagnostic rounds with proper context management.

    Handles the orchestration of agent responses, context building,
    and result aggregation for each round type.
    """

    def __init__(self, agents: List[DDxAgent], transcript: TranscriptManager,
                 case_description: str):
        self.agents = agents
        self.transcript = transcript
        self.case_description = case_description
        self.round_results: Dict[RoundType, RoundResult] = {}
        self.master_diagnosis_list: List[str] = []

    def execute_round(self, round_type: RoundType,
                       callback: Optional[Callable] = None,
                       token_callback: Optional[Callable] = None) -> RoundResult:
        """
        Execute a single round.

        Args:
            callback: Progress callback(msg, response) for round-level events
            token_callback: Token callback(agent_name, token_text) for streaming
        """
        print(f"\n{'='*60}")
        print(f"ROUND: {round_type.value.upper()}")
        print(f"{'='*60}")

        if callback:
            callback(f"ROUND_START:{round_type.value}", None)

        start_time = time.time()

        # Dispatch to appropriate handler
        handlers = {
            RoundType.SPECIALIZED_RANKING: self._run_specialized_ranking,
            RoundType.SYMPTOM_MANAGEMENT: self._run_symptom_management,
            RoundType.TEAM_DIFFERENTIALS: self._run_team_differentials,
            RoundType.MASTER_LIST: self._run_master_list,
            RoundType.REFINEMENT: self._run_refinement,
            RoundType.VOTING: self._run_voting,
            RoundType.CANT_MISS: self._run_cant_miss,
        }

        handler = handlers.get(round_type)
        if not handler:
            return RoundResult(round_type=round_type, responses=[], duration=0)

        responses = handler(callback, token_callback)

        if callback:
            callback(f"ROUND_COMPLETE:{round_type.value}", None)

        result = RoundResult(
            round_type=round_type,
            responses=responses,
            duration=time.time() - start_time
        )

        self.round_results[round_type] = result
        return result

    def _make_agent_token_cb(self, agent_name: str,
                             token_callback: Optional[Callable]) -> Optional[Callable]:
        """Create a per-agent token callback that tags tokens with agent name."""
        if not token_callback:
            return None
        return lambda token: token_callback(agent_name, token)

    def _run_specialized_ranking(self, callback: Optional[Callable],
                                  token_callback: Optional[Callable] = None) -> List[AgentResponse]:
        """Round 1: Each agent ranks their specialty's relevance"""
        prompt = f"""CLINICAL CASE:
{self.case_description}

Rate the relevance of your specialty ({self.agents[0].specialty.value if self.agents else 'your specialty'}) to this case.
Format: RELEVANCE: [1-10]/10

Then explain:
1. Why your specialty is relevant to this case
2. What aspects you can contribute to the diagnosis
3. Any immediate concerns from your perspective"""

        responses = []
        for agent in self.agents:
            if callback:
                callback(f"Agent {agent.name} ranking...")

            response = agent.generate_response(
                prompt, "specialized_ranking", use_context=False,
                token_callback=self._make_agent_token_cb(agent.name, token_callback),
            )
            responses.append(response)
            if callback:
                callback(f"Agent {agent.name} complete", response)
            print(f"  {agent.name} ({agent.specialty.value}): {response.confidence_score:.2f}")

        return responses

    def _run_symptom_management(self, callback: Optional[Callable],
                                token_callback: Optional[Callable] = None) -> List[AgentResponse]:
        """Round 2: Immediate triage and stabilization"""
        prompt = f"""CLINICAL CASE:
{self.case_description}

From your specialty perspective, identify:
1. IMMEDIATE PRIORITIES - What needs attention right now?
2. STABILIZATION - Initial management steps
3. CRITICAL TESTS - Urgent diagnostics needed
4. RED FLAGS - Warning signs to monitor

Focus on patient safety and acute stabilization."""

        responses = []
        for agent in self.agents:
            if callback:
                callback(f"Agent {agent.name} assessing...")

            response = agent.generate_response(
                prompt, "symptom_management", use_context=True,
                token_callback=self._make_agent_token_cb(agent.name, token_callback),
            )
            responses.append(response)
            if callback:
                callback(f"Agent {agent.name} complete", response)
            print(f"  {agent.name}: Triage assessment complete")

        return responses

    def _run_team_differentials(self, callback: Optional[Callable],
                                token_callback: Optional[Callable] = None) -> List[AgentResponse]:
        """Round 3: Independent differential diagnosis generation"""
        prompt = f"""CLINICAL CASE:
{self.case_description}

Provide your independent differential diagnosis.

Start with a JSON object mapping diagnoses to supporting evidence:
{{"Diagnosis Name": ["evidence1", "evidence2", "evidence3"]}}

Then explain your clinical reasoning for each diagnosis.
List 3-5 diagnoses ranked by likelihood from your specialty's perspective."""

        responses = []
        for agent in self.agents:
            if callback:
                callback(f"Agent {agent.name} generating differential...")

            response = agent.generate_response(
                prompt, "team_differentials", use_context=True,
                token_callback=self._make_agent_token_cb(agent.name, token_callback),
            )
            responses.append(response)
            if callback:
                callback(f"Agent {agent.name} complete", response)

            # Count diagnoses
            dx_count = len(response.structured_data) if response.structured_data else 0
            print(f"  {agent.name}: {dx_count} diagnoses proposed")

        return responses

    def _run_master_list(self, callback: Optional[Callable],
                          token_callback: Optional[Callable] = None) -> List[AgentResponse]:
        """Round 4: Consolidate all diagnoses into master list"""

        # Gather all diagnoses from Round 3
        all_diagnoses = []
        differentials = self.round_results.get(RoundType.TEAM_DIFFERENTIALS)
        if differentials:
            for resp in differentials.responses:
                if resp.structured_data:
                    all_diagnoses.extend(resp.structured_data.keys())

        # Normalize and deduplicate
        self.master_diagnosis_list = consolidate_diagnoses(all_diagnoses)

        prompt = f"""CLINICAL CASE:
{self.case_description}

The team has proposed the following diagnoses:
{chr(10).join(f"- {d}" for d in self.master_diagnosis_list)}

Review this list and:
1. Identify any diagnoses that should be merged (same condition, different names)
2. Flag any diagnoses that seem unlikely given the presentation
3. Note if any important diagnoses are missing
4. Organize by likelihood (most likely first)

Provide a consolidated master list with brief rationale for each."""

        # Only need one agent for synthesis
        responses = []
        synthesizer = self.agents[0] if self.agents else None

        if synthesizer:
            if callback:
                callback("Consolidating diagnoses...")

            response = synthesizer.generate_response(
                prompt, "master_list", use_context=True,
                token_callback=self._make_agent_token_cb(synthesizer.name, token_callback),
            )
            responses.append(response)
            if callback:
                callback(f"Agent {synthesizer.name} complete", response)
            print(f"  Master list created with {len(self.master_diagnosis_list)} unique diagnoses")

        return responses

    def _run_refinement(self, callback: Optional[Callable],
                         token_callback: Optional[Callable] = None) -> List[AgentResponse]:
        """
        Round 5: Structured debate with 3 sub-rounds.

        Sub-round 1: Initial positions
        Sub-round 2: Direct challenges
        Sub-round 3: Responses and final positions
        """
        all_responses = []

        # Build diagnosis context
        dx_list = "\n".join(f"- {d}" for d in self.master_diagnosis_list[:10])

        # =====================================================================
        # Sub-round 1: Initial Positions
        # =====================================================================
        print("\n  Sub-round 1: Initial Positions")

        prompt_sr1 = f"""CLINICAL CASE:
{self.case_description}

DIAGNOSES UNDER CONSIDERATION:
{dx_list}

Establish your initial position on each diagnosis:
- SUPPORT: Diagnoses you believe are likely (with evidence)
- CHALLENGE: Diagnoses you believe are unlikely (with reasoning)
- NEUTRAL: Diagnoses requiring more information

State your TOP 3 diagnoses with confidence levels (HIGH/MEDIUM/LOW).
Provide specific clinical reasoning for each position."""

        for agent in self.agents:
            if callback:
                callback(f"Sub-round 1: {agent.name} establishing position...")

            response = agent.generate_response(
                prompt_sr1, "refinement", use_context=True,
                token_callback=self._make_agent_token_cb(agent.name, token_callback),
            )
            all_responses.append(response)
            if callback:
                callback(f"Agent {agent.name} complete", response)
            print(f"    {agent.name}: Position established")

        # =====================================================================
        # Sub-round 2: Direct Challenges
        # =====================================================================
        print("\n  Sub-round 2: Direct Challenges")

        # Assign challenge targets (round-robin)
        agent_count = len(self.agents)

        for i, agent in enumerate(self.agents):
            # Target is next agent in rotation
            target_idx = (i + 1) % agent_count
            target_agent = self.agents[target_idx]

            prompt_sr2 = f"""CLINICAL CASE:
{self.case_description}

You are now in the CHALLENGE phase of the diagnostic debate.

Your assigned colleague to challenge: {target_agent.name} ({target_agent.specialty.value})

Review {target_agent.name}'s reasoning from the previous sub-round and:
1. DIRECTLY CHALLENGE their top diagnosis with clinical counter-evidence
2. PROPOSE an alternative diagnosis they may have underweighted
3. ASK a specific question about their reasoning
4. CITE evidence that contradicts or complicates their position

Be respectful but rigorous. The goal is diagnostic accuracy through adversarial testing."""

            if callback:
                callback(f"Sub-round 2: {agent.name} challenging {target_agent.name}...")

            response = agent.generate_response(
                prompt_sr2, "refinement", use_context=True,
                token_callback=self._make_agent_token_cb(agent.name, token_callback),
            )
            all_responses.append(response)
            if callback:
                callback(f"Agent {agent.name} complete", response)
            print(f"    {agent.name} challenged {target_agent.name}")

        # =====================================================================
        # Sub-round 3: Responses and Final Positions
        # =====================================================================
        print("\n  Sub-round 3: Final Positions")

        prompt_sr3 = f"""CLINICAL CASE:
{self.case_description}

You are now in the FINAL POSITION phase.

Review the challenges raised against your reasoning and:
1. ADDRESS each challenge directly - accept valid points with intellectual honesty
2. DEFEND positions where you have strong counter-evidence
3. UPDATE your diagnosis ranking if the debate changed your thinking
4. STATE clearly which positions you MAINTAIN vs CHANGED

Your final TOP 3 diagnoses (may differ from initial):
1. [Diagnosis] - [MAINTAINED/CHANGED] - [Brief justification]
2. [Diagnosis] - [MAINTAINED/CHANGED] - [Brief justification]
3. [Diagnosis] - [MAINTAINED/CHANGED] - [Brief justification]"""

        for agent in self.agents:
            if callback:
                callback(f"Sub-round 3: {agent.name} finalizing position...")

            response = agent.generate_response(
                prompt_sr3, "refinement", use_context=True,
                token_callback=self._make_agent_token_cb(agent.name, token_callback),
            )
            all_responses.append(response)
            if callback:
                callback(f"Agent {agent.name} complete", response)
            print(f"    {agent.name}: Final position stated")

        return all_responses

    def _run_voting(self, callback: Optional[Callable],
                     token_callback: Optional[Callable] = None) -> List[AgentResponse]:
        """Round 6: Preferential voting with Borda count"""

        # Get refined diagnosis options
        dx_options = self.master_diagnosis_list[:10] if self.master_diagnosis_list else []

        if not dx_options:
            # Fallback: extract from refinement round
            refinement = self.round_results.get(RoundType.REFINEMENT)
            if refinement:
                for resp in refinement.responses:
                    if resp.structured_data:
                        dx_options.extend(resp.structured_data.keys())
                dx_options = consolidate_diagnoses(dx_options)[:10]

        dx_list = "\n".join(f"  {i+1}. {d}" for i, d in enumerate(dx_options))

        prompt = f"""CLINICAL CASE:
{self.case_description}

VOTING OPTIONS (refined diagnoses):
{dx_list}

Cast your PREFERENTIAL VOTE for the top 3 diagnoses.
Consider the debate evidence and your clinical judgment.

Format your vote EXACTLY as:
<PREFERENTIAL_VOTE>
1st Choice: [Diagnosis from list] - [Brief justification]
2nd Choice: [Diagnosis from list] - [Brief justification]
3rd Choice: [Diagnosis from list] - [Brief justification]
</PREFERENTIAL_VOTE>

Confidence in your ranking: [XX%]"""

        responses = []
        for agent in self.agents:
            if callback:
                callback(f"Agent {agent.name} voting...")

            response = agent.generate_response(
                prompt, "voting", use_context=True,
                token_callback=self._make_agent_token_cb(agent.name, token_callback),
            )
            responses.append(response)
            if callback:
                callback(f"Agent {agent.name} complete", response)

            # Extract vote for display
            vote_data = response.structured_data
            if vote_data and 'rankings' in vote_data:
                print(f"  {agent.name}: Voted for {vote_data['rankings'][0] if vote_data['rankings'] else 'N/A'}")
            else:
                print(f"  {agent.name}: Vote recorded")

        return responses

    def _run_cant_miss(self, callback: Optional[Callable],
                        token_callback: Optional[Callable] = None) -> List[AgentResponse]:
        """Round 7: Critical diagnosis safety check"""

        prompt = f"""CLINICAL CASE:
{self.case_description}

CRITICAL SAFETY CHECK: Identify diagnoses that CANNOT BE MISSED.

For each can't-miss diagnosis:
1. DIAGNOSIS: Name of the critical condition
2. URGENCY: HIGH (immediate threat) or MEDIUM (significant if delayed)
3. WHY CRITICAL: What harm occurs if missed
4. KEY TESTS: Specific diagnostics needed to rule in/out
5. TIME WINDOW: How quickly must this be addressed

Focus on:
- Life-threatening conditions
- Conditions that worsen rapidly without treatment
- Diagnoses with narrow treatment windows
- Conditions that mimic benign presentations"""

        responses = []
        for agent in self.agents:
            if callback:
                callback(f"Agent {agent.name} safety check...")

            response = agent.generate_response(
                prompt, "cant_miss", use_context=True,
                token_callback=self._make_agent_token_cb(agent.name, token_callback),
            )
            responses.append(response)
            if callback:
                callback(f"Agent {agent.name} complete", response)
            print(f"  {agent.name}: Safety assessment complete")

        return responses


# =============================================================================
# Pipeline Runner
# =============================================================================

class DiagnosticPipeline:
    """
    Runs the complete 7-round diagnostic pipeline.

    Manages round execution order, context flow between rounds,
    and final synthesis of results.
    """

    def __init__(self, agents: List[DDxAgent], transcript: TranscriptManager,
                 case_description: str):
        self.executor = RoundExecutor(agents, transcript, case_description)
        self.agents = agents
        self.transcript = transcript

    def run_full_pipeline(self, callback: Optional[Callable] = None,
                           token_callback: Optional[Callable] = None,
                           skip_rounds: Optional[List[RoundType]] = None) -> Dict[str, Any]:
        """
        Run complete diagnostic pipeline.

        Args:
            callback: Optional progress callback function
            token_callback: Optional token callback(agent_name, token) for streaming
            skip_rounds: Optional list of rounds to skip

        Returns:
            Complete pipeline results including all round data and final synthesis
        """
        skip_rounds = skip_rounds or []
        start_time = time.time()

        print("\n" + "="*70)
        print("STARTING FULL DIAGNOSTIC PIPELINE")
        print("="*70)

        results = {
            'rounds': {},
            'final_diagnoses': [],
            'voting_result': None,
            'credibility_scores': {},
            'total_duration': 0
        }

        # Execute each round in order
        for round_type in ROUND_ORDER:
            if round_type in skip_rounds:
                print(f"\nSkipping {round_type.value}...")
                continue

            round_result = self.executor.execute_round(round_type, callback, token_callback)
            results['rounds'][round_type.value] = {
                'responses': [r.to_dict() for r in round_result.responses],
                'duration': round_result.duration,
                'success': round_result.success
            }

        # Final synthesis
        print("\n" + "="*60)
        print("SYNTHESIS")
        print("="*60)

        # Gather all responses
        all_responses = []
        for round_result in self.executor.round_results.values():
            all_responses.extend(round_result.responses)

        # Assess credibility
        credibility_scores = assess_all_agents(self.agents, all_responses)
        results['credibility_scores'] = {
            name: {
                'final_score': cs.final_score,
                'base_score': cs.base_score,
                'valence': cs.valence_multiplier
            }
            for name, cs in credibility_scores.items()
        }

        # Tally votes if voting round completed
        voting_result = self.executor.round_results.get(RoundType.VOTING)
        if voting_result:
            votes = extract_votes_from_responses(voting_result.responses)
            if votes:
                vote_tally = tally_borda_votes(votes, credibility_scores)
                results['voting_result'] = {
                    'winner': vote_tally.winner,
                    'ranked': vote_tally.ranked_results[:6],
                    'total_votes': vote_tally.total_votes
                }
                results['final_diagnoses'] = [d[0] for d in vote_tally.ranked_results[:6]]

                print(f"\nFinal Diagnosis Ranking:")
                for i, (diag, score) in enumerate(vote_tally.ranked_results[:6], 1):
                    print(f"  {i}. {diag} (score: {score:.1f})")

        results['total_duration'] = time.time() - start_time
        print(f"\nPipeline completed in {results['total_duration']:.1f}s")

        return results

    def run_quick_diagnosis(self, callback: Optional[Callable] = None,
                             token_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Run abbreviated 3-round pipeline (like v9).

        Useful for quick demos or when full pipeline is too slow.
        """
        skip = [
            RoundType.SPECIALIZED_RANKING,
            RoundType.SYMPTOM_MANAGEMENT,
            RoundType.MASTER_LIST,
            RoundType.VOTING
        ]

        return self.run_full_pipeline(callback=callback, token_callback=token_callback,
                                       skip_rounds=skip)


# =============================================================================
# Testing
# =============================================================================

def test_rounds():
    """Test round execution"""
    print("Testing DDx Rounds")
    print("=" * 50)

    # This would require full system initialization
    # See ddx_runner.py for complete integration test

    print("Round module loaded successfully")
    print(f"Available rounds: {[r.value for r in ROUND_ORDER]}")

    return True


if __name__ == "__main__":
    test_rounds()
