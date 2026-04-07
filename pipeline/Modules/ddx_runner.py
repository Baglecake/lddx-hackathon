# =============================================================================
# DDx Runner - Main Orchestrator
# =============================================================================

"""
Main entry point for the v10 full diagnostic pipeline.

Orchestrates:
- System initialization (Ollama backend, models)
- Case analysis and specialist team generation
- Full 7-round or quick 3-round diagnostic pipelines
- Result synthesis and export
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable

# Add Modules to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ddx_core import (
    OllamaModelManager, load_system_config,
    DynamicAgentGenerator, DDxAgent
)
from ddx_sliding_context import TranscriptManager
from ddx_rounds import DiagnosticPipeline, RoundType
from ddx_synthesis import (
    run_synthesis, normalize_diagnosis,
    TempoScore, CredibilityScore, VotingResult
)


# =============================================================================
# Main DDx System
# =============================================================================

class DDxSystem:
    """
    Main diagnostic system - v10 full pipeline.

    Manages the complete diagnostic workflow from initialization
    through all 7 rounds to final synthesis.
    """

    def __init__(self):
        self.model_manager: Optional[OllamaModelManager] = None
        self.transcript: Optional[TranscriptManager] = None
        self.agent_generator: Optional[DynamicAgentGenerator] = None
        self.current_agents: List[DDxAgent] = []
        self.current_case: Dict[str, Any] = {}
        self.pipeline: Optional[DiagnosticPipeline] = None
        self.last_result: Optional[Dict[str, Any]] = None

    def initialize(self, config_path: str = "config.yaml") -> bool:
        """Initialize the diagnostic system"""
        print("="*60)
        print("Initializing Local-DDx v10 Full Pipeline")
        print("="*60)

        # Load model configuration
        configs = load_system_config(config_path)
        self.model_manager = OllamaModelManager(configs)

        if not self.model_manager.initialize():
            print("ERROR: Failed to initialize Ollama backend")
            print("Make sure Ollama is running: ollama serve")
            return False

        # Warm up models
        print("\nWarming up models...")
        for model_id in self.model_manager.get_available_models():
            print(f"  Loading {model_id}...")
            self.model_manager.load_model(model_id)

        # Initialize transcript manager
        self.transcript = TranscriptManager()

        # Initialize agent generator
        self.agent_generator = DynamicAgentGenerator(
            self.model_manager, self.transcript
        )

        print("\nSystem ready!")
        return True

    def analyze_case(self, case_description: str,
                     case_name: str = "case",
                     max_specialists: int = 6) -> Dict[str, Any]:
        """
        Analyze a case and generate specialist team.

        Args:
            case_description: Clinical case text
            case_name: Identifier for the case
            max_specialists: Maximum number of specialists (default 6)

        Returns:
            Analysis result with team composition
        """
        print(f"\n{'='*60}")
        print(f"CASE ANALYSIS: {case_name}")
        print(f"{'='*60}")

        # Clear previous state
        self.transcript.clear()
        self.current_agents = []
        self.last_result = None

        # Store case data
        self.current_case = {
            'name': case_name,
            'description': case_description,
            'timestamp': datetime.now().isoformat()
        }

        # Generate specialist team
        self.current_agents = self.agent_generator.generate_agents(
            case_description, max_specialists=max_specialists
        )

        if not self.current_agents:
            return {
                'success': False,
                'error': 'Failed to generate specialist team'
            }

        # Initialize pipeline
        self.pipeline = DiagnosticPipeline(
            self.current_agents, self.transcript, case_description
        )

        return {
            'success': True,
            'case_name': case_name,
            'specialists': [
                {
                    'name': a.name,
                    'specialty': a.specialty.value,
                    'model': a.config.model_id,
                    'temperature': a.config.temperature,
                    'reasoning_style': a.config.reasoning_style,
                }
                for a in self.current_agents
            ]
        }

    def run_full_diagnosis(self, callback: Optional[Callable] = None,
                            token_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Run the complete 7-round diagnostic pipeline.

        Args:
            callback: Optional progress callback
            token_callback: Optional token callback(agent_name, token) for streaming

        Returns:
            Complete diagnostic results
        """
        if not self.pipeline:
            return {'success': False, 'error': 'No case loaded. Call analyze_case first.'}

        result = self.pipeline.run_full_pipeline(callback=callback, token_callback=token_callback)
        result['case'] = self.current_case
        self.last_result = result

        return result

    def run_quick_diagnosis(self, callback: Optional[Callable] = None,
                             token_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Run abbreviated 3-round pipeline.

        Skips: specialized_ranking, symptom_management, master_list, voting
        Runs: team_differentials, refinement, cant_miss

        Faster for demos while still showing multi-agent collaboration.
        """
        if not self.pipeline:
            return {'success': False, 'error': 'No case loaded. Call analyze_case first.'}

        result = self.pipeline.run_quick_diagnosis(callback=callback, token_callback=token_callback)
        result['case'] = self.current_case
        self.last_result = result

        return result

    def get_transcript(self) -> List[Dict]:
        """Get full conversation transcript"""
        if self.transcript:
            return self.transcript.export_transcript()
        return []

    def export_results(self, filepath: str) -> bool:
        """Export results to JSON file"""
        if not self.last_result:
            print("No results to export")
            return False

        try:
            export_data = {
                'case': self.current_case,
                'specialists': [
                    {'name': a.name, 'specialty': a.specialty.value}
                    for a in self.current_agents
                ],
                'results': self.last_result,
                'transcript': self.get_transcript(),
                'exported_at': datetime.now().isoformat()
            }

            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)

            print(f"Results exported to {filepath}")
            return True

        except Exception as e:
            print(f"Export failed: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            'initialized': self.model_manager is not None,
            'case_loaded': bool(self.current_case),
            'agents_count': len(self.current_agents),
            'transcript_entries': len(self.transcript.entries) if self.transcript else 0,
            'has_results': self.last_result is not None
        }


# =============================================================================
# CLI Interface
# =============================================================================

def run_interactive():
    """Run interactive CLI session"""
    print("\n" + "="*60)
    print("Local-DDx v10 - Interactive Mode")
    print("="*60)

    system = DDxSystem()

    if not system.initialize():
        print("Initialization failed. Exiting.")
        return

    while True:
        print("\n" + "-"*40)
        print("Commands:")
        print("  1. Load case")
        print("  2. Run full diagnosis (7 rounds)")
        print("  3. Run quick diagnosis (3 rounds)")
        print("  4. Export results")
        print("  5. View status")
        print("  q. Quit")
        print("-"*40)

        choice = input("Enter choice: ").strip().lower()

        if choice == 'q':
            print("Goodbye!")
            break

        elif choice == '1':
            print("\nEnter clinical case (end with empty line):")
            lines = []
            while True:
                line = input()
                if line == "":
                    break
                lines.append(line)

            if lines:
                case_text = "\n".join(lines)
                result = system.analyze_case(case_text, "interactive_case")
                if result['success']:
                    print(f"\nTeam generated: {len(result['specialists'])} specialists")
                    for spec in result['specialists']:
                        print(f"  - {spec['name']} ({spec['specialty']})")
                else:
                    print(f"Error: {result.get('error')}")

        elif choice == '2':
            if not system.current_case:
                print("No case loaded. Load a case first.")
                continue

            print("\nRunning full 7-round diagnosis...")
            result = system.run_full_diagnosis()

            if result.get('final_diagnoses'):
                print("\n" + "="*50)
                print("FINAL DIAGNOSES:")
                print("="*50)
                for i, diag in enumerate(result['final_diagnoses'][:6], 1):
                    print(f"  {i}. {diag}")

        elif choice == '3':
            if not system.current_case:
                print("No case loaded. Load a case first.")
                continue

            print("\nRunning quick 3-round diagnosis...")
            result = system.run_quick_diagnosis()

            # For quick diagnosis, show round summaries
            print("\nRound summaries:")
            for round_name, round_data in result.get('rounds', {}).items():
                print(f"  {round_name}: {len(round_data.get('responses', []))} responses")

        elif choice == '4':
            filename = f"lddx_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            system.export_results(filename)

        elif choice == '5':
            status = system.get_status()
            print("\nSystem Status:")
            for key, value in status.items():
                print(f"  {key}: {value}")


# =============================================================================
# Test Runner
# =============================================================================

def run_test_case():
    """Run a test case through the system"""
    print("\n" + "="*60)
    print("Local-DDx v10 - Test Run")
    print("="*60)

    system = DDxSystem()

    if not system.initialize():
        print("Initialization failed")
        return False

    # Test case: Classic STEMI
    test_case = """
    A 58-year-old male with history of type 2 diabetes and hypertension presents
    to the emergency department with crushing substernal chest pain that began
    90 minutes ago. The pain radiates to his left arm and jaw. He is diaphoretic
    and appears anxious. He took aspirin at home without relief.

    Vitals: BP 165/95, HR 92, RR 22, SpO2 96% on room air
    ECG: ST elevation in leads V1-V4 with reciprocal changes in II, III, aVF
    Labs: Troponin I elevated at 2.4 ng/mL (normal <0.04)

    Physical exam notable for:
    - JVP not elevated
    - Lungs clear to auscultation
    - No murmurs, regular rhythm
    - No peripheral edema
    """

    # Analyze case
    analysis = system.analyze_case(test_case, "STEMI_test_case", max_specialists=4)

    if not analysis['success']:
        print(f"Case analysis failed: {analysis.get('error')}")
        return False

    print(f"\nGenerated team of {len(analysis['specialists'])} specialists")

    # Run quick diagnosis for faster testing
    print("\nRunning quick diagnosis (3 rounds)...")
    result = system.run_quick_diagnosis()

    print("\n" + "="*50)
    print("TEST COMPLETE")
    print("="*50)

    if result.get('rounds'):
        print(f"Rounds completed: {list(result['rounds'].keys())}")
        print(f"Total duration: {result.get('total_duration', 0):.1f}s")

    # Export results
    system.export_results("test_results.json")

    return True


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Local-DDx v10 Full Pipeline")
    parser.add_argument('--test', action='store_true', help='Run test case')
    parser.add_argument('--interactive', action='store_true', help='Run interactive mode')

    args = parser.parse_args()

    if args.test:
        run_test_case()
    elif args.interactive:
        run_interactive()
    else:
        # Default to test
        run_test_case()
