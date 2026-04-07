# =============================================================================
# DDx Core - v10 Full Pipeline
# =============================================================================

"""
Core agent framework for the full 7-round diagnostic pipeline.

Builds on v9's Ollama backend while adding:
- Integration with sliding context windows
- Enhanced agent response tracking
- Support for all 7 round types
- Credibility score tracking
"""

import yaml
import time
import json
import re
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

from inference_backends import OllamaBackend, SamplingConfig, create_backend
from ddx_sliding_context import TranscriptManager, TranscriptEntry


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class ModelConfig:
    """Model configuration for Ollama"""
    name: str
    model_name: str
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 1024
    role: str = "balanced"

    def to_sampling_config(self) -> SamplingConfig:
        return SamplingConfig(
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_tokens
        )


def load_system_config(config_path: str = "config.yaml") -> Dict[str, ModelConfig]:
    """Load system configuration"""
    try:
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        print(f"Loaded {config_path}")
    except FileNotFoundError:
        print("Using default configuration")
        config_data = {
            'conservative_model': {
                'name': 'Conservative',
                'model_name': 'llama3.1:8b',
                'temperature': 0.3,
                'top_p': 0.7,
                'max_tokens': 1024,
                'role': 'conservative'
            },
            'innovative_model': {
                'name': 'Innovative',
                'model_name': 'llama3.1:8b',
                'temperature': 0.8,
                'top_p': 0.95,
                'max_tokens': 1024,
                'role': 'innovative'
            }
        }

    return {
        key: ModelConfig(**values)
        for key, values in config_data.items()
        if key.endswith('_model')
    }


# =============================================================================
# Model Manager
# =============================================================================

class OllamaModelManager:
    """Manages model configurations via configurable backend (Ollama, vLLM, etc.)"""

    def __init__(self, configs: Dict[str, ModelConfig],
                 backend_type: str = "ollama", **backend_kwargs):
        self.configs = configs
        self.backend = create_backend(backend_type, **backend_kwargs)
        self.backend_type = backend_type
        self.active_model_id: Optional[str] = None
        self.loaded_models: set = set()

    def initialize(self) -> bool:
        """Initialize and verify backend"""
        if not self.backend.is_available():
            print(f"{self.backend_type} not available.")
            if self.backend_type == "ollama":
                print("Start with: ollama serve")
            return False

        # get_available_models is Ollama-specific; check if method exists
        if hasattr(self.backend, 'get_available_models'):
            available = self.backend.get_available_models()
            print(f"{self.backend_type} ready with {len(available)} models")

            for config_id, config in self.configs.items():
                if config.model_name not in available:
                    print(f"  Warning: {config.model_name} not found")
                    if self.backend_type == "ollama":
                        print(f"  Pull with: ollama pull {config.model_name}")
        else:
            print(f"{self.backend_type} backend ready")

        return True

    def load_model(self, model_id: str) -> bool:
        """Load/warm up a model"""
        if model_id not in self.configs:
            return False

        config = self.configs[model_id]
        if self.backend.load(config.model_name):
            self.active_model_id = model_id
            self.loaded_models.add(model_id)
            return True
        return False

    def generate_chat(self, model_id: str, messages: List[Dict[str, str]],
                      temperature_override: Optional[float] = None,
                      token_callback=None) -> str:
        """Generate using chat format, optionally streaming tokens."""
        config = self.configs.get(model_id)
        if not config:
            return f"Error: Unknown model {model_id}"

        if model_id != self.active_model_id:
            self.backend.load(config.model_name)
            self.active_model_id = model_id

        sampling = config.to_sampling_config()
        if temperature_override is not None:
            sampling.temperature = temperature_override

        if token_callback:
            return self.backend.generate_chat_stream(messages, sampling, token_callback)
        return self.backend.generate_chat(messages, sampling)

    def get_available_models(self) -> List[str]:
        return list(self.configs.keys())

    def get_config(self, model_id: str) -> Optional[ModelConfig]:
        return self.configs.get(model_id)


# =============================================================================
# Specialty System
# =============================================================================

class SpecialtyType(Enum):
    """Medical specialties"""
    CARDIOLOGY = "Cardiology"
    PULMONOLOGY = "Pulmonology"
    ENDOCRINOLOGY = "Endocrinology"
    GASTROENTEROLOGY = "Gastroenterology"
    NEUROLOGY = "Neurology"
    NEPHROLOGY = "Nephrology"
    HEMATOLOGY = "Hematology"
    INFECTIOUS_DISEASE = "Infectious Disease"
    EMERGENCY_MEDICINE = "Emergency Medicine"
    CRITICAL_CARE = "Critical Care"
    INTERNAL_MEDICINE = "Internal Medicine"
    RHEUMATOLOGY = "Rheumatology"
    ONCOLOGY = "Oncology"
    SURGERY = "Surgery"
    GENERAL = "General Medicine"


SPECIALTY_MAPPING = {
    'cardio': SpecialtyType.CARDIOLOGY,
    'heart': SpecialtyType.CARDIOLOGY,
    'pulmon': SpecialtyType.PULMONOLOGY,
    'lung': SpecialtyType.PULMONOLOGY,
    'respiratory': SpecialtyType.PULMONOLOGY,
    'endocrin': SpecialtyType.ENDOCRINOLOGY,
    'gastro': SpecialtyType.GASTROENTEROLOGY,
    'gi': SpecialtyType.GASTROENTEROLOGY,
    'neuro': SpecialtyType.NEUROLOGY,
    'nephro': SpecialtyType.NEPHROLOGY,
    'kidney': SpecialtyType.NEPHROLOGY,
    'renal': SpecialtyType.NEPHROLOGY,
    'hemato': SpecialtyType.HEMATOLOGY,
    'blood': SpecialtyType.HEMATOLOGY,
    'infectious': SpecialtyType.INFECTIOUS_DISEASE,
    'infection': SpecialtyType.INFECTIOUS_DISEASE,
    'emergency': SpecialtyType.EMERGENCY_MEDICINE,
    'critical': SpecialtyType.CRITICAL_CARE,
    'icu': SpecialtyType.CRITICAL_CARE,
    'internal': SpecialtyType.INTERNAL_MEDICINE,
    'rheumat': SpecialtyType.RHEUMATOLOGY,
    'oncol': SpecialtyType.ONCOLOGY,
    'cancer': SpecialtyType.ONCOLOGY,
    'surgery': SpecialtyType.SURGERY,
}


def map_specialty(specialty_str: str) -> SpecialtyType:
    """Map specialty string to enum"""
    specialty_lower = specialty_str.lower()
    for key, value in SPECIALTY_MAPPING.items():
        if key in specialty_lower:
            return value
    return SpecialtyType.GENERAL


# =============================================================================
# Agent Framework
# =============================================================================

@dataclass
class AgentConfig:
    """Configuration for a specialist agent"""
    name: str
    specialty: SpecialtyType
    persona: str
    reasoning_style: str
    temperature: float
    focus_areas: List[str]
    model_id: str = "conservative_model"
    case_relevance_score: float = 0.0


@dataclass
class AgentResponse:
    """Response from an agent"""
    agent_name: str
    specialty: str
    content: str
    structured_data: Optional[Dict] = None
    response_time: float = 0.0
    round_type: str = ""
    confidence_score: float = 0.0
    reasoning_quality: str = "standard"

    def to_dict(self) -> Dict:
        return {
            'agent_name': self.agent_name,
            'specialty': self.specialty,
            'content': self.content,
            'structured_data': self.structured_data,
            'response_time': self.response_time,
            'round_type': self.round_type,
            'confidence_score': self.confidence_score,
            'reasoning_quality': self.reasoning_quality
        }


class DDxAgent:
    """
    A specialist agent with sliding context awareness.

    Integrates with TranscriptManager to receive filtered context
    from prior rounds and contribute responses back.
    """

    def __init__(self, config: AgentConfig, model_manager: OllamaModelManager,
                 transcript_manager: TranscriptManager):
        self.config = config
        self.model_manager = model_manager
        self.transcript = transcript_manager
        self.credibility_score: float = 1.0  # Updated by Dr. Reed assessment

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def specialty(self) -> SpecialtyType:
        return self.config.specialty

    def generate_response(self, prompt: str, round_type: str,
                          use_context: bool = True,
                          token_callback=None) -> AgentResponse:
        """Generate a response with optional sliding context and streaming."""
        start_time = time.time()

        try:
            # Get filtered context if enabled
            context = None
            if use_context:
                context = self.transcript.get_filtered_context(
                    round_type=round_type,
                    agent_name=self.name,
                    agent_specialty=self.specialty.value
                )

            # Build messages
            messages = self._build_messages(prompt, round_type, context)

            # Generate (streaming if callback provided)
            response_content = self.model_manager.generate_chat(
                self.config.model_id,
                messages,
                temperature_override=self.config.temperature,
                token_callback=token_callback,
            )

            # Extract structured data
            structured_data = self._extract_structured_data(response_content, round_type)

            # Calculate metrics
            confidence = self._calculate_confidence(response_content, structured_data)
            reasoning_quality = self._assess_reasoning_quality(response_content)

            response = AgentResponse(
                agent_name=self.name,
                specialty=self.specialty.value,
                content=response_content,
                structured_data=structured_data,
                response_time=time.time() - start_time,
                round_type=round_type,
                confidence_score=confidence,
                reasoning_quality=reasoning_quality
            )

            # Record to transcript
            self.transcript.add_entry(
                round_type=round_type,
                agent_name=self.name,
                specialty=self.specialty.value,
                content=response_content,
                confidence=confidence,
                metadata={'structured_data': structured_data}
            )

            return response

        except Exception as e:
            print(f"Error in {self.name}: {e}")
            return AgentResponse(
                agent_name=self.name,
                specialty=self.specialty.value,
                content=f"Error: {str(e)}",
                response_time=time.time() - start_time,
                round_type=round_type
            )

    def _build_messages(self, user_prompt: str, round_type: str,
                        context: Optional[str]) -> List[Dict[str, str]]:
        """Build chat messages with round-specific instructions"""

        system_prompt = f"""You are {self.name}, a medical specialist in {self.specialty.value}.
{self.config.persona}

Your expertise: {', '.join(self.config.focus_areas)}
Reasoning style: {self.config.reasoning_style}

When providing differential diagnoses, structure your response with:
1. A JSON object containing diagnoses and supporting evidence
2. Followed by your clinical reasoning

JSON format:
{{"diagnosis_name": ["evidence1", "evidence2"], "another_diagnosis": ["evidence"]}}"""

        # Round-specific instructions
        round_instructions = {
            "specialized_ranking": """
TASK: Rank the relevance of your specialty to this case (1-10) and explain why.
Format: RELEVANCE: [score]/10
Then provide your reasoning.""",

            "symptom_management": """
TASK: Identify immediate management priorities from your specialty perspective.
Focus on stabilization and urgent interventions needed.""",

            "team_differentials": """
TASK: Provide 3-5 differential diagnoses from your specialty perspective.
Start with a JSON object mapping diagnoses to evidence, then explain your reasoning.""",

            "differential": """
TASK: Provide 3-5 differential diagnoses from your specialty perspective.
Start with a JSON object, then explain your reasoning.""",

            "master_list": """
TASK: Review all team diagnoses and create a consolidated master list.
Identify duplicates and organize by likelihood.""",

            "refinement": """
TASK: This is a structured debate. Review your colleagues' reasoning.
For each major diagnosis proposed:
- SUPPORT: If you agree, provide additional evidence
- CHALLENGE: If you disagree, explain why with counter-evidence
- REFINE: If partially agree, suggest modifications

Be specific. Reference colleagues by name. Update your position if convinced.""",

            "debate": """
TASK: Engage with your colleagues' reasoning.
SUPPORT diagnoses you agree with (cite additional evidence)
CHALLENGE diagnoses you question (provide counter-evidence)
Be intellectually honest - change your position if the evidence warrants it.""",

            "voting": """
TASK: Cast your preferential vote for the top 3 diagnoses.
Format your response as:
<PREFERENTIAL_VOTE>
1st Choice: [Diagnosis] - [Brief justification]
2nd Choice: [Diagnosis] - [Brief justification]
3rd Choice: [Diagnosis] - [Brief justification]
</PREFERENTIAL_VOTE>
Confidence: [XX%]""",

            "cant_miss": """
TASK: Identify critical diagnoses that CANNOT be missed.
Focus on conditions that could cause serious harm if diagnosis is delayed.
For each, specify:
- Urgency level (HIGH/MEDIUM)
- Key tests needed
- Time sensitivity"""
        }

        system_prompt += round_instructions.get(round_type, "")

        messages = [{"role": "system", "content": system_prompt}]

        # Add context if available
        if context and len(context) > 50:
            messages.append({
                "role": "assistant",
                "content": f"[Team Context]\n{context}"
            })

        messages.append({"role": "user", "content": user_prompt})

        return messages

    def _extract_structured_data(self, content: str, round_type: str) -> Optional[Dict]:
        """Extract structured data from response"""

        # For voting round, extract preferential vote
        if round_type == "voting":
            return self._extract_vote(content)

        # For other rounds, extract JSON diagnoses
        try:
            # Find JSON object
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                json_str = re.sub(r',\s*}', '}', json_str)
                json_str = re.sub(r',\s*]', ']', json_str)

                data = json.loads(json_str)
                if isinstance(data, dict) and len(data) > 0:
                    return data
        except:
            pass

        return None

    def _extract_vote(self, content: str) -> Optional[Dict]:
        """Extract preferential vote from response"""
        vote_data = {'rankings': [], 'confidence': 0.5}

        # Try XML format
        vote_match = re.search(r'<PREFERENTIAL_VOTE>(.*?)</PREFERENTIAL_VOTE>',
                               content, re.DOTALL | re.IGNORECASE)
        if vote_match:
            vote_text = vote_match.group(1)
        else:
            vote_text = content

        # Extract rankings
        for pattern in [r'(\d)(?:st|nd|rd|th)\s*[Cc]hoice:\s*(.+?)(?:\s+-\s|\n|$)',
                        r'(\d)\.\s*(.+?)(?:\s+-\s|\n|$)']:
            matches = re.findall(pattern, vote_text)
            if matches:
                for pos, diagnosis in matches[:3]:
                    vote_data['rankings'].append(diagnosis.strip())
                break

        # Extract confidence
        conf_match = re.search(r'[Cc]onfidence:\s*(\d+)%?', content)
        if conf_match:
            vote_data['confidence'] = int(conf_match.group(1)) / 100

        return vote_data if vote_data['rankings'] else None

    def _calculate_confidence(self, content: str, structured_data: Optional[Dict]) -> float:
        """Calculate confidence score"""
        score = 0.5

        if structured_data:
            score += 0.2

        medical_terms = len(re.findall(
            r'\b(?:diagnosis|evidence|findings|symptoms|clinical|pathology|presentation)\b',
            content, re.IGNORECASE
        ))
        score += min(0.2, medical_terms * 0.02)

        if len(content) > 300:
            score += 0.1

        return min(1.0, score)

    def _assess_reasoning_quality(self, content: str) -> str:
        """Assess reasoning quality"""
        from ddx_sliding_context import assess_reasoning_quality
        return assess_reasoning_quality(content)


# =============================================================================
# Dynamic Agent Generator
# =============================================================================

class DynamicAgentGenerator:
    """Generates specialist teams dynamically based on case"""

    def __init__(self, model_manager: OllamaModelManager,
                 transcript_manager: TranscriptManager,
                 ablation_mode: bool = False):
        self.model_manager = model_manager
        self.transcript = transcript_manager
        self.ablation_mode = ablation_mode

    def generate_agents(self, case_description: str,
                        max_specialists: int = 6) -> List[DDxAgent]:
        """Generate a team of specialists for the case"""
        print(f"\nGenerating specialist team...")

        proposals = self._get_specialist_proposals(case_description)

        if not proposals:
            print("Using fallback specialists")
            proposals = self._fallback_proposals()

        proposals = proposals[:max_specialists]

        agents = []
        model_ids = self.model_manager.get_available_models()

        for i, proposal in enumerate(proposals):
            model_id = model_ids[i % len(model_ids)] if model_ids else "conservative_model"

            try:
                specialty = map_specialty(proposal.get('specialty', 'General'))
                temp = self._calculate_temperature(proposal, model_id)

                config = AgentConfig(
                    name=proposal.get('name', f'Dr. Specialist {i+1}'),
                    specialty=specialty,
                    persona=proposal.get('persona', 'Experienced specialist'),
                    reasoning_style=proposal.get('reasoning_style', 'analytical'),
                    temperature=temp,
                    focus_areas=proposal.get('focus_areas', ['general medicine']),
                    model_id=model_id
                )

                agent = DDxAgent(config, self.model_manager, self.transcript)
                agents.append(agent)

                model_type = "Conservative" if "conservative" in model_id else "Innovative"
                print(f"  Created: {agent.name} ({agent.specialty.value}) [{model_type}]")

            except Exception as e:
                print(f"  Failed to create agent: {e}")

        print(f"Generated {len(agents)} specialists")
        return agents

    def _get_specialist_proposals(self, case_description: str) -> List[Dict]:
        """Ask LLM to propose specialists"""
        prompt = f"""Analyze this medical case and propose 4-6 specialists needed.

CASE:
{case_description}

Respond with a JSON array:
[
  {{
    "name": "Dr. [Name]",
    "specialty": "[Specialty]",
    "persona": "[Approach description]",
    "reasoning_style": "[analytical/systematic/innovative/intuitive]",
    "focus_areas": ["area1", "area2"],
    "rationale": "[Why needed]"
  }}
]

Include at least one generalist (Internal Medicine or Emergency Medicine).
"""

        messages = [
            {"role": "system", "content": "You are a medical team coordinator. Respond only with valid JSON."},
            {"role": "user", "content": prompt}
        ]

        try:
            response = self.model_manager.generate_chat("conservative_model", messages)

            # Find the JSON array — use raw_decode to handle trailing text
            start = response.find('[')
            if start != -1:
                # Clean trailing commas before parsing
                json_str = response[start:]
                json_str = re.sub(r',\s*]', ']', json_str)
                json_str = re.sub(r',\s*}', '}', json_str)

                try:
                    decoder = json.JSONDecoder()
                    proposals, _ = decoder.raw_decode(json_str)
                except json.JSONDecodeError:
                    # Fallback: extract with regex
                    json_match = re.search(r'\[.*?\]', json_str, re.DOTALL)
                    proposals = json.loads(json_match.group(0)) if json_match else None

                if isinstance(proposals, list) and len(proposals) >= 2:
                    print(f"  LLM proposed {len(proposals)} specialists")
                    return proposals
        except Exception as e:
            print(f"  Proposal generation failed: {e}")

        return []

    def _fallback_proposals(self) -> List[Dict]:
        """Fallback when LLM generation fails"""
        return [
            {
                "name": "Dr. Sarah Chen",
                "specialty": "Internal Medicine",
                "persona": "Systematic internist with broad diagnostic experience",
                "reasoning_style": "systematic",
                "focus_areas": ["general medicine", "diagnostic reasoning"]
            },
            {
                "name": "Dr. Michael Torres",
                "specialty": "Emergency Medicine",
                "persona": "Rapid assessment specialist focused on acute presentations",
                "reasoning_style": "analytical",
                "focus_areas": ["acute care", "triage"]
            },
            {
                "name": "Dr. Emily Watson",
                "specialty": "Cardiology",
                "persona": "Cardiologist with expertise in complex presentations",
                "reasoning_style": "methodical",
                "focus_areas": ["cardiac disease", "vascular conditions"]
            },
            {
                "name": "Dr. James Park",
                "specialty": "Infectious Disease",
                "persona": "ID specialist attuned to subtle infection patterns",
                "reasoning_style": "intuitive",
                "focus_areas": ["infections", "immunology"]
            }
        ]

    def _calculate_temperature(self, proposal: Dict, model_id: str) -> float:
        """Calculate temperature based on model config and reasoning style.

        In ablation_mode, style modifiers are disabled so agents get exactly
        the base temperature from their ModelConfig. This ensures strict
        temperature isolation for ablation experiments.
        """
        model_config = self.model_manager.get_config(model_id)
        base = model_config.temperature if model_config else 0.7

        if self.ablation_mode:
            return base

        style = proposal.get('reasoning_style', 'analytical').lower()
        style_mods = {
            'analytical': -0.1,
            'systematic': -0.1,
            'methodical': -0.1,
            'innovative': +0.15,
            'creative': +0.15,
            'intuitive': +0.1
        }

        modifier = style_mods.get(style, 0.0)
        return max(0.1, min(0.95, base + modifier))


# =============================================================================
# Testing
# =============================================================================

def test_core():
    """Test core components"""
    print("Testing v10 DDx Core")
    print("=" * 50)

    # Initialize
    configs = load_system_config()
    model_manager = OllamaModelManager(configs)

    if not model_manager.initialize():
        print("Failed to initialize Ollama")
        return False

    # Create transcript manager
    transcript = TranscriptManager()

    # Create agent generator
    generator = DynamicAgentGenerator(model_manager, transcript)

    # Test case
    test_case = """
    A 45-year-old male presents with acute chest pain radiating to the left arm,
    associated with shortness of breath and diaphoresis. History of diabetes
    and hypertension. ECG shows ST elevation in leads II, III, aVF.
    """

    # Generate team
    agents = generator.generate_agents(test_case, max_specialists=4)

    if not agents:
        print("Failed to generate agents")
        return False

    # Run one differential round
    print("\nRunning differential round...")
    for agent in agents:
        print(f"  {agent.name} analyzing...")
        response = agent.generate_response(
            f"CLINICAL CASE:\n{test_case}",
            round_type="differential",
            use_context=True
        )
        print(f"    Confidence: {response.confidence_score:.2f}")
        print(f"    Quality: {response.reasoning_quality}")

    # Check transcript
    print(f"\nTranscript entries: {len(transcript.entries)}")
    summary = transcript.get_round_summary("differential")
    print(f"Round summary: {summary}")

    return True


if __name__ == "__main__":
    test_core()
