# =============================================================================
# Inference Backends - Abstraction Layer for LLM Inference
# =============================================================================

"""
Provides a unified interface for different LLM inference backends.
Supports Ollama (primary for M4 Mac) with MLX as future option.
"""

import json
import time
import requests
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Generator, List, Optional, Dict, Any


@dataclass
class SamplingConfig:
    """Backend-agnostic sampling configuration"""
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 1024
    stop_tokens: List[str] = field(default_factory=lambda: ["</s>", "<|im_end|>", "<|eot_id|>"])

    def to_ollama_options(self) -> Dict[str, Any]:
        """Convert to Ollama API format"""
        return {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "num_predict": self.max_tokens,
            "stop": self.stop_tokens
        }

    def to_vllm_params(self) -> Dict[str, Any]:
        """Convert to vLLM SamplingParams kwargs"""
        return {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
            "stop": self.stop_tokens
        }


class InferenceBackend(ABC):
    """Abstract interface for LLM inference"""

    @abstractmethod
    def load(self, model_name: str, **kwargs) -> bool:
        """Load/prepare a model for inference"""
        pass

    @abstractmethod
    def generate(self, prompt: str, config: SamplingConfig) -> str:
        """Generate text from prompt"""
        pass

    def generate_chat_stream(self, messages: List[Dict[str, str]],
                             config: 'SamplingConfig',
                             token_callback: Optional[Callable[[str], None]] = None) -> str:
        """
        Generate using chat format with per-token streaming.

        Calls token_callback(token_text) for each generated token.
        Returns the full response string.

        Default implementation falls back to non-streaming generate_chat.
        """
        response = self.generate_chat(messages, config)
        if token_callback:
            token_callback(response)
        return response

    @abstractmethod
    def unload(self) -> None:
        """Unload current model (if applicable)"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if backend is available"""
        pass

    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """Get backend and model info"""
        pass


class MLXBackend(InferenceBackend):
    """
    MLX-based inference backend for Apple Silicon.

    Uses mlx-lm for fast, native Metal inference. Models are loaded
    from Hugging Face (mlx-community) and run directly on the GPU.
    """

    def __init__(self, **kwargs):
        self.model = None
        self.tokenizer = None
        self.current_model_name: Optional[str] = None
        self.model_info: Dict[str, Any] = {}
        self._mlx_lm = None  # lazy import

    def _ensure_import(self):
        """Lazy import mlx_lm to avoid import errors when not installed."""
        if self._mlx_lm is None:
            try:
                import mlx_lm
                self._mlx_lm = mlx_lm
            except ImportError:
                raise ImportError(
                    "mlx-lm is not installed. Install with: pip install mlx-lm"
                )

    def is_available(self) -> bool:
        """Check if MLX is available (Apple Silicon with mlx-lm installed)."""
        try:
            self._ensure_import()
            import mlx.core as mx
            return True
        except (ImportError, RuntimeError):
            return False

    def get_available_models(self) -> List[str]:
        """
        List MLX models available in the HuggingFace cache.

        Scans the HF cache for directories matching mlx-community/gemma-4-*
        and other known MLX model patterns.
        """
        try:
            from huggingface_hub import scan_cache_dir
            cache_info = scan_cache_dir()
            mlx_models = []
            for repo in cache_info.repos:
                # Include mlx-community models and any repo with 'mlx' in name
                if repo.repo_id.startswith("mlx-community/"):
                    # Check that there's at least one snapshot with model files
                    for revision in repo.revisions:
                        files = [f.file_name for f in revision.files]
                        if any(f.endswith('.safetensors') for f in files):
                            mlx_models.append(repo.repo_id)
                            break
            return sorted(mlx_models)
        except Exception as e:
            print(f"Failed to scan MLX models: {e}")
            return []

    def load(self, model_name: str, **kwargs) -> bool:
        """
        Load an MLX model into memory.

        Args:
            model_name: HuggingFace model ID (e.g. 'mlx-community/gemma-4-31b-it-4bit')
        """
        self._ensure_import()

        # Skip reload if same model
        if model_name == self.current_model_name and self.model is not None:
            return True

        # Unload previous model
        if self.model is not None:
            self.unload()

        print(f"Loading MLX model: {model_name}")
        start_time = time.time()

        try:
            self.model, self.tokenizer = self._mlx_lm.load(model_name)
            load_time = time.time() - start_time
            self.current_model_name = model_name
            self.model_info = {
                "name": model_name,
                "load_time": load_time,
                "status": "ready",
                "backend": "mlx",
            }
            print(f"  MLX model ready in {load_time:.1f}s")
            return True

        except Exception as e:
            print(f"  MLX load failed: {e}")
            self.model = None
            self.tokenizer = None
            return False

    def _make_sampler(self, config: SamplingConfig):
        """Create an mlx-lm sampler from our sampling config."""
        from mlx_lm.sample_utils import make_sampler
        return make_sampler(temp=config.temperature, top_p=config.top_p)

    def generate(self, prompt: str, config: SamplingConfig) -> str:
        """Generate text from a raw prompt string."""
        self._ensure_import()
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("No MLX model loaded. Call load() first.")

        try:
            response = self._mlx_lm.generate(
                self.model,
                self.tokenizer,
                prompt=prompt,
                max_tokens=config.max_tokens,
                sampler=self._make_sampler(config),
            )
            return response
        except Exception as e:
            print(f"MLX generation error: {e}")
            return f"Error: {str(e)}"

    def generate_chat(self, messages: List[Dict[str, str]], config: SamplingConfig) -> str:
        """Generate using chat messages (applies the model's chat template)."""
        self._ensure_import()
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("No MLX model loaded. Call load() first.")

        try:
            prompt = self.tokenizer.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=False,
            )

            response = self._mlx_lm.generate(
                self.model,
                self.tokenizer,
                prompt=prompt,
                max_tokens=config.max_tokens,
                sampler=self._make_sampler(config),
            )
            return response
        except Exception as e:
            print(f"MLX chat generation error: {e}")
            return f"Error: {str(e)}"

    def generate_chat_stream(self, messages: List[Dict[str, str]],
                             config: SamplingConfig,
                             token_callback: Optional[Callable[[str], None]] = None) -> str:
        """Stream tokens from chat messages, calling token_callback per chunk."""
        self._ensure_import()
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("No MLX model loaded. Call load() first.")

        try:
            prompt = self.tokenizer.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=False,
            )

            chunks = []
            for response in self._mlx_lm.stream_generate(
                self.model,
                self.tokenizer,
                prompt=prompt,
                max_tokens=config.max_tokens,
                sampler=self._make_sampler(config),
            ):
                token_text = response.text
                chunks.append(token_text)
                if token_callback:
                    token_callback(token_text)

            return "".join(chunks)
        except Exception as e:
            print(f"MLX stream error: {e}")
            return f"Error: {str(e)}"

    def unload(self) -> None:
        """Unload the current model and free memory."""
        if self.model is not None:
            print(f"Unloading MLX model: {self.current_model_name}")
            del self.model
            del self.tokenizer
            self.model = None
            self.tokenizer = None
            self.current_model_name = None
            self.model_info = {}

            # Force garbage collection to reclaim Metal memory
            import gc
            gc.collect()
            try:
                import mlx.core as mx
                mx.metal.clear_cache()
            except Exception:
                pass

    def get_info(self) -> Dict[str, Any]:
        """Get backend and model information."""
        return {
            "backend": "mlx",
            "available": self.is_available(),
            "current_model": self.current_model_name,
            "model_info": self.model_info,
            "available_models": self.get_available_models(),
        }


class OllamaBackend(InferenceBackend):
    """
    Ollama-based inference backend for Apple Silicon.

    Uses the Ollama REST API for model management and inference.
    Models are loaded on-demand and cached by Ollama.
    """

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.current_model: Optional[str] = None
        self.model_info: Dict[str, Any] = {}

    def is_available(self) -> bool:
        """Check if Ollama server is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [m["name"] for m in models]
        except requests.exceptions.RequestException as e:
            print(f"Failed to get models: {e}")
        return []

    def load(self, model_name: str, **kwargs) -> bool:
        """
        Prepare a model for inference.

        Ollama loads models on first use, but we can warm it up
        with a small request to ensure it's ready.
        """
        print(f"Preparing model: {model_name}")

        # Check if model exists
        available = self.get_available_models()
        if model_name not in available:
            print(f"Model {model_name} not found. Available: {available}")
            print(f"You can pull it with: ollama pull {model_name}")
            return False

        self.current_model = model_name

        # Warm up the model with a minimal request
        try:
            print(f"   Warming up {model_name}...")
            start_time = time.time()

            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model_name,
                    "prompt": "Hello",
                    "options": {"num_predict": 1},
                    "stream": False
                },
                timeout=120  # First load can take time
            )

            load_time = time.time() - start_time

            if response.status_code == 200:
                print(f"   Model ready in {load_time:.1f}s")
                self.model_info = {
                    "name": model_name,
                    "load_time": load_time,
                    "status": "ready"
                }
                return True
            else:
                print(f"   Warmup failed: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"   Load failed: {e}")
            return False

    def generate(self, prompt: str, config: SamplingConfig) -> str:
        """Generate text using Ollama API"""
        if not self.current_model:
            raise RuntimeError("No model loaded. Call load() first.")

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.current_model,
                    "prompt": prompt,
                    "options": config.to_ollama_options(),
                    "stream": False
                },
                timeout=300  # 5 min timeout for long generations
            )

            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                print(f"Generation failed: {response.status_code}")
                return f"Error: {response.status_code}"

        except requests.exceptions.RequestException as e:
            print(f"Generation error: {e}")
            return f"Error: {str(e)}"

    def generate_chat(self, messages: List[Dict[str, str]], config: SamplingConfig) -> str:
        """Generate using chat format (for instruction-tuned models)"""
        if not self.current_model:
            raise RuntimeError("No model loaded. Call load() first.")

        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.current_model,
                    "messages": messages,
                    "options": config.to_ollama_options(),
                    "stream": False
                },
                timeout=300
            )

            if response.status_code == 200:
                return response.json().get("message", {}).get("content", "")
            else:
                print(f"Chat generation failed: {response.status_code}")
                return f"Error: {response.status_code}"

        except requests.exceptions.RequestException as e:
            print(f"Chat generation error: {e}")
            return f"Error: {str(e)}"

    def generate_chat_stream(self, messages: List[Dict[str, str]],
                             config: SamplingConfig,
                             token_callback: Optional[Callable[[str], None]] = None) -> str:
        """Stream tokens from Ollama chat API."""
        if not self.current_model:
            raise RuntimeError("No model loaded. Call load() first.")

        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.current_model,
                    "messages": messages,
                    "options": config.to_ollama_options(),
                    "stream": True,
                },
                timeout=300,
                stream=True,
            )

            if response.status_code != 200:
                return f"Error: {response.status_code}"

            chunks = []
            for line in response.iter_lines():
                if not line:
                    continue
                data = json.loads(line)
                token_text = data.get("message", {}).get("content", "")
                if token_text:
                    chunks.append(token_text)
                    if token_callback:
                        token_callback(token_text)
                if data.get("done"):
                    break

            return "".join(chunks)

        except requests.exceptions.RequestException as e:
            print(f"Ollama stream error: {e}")
            return f"Error: {str(e)}"

    def unload(self) -> None:
        """
        Unload current model from memory.

        Note: Ollama manages model lifecycle automatically, but we can
        force unload by loading a tiny model or using the API.
        """
        if self.current_model:
            print(f"Releasing model: {self.current_model}")
            # Ollama doesn't have explicit unload, but setting keep_alive=0
            # on next request will unload after completion
            self.current_model = None
            self.model_info = {}

    def get_info(self) -> Dict[str, Any]:
        """Get backend and model information"""
        return {
            "backend": "ollama",
            "base_url": self.base_url,
            "available": self.is_available(),
            "current_model": self.current_model,
            "model_info": self.model_info,
            "available_models": self.get_available_models()
        }


# =============================================================================
# Backend Factory
# =============================================================================

def create_backend(backend_type: str = "ollama", **kwargs) -> InferenceBackend:
    """
    Factory function to create inference backends.

    Args:
        backend_type: "ollama" (default) or "mlx" (future)
        **kwargs: Backend-specific configuration

    Returns:
        Configured InferenceBackend instance
    """
    if backend_type == "ollama":
        base_url = kwargs.get("base_url", "http://localhost:11434")
        return OllamaBackend(base_url=base_url)
    elif backend_type == "vllm":
        # Lazy import — vllm is only available on Colab/GPU systems
        from benchmark.vllm_backend import VLLMBackend
        return VLLMBackend(**kwargs)
    elif backend_type == "mlx":
        return MLXBackend(**kwargs)
    else:
        raise ValueError(f"Unknown backend type: {backend_type}")


# =============================================================================
# Testing
# =============================================================================

def test_ollama_backend():
    """Test the Ollama backend"""
    print("Testing Ollama Backend")
    print("=" * 50)

    backend = create_backend("ollama")

    # Check availability
    if not backend.is_available():
        print("Ollama is not running. Start it with: ollama serve")
        return False

    print("Ollama is available")

    # Show available models
    info = backend.get_info()
    print(f"Available models: {info['available_models']}")

    # Test with a small model
    test_model = "phi3:mini"  # Small, fast model for testing

    if test_model not in info['available_models']:
        print(f"{test_model} not available. Trying llama3:latest...")
        test_model = "llama3:latest"

    if test_model not in info['available_models']:
        print("No suitable test model found")
        return False

    # Load model
    if not backend.load(test_model):
        print("Failed to load model")
        return False

    # Test generation
    print("\nTesting generation...")
    config = SamplingConfig(temperature=0.7, max_tokens=50)

    response = backend.generate(
        "What are three common symptoms of pneumonia? Be brief.",
        config
    )

    print(f"Response: {response[:200]}...")

    # Test chat format
    print("\nTesting chat format...")
    messages = [
        {"role": "system", "content": "You are a medical specialist. Be concise."},
        {"role": "user", "content": "Name one cardiac emergency."}
    ]

    chat_response = backend.generate_chat(messages, config)
    print(f"Chat response: {chat_response[:200]}...")

    print("\nOllama backend test passed!")
    return True


if __name__ == "__main__":
    test_ollama_backend()
