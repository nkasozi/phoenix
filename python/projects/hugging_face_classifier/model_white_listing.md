# Mode white-listing approach

Here are some rough notes about what the model white-listing from the Hugging Face may look like.

There are two main goals for model white-listing:

- checking that there are no extra dependencies that would make the HF pipeline fail;
- putting safeguards in place against possible security threats.

## Model white-listing script

This script would run before the main HF pipeline is triggered. Here is a prototype (courtesy of Claude): it's here just for information purposes. Still need to be properly implemented.

The script would consist of several parts.

### Technical compatibility verification

Ensures that a given HF model works with the standard pipeline.

```
import os
import json
import tempfile
import time
from typing import Dict, Any, Tuple, List
from transformers import pipeline, AutoConfig, AutoTokenizer, AutoModelForSequenceClassification

class ModelCompatibilityChecker:
    def __init__(self, timeout=60):
        self.timeout = timeout

    def check_pipeline_compatibility(self, model_id: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Check if the model works with standard text-classification pipeline"""
        start_time = time.time()
        results = {"errors": [], "warnings": [], "metadata": {}}

        try:
            # Try loading with standard pipeline
            with tempfile.TemporaryDirectory() as tmp_dir:
                classifier = pipeline(
                    "text-classification",
                    model=model_id,
                    cache_dir=tmp_dir,
                    device=-1,  # CPU only for safety
                )

                # Test with simple inputs
                test_inputs = [
                    "This is a test sentence.",
                    "I enjoyed the movie we watched yesterday."
                ]

                for text in test_inputs:
                    result = classifier(text)

                    # Verify output structure (should have label and score)
                    if not (isinstance(result, list) and len(result) > 0):
                        results["errors"].append(f"Model produced unexpected output format: {result}")
                        continue

                    if not all(isinstance(item, dict) and 'label' in item and 'score' in item for item in result):
                        results["errors"].append(f"Output missing required fields: {result}")

                # Get model config
                config = AutoConfig.from_pretrained(model_id, cache_dir=tmp_dir)

                # Store useful metadata
                results["metadata"] = {
                    "model_type": getattr(config, "model_type", "unknown"),
                    "id2label": getattr(config, "id2label", {}),
                    "label2id": getattr(config, "label2id", {}),
                    "num_labels": getattr(config, "num_labels", 0),
                }

                # Warn if the model has very many output labels (might be inefficient)
                if results["metadata"]["num_labels"] > 100:
                    results["warnings"].append(f"Model has {results['metadata']['num_labels']} output labels, which might be inefficient")

                elapsed = time.time() - start_time
                results["metadata"]["load_and_inference_time"] = elapsed

                # Warn if model is slow
                if elapsed > 10:
                    results["warnings"].append(f"Model is relatively slow: {elapsed:.2f} seconds for loading and basic inference")

        except Exception as e:
            results["errors"].append(f"Pipeline compatibility test failed: {str(e)}")

        compatible = len(results["errors"]) == 0
        message = "Model is compatible with standard pipeline" if compatible else f"Compatibility issues: {', '.join(results['errors'])}"

        return compatible, message, results

    def check_tokenizer_compatibility(self, model_id: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Verify tokenizer works properly with standard interfaces"""
        results = {"errors": [], "warnings": [], "metadata": {}}

        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                # Check tokenizer loads and functions
                tokenizer = AutoTokenizer.from_pretrained(model_id, cache_dir=tmp_dir)

                # Test tokenization
                tokens = tokenizer("This is a test sentence.", return_tensors="pt")

                # Check if expected keys are present
                expected_keys = ['input_ids', 'attention_mask']
                missing_keys = [key for key in expected_keys if key not in tokens]

                if missing_keys:
                    results["errors"].append(f"Tokenizer missing expected outputs: {missing_keys}")

                # Store tokenizer metadata
                results["metadata"] = {
                    "vocab_size": getattr(tokenizer, "vocab_size", 0),
                    "model_max_length": getattr(tokenizer, "model_max_length", 0),
                }

        except Exception as e:
            results["errors"].append(f"Tokenizer compatibility test failed: {str(e)}")

        compatible = len(results["errors"]) == 0
        message = "Tokenizer is compatible" if compatible else f"Tokenizer issues: {', '.join(results['errors'])}"

        return compatible, message, results

    def check_dependencies(self, model_id: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Check for extra dependencies or custom code"""
        results = {"custom_files": [], "warnings": []}

        try:
            import requests
            from huggingface_hub import list_repo_files

            # List all files in the model repository
            all_files = list_repo_files(model_id)

            # Check for Python files or other custom code
            custom_code_files = [f for f in all_files if f.endswith(('.py', '.ipynb'))]
            results["custom_files"] = custom_code_files

            # Check for requirements.txt
            if "requirements.txt" in all_files:
                req_url = f"https://huggingface.co/{model_id}/raw/main/requirements.txt"
                response = requests.get(req_url, timeout=10)

                if response.status_code == 200:
                    requirements = [line.strip() for line in response.text.split('\n')
                                   if line.strip() and not line.startswith('#')]
                    results["requirements"] = requirements

                    if requirements:
                        results["warnings"].append(f"Model has extra dependencies: {', '.join(requirements)}")

            # Warning level based on custom files
            if custom_code_files:
                return False, f"Model has {len(custom_code_files)} custom code files that need review", results

            if "warnings" in results and results["warnings"]:
                return True, "Model has no custom code but has extra dependencies", results

            return True, "Model has no custom code or extra dependencies", results

        except Exception as e:
            return False, f"Error checking dependencies: {str(e)}", {"error": str(e)}

    def verify_model_compatibility(self, model_id: str) -> Dict[str, Any]:
        """Run all compatibility checks and return comprehensive results"""
        results = {
            "model_id": model_id,
            "compatible": False,
            "checks": {},
            "metadata": {},
            "requires_manual_review": False
        }

        # Check pipeline compatibility
        pipeline_ok, pipeline_msg, pipeline_details = self.check_pipeline_compatibility(model_id)
        results["checks"]["pipeline"] = {
            "passed": pipeline_ok,
            "message": pipeline_msg,
            "details": pipeline_details
        }

        # Only continue checks if the pipeline works
        if pipeline_ok:
            # Check tokenizer compatibility
            tokenizer_ok, tokenizer_msg, tokenizer_details = self.check_tokenizer_compatibility(model_id)
            results["checks"]["tokenizer"] = {
                "passed": tokenizer_ok,
                "message": tokenizer_msg,
                "details": tokenizer_details
            }

            # Check dependencies
            dep_ok, dep_msg, dep_details = self.check_dependencies(model_id)
            results["checks"]["dependencies"] = {
                "passed": dep_ok,
                "message": dep_msg,
                "details": dep_details
            }

            # Aggregate metadata
            results["metadata"] = {
                **results["checks"]["pipeline"].get("details", {}).get("metadata", {}),
                **results["checks"]["tokenizer"].get("details", {}).get("metadata", {})
            }

            # Models with custom code need manual review
            if not dep_ok:
                results["requires_manual_review"] = True

            # Overall compatibility
            results["compatible"] = pipeline_ok and tokenizer_ok

        return results

# Example usage
if __name__ == "__main__":
    checker = ModelCompatibilityChecker()
    results = checker.verify_model_compatibility("distilbert-base-uncased-finetuned-sst-2-english")
    print(json.dumps(results, indent=2))
```

### Security sandbox for model execution

Focuses on resource and runtime safety.

```
import os
import time
import json
import signal
import resource
import threading
import traceback
import tempfile
from typing import Dict, List, Any, Tuple, Optional, Callable
from transformers import pipeline

class ModelSecuritySandbox:
    def __init__(self,
                 max_memory_mb=4000,
                 inference_timeout=30,
                 max_input_length=10000):
        # Runtime limits
        self.max_memory_mb = max_memory_mb
        self.inference_timeout = inference_timeout
        self.max_input_length = max_input_length

        # Prepare test inputs for different scenarios
        self._prepare_test_inputs()

    def _prepare_test_inputs(self):
        """Prepare test inputs for runtime security testing"""
        # Standard inputs
        self.standard_inputs = [
            "This is a normal test sentence.",
            "I enjoyed the movie we watched yesterday.",
            "The weather today is quite pleasant."
        ]

        # Resource stress test inputs
        self.stress_test_inputs = [
            "a" * 1000,  # Long input
            "This is a test. " * 100,  # Repetitive input
            "\n".join(f"Line {i}" for i in range(100))  # Many lines
        ]

        # Edge case inputs
        self.edge_case_inputs = [
            "",  # Empty input
            " ",  # Just whitespace
            "null\x00\n\r\t'''\"\"\"",  # Special characters
            "ÜñíÇødē Ťëşţ Șťŕĩňğ",  # Unicode
        ]

    def _set_resource_limits(self):
        """Set resource limits for the process"""
        # Convert MB to bytes for memory limit
        memory_bytes = self.max_memory_mb * 1024 * 1024

        # Set memory limit
        resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))

    def _run_with_timeout(self, func: Callable, *args, timeout=None, **kwargs) -> Tuple[bool, str, Any]:
        """Run a function with timeout and resource limits"""
        result = [None]
        exception = [None]

        def worker():
            try:
                self._set_resource_limits()
                result[0] = func(*args, **kwargs)
            except Exception as e:
                exception[0] = e

        thread = threading.Thread(target=worker)
        thread.daemon = True

        start_time = time.time()
        thread.start()
        thread.join(timeout or self.inference_timeout)
        elapsed = time.time() - start_time

        if thread.is_alive():
            return False, f"Timeout after {elapsed:.2f} seconds", None
        if exception[0]:
            return False, f"Error: {str(exception[0])}", None

        return True, f"Completed in {elapsed:.2f} seconds", result[0]

    def _truncate_input(self, text: str) -> str:
        """Safely truncate input to maximum length"""
        if len(text) > self.max_input_length:
            return text[:self.max_input_length]
        return text

    def run_security_tests(self, model_id: str) -> Dict[str, Any]:
        """Run security tests on the model"""
        security_results = {
            "model_id": model_id,
            "passed": False,
            "tests": {
                "standard": {"passed": False, "details": []},
                "stress": {"passed": False, "details": []},
                "edge_case": {"passed": False, "details": []}
            },
            "performance": {
                "avg_inference_time": None,
                "max_inference_time": None
            }
        }

        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                # Load model
                classifier = pipeline(
                    "text-classification",
                    model=model_id,
                    cache_dir=tmp_dir,
                    device=-1  # CPU only for safety
                )

                inference_times = []

                # Test standard inputs
                for text in self.standard_inputs:
                    safe_text = self._truncate_input(text)
                    success, message, result = self._run_with_timeout(classifier, safe_text)

                    test_result = {
                        "input": safe_text,
                        "success": success,
                        "message": message,
                        "output": result if success else None
                    }

                    security_results["tests"]["standard"]["details"].append(test_result)
                    if success:
                        inference_time = float(message.split()[-2])
                        inference_times.append(inference_time)

                # Standard tests must all pass
                security_results["tests"]["standard"]["passed"] = all(
                    r["success"] for r in security_results["tests"]["standard"]["details"]
                )

                # Test stress inputs
                for text in self.stress_test_inputs:
                    safe_text = self._truncate_input(text)
                    success, message, result = self._run_with_timeout(classifier, safe_text)

                    test_result = {
                        "input_length": len(safe_text),
                        "success": success,
                        "message": message
                    }

                    security_results["tests"]["stress"]["details"].append(test_result)
                    if success:
                        inference_time = float(message.split()[-2])
                        inference_times.append(inference_time)

                # At least 2/3 stress tests should pass
                stress_success_count = sum(1 for r in security_results["tests"]["stress"]["details"] if r["success"])
                security_results["tests"]["stress"]["passed"] = stress_success_count >= 2

                # Test edge cases
                for text in self.edge_case_inputs:
                    safe_text = self._truncate_input(text)
                    success, message, result = self._run_with_timeout(classifier, safe_text)

                    test_result = {
                        "input": safe_text,
                        "success": success,
                        "message": message
                    }

                    security_results["tests"]["edge_case"]["details"].append(test_result)

                # At least half of edge cases should pass
                edge_success_count = sum(1 for r in security_results["tests"]["edge_case"]["details"] if r["success"])
                security_results["tests"]["edge_case"]["passed"] = edge_success_count >= len(self.edge_case_inputs) // 2

                # Calculate performance metrics
                if inference_times:
                    security_results["performance"]["avg_inference_time"] = sum(inference_times) / len(inference_times)
                    security_results["performance"]["max_inference_time"] = max(inference_times)

                # Overall security pass/fail
                security_results["passed"] = (
                    security_results["tests"]["standard"]["passed"] and
                    (security_results["tests"]["stress"]["passed"] or security_results["tests"]["edge_case"]["passed"])
                )

        except Exception as e:
            security_results["error"] = str(e)
            security_results["traceback"] = traceback.format_exc()

        return security_results
```

### Pickle scanning

Scans pickled objects for potential malicious code.

```
import os

def is_safetensors_model(model_path):
    """Check if model files use safetensors format."""
    files = os.listdir(model_path)
    weight_files = [f for f in files if not f.startswith('.')]
    safetensors_files = [f for f in weight_files if f.endswith('.safetensors')]

    # If no weight files or some weights aren't safetensors
    if not weight_files or len(safetensors_files) < len([f for f in weight_files if f.endswith(('.bin', '.pt', '.pth'))]):
        return False
    return True

from transformers import AutoModel

def safe_load_model(model_name_or_path, allow_only_safetensors=True):
    # Check if the model has safetensors files
    if allow_only_safetensors and not is_safetensors_model(model_name_or_path):
        raise SecurityError(f"Model {model_name_or_path} does not use SafeTensors format")

    # Load the model
    return AutoModel.from_pretrained(model_name_or_path)

```

For the models not using safetensors - implement additional scans.

```
import os
import re
from pathlib import Path

def lightweight_model_scan(model_path):
    """
    Performs basic security checks on model files.
    Returns (is_safe, reason) tuple.
    """
    suspicious_imports = [
        b"import os", b"import sys", b"import subprocess",
        b"import shutil", b"__import__", b"eval(", b"exec("
    ]

    suspicious_functions = [
        b"subprocess.Popen", b"subprocess.call", b"os.system",
        b"open(", b"file(", b"execfile", b"os.remove", b"os.unlink"
    ]

    # Check for pickle and pt files
    model_files = list(Path(model_path).glob("**/*"))
    binary_files = [f for f in model_files if f.suffix in ('.bin', '.pt', '.pth', '.pkl')]

    for file_path in binary_files:
        try:
            # Read file in binary mode to check for patterns
            with open(file_path, 'rb') as f:
                content = f.read()

                # Check for suspicious patterns
                for pattern in suspicious_imports + suspicious_functions:
                    if pattern in content:
                        return False, f"Suspicious pattern found: {pattern}"

                # Additional check for encoded commands
                if b"base64" in content and b"decode" in content:
                    return False, "Potential encoded commands detected"

        except Exception as e:
            return False, f"Error scanning file {file_path}: {str(e)}"

    return True, "Model passed basic security scan"

def safe_load_model(model_name_or_path):
    """Safe model loading with multiple security checks"""
    # First check for safetensors
    if is_safetensors_model(model_name_or_path):
        print("Model uses SafeTensors format - loading directly")
        return AutoModel.from_pretrained(model_name_or_path)

    # For non-safetensors models, perform additional checks
    is_safe, reason = lightweight_model_scan(model_name_or_path)
    if not is_safe:
        raise SecurityError(f"Security check failed: {reason}")

    print("WARNING: Loading non-SafeTensors model after security check")
    return AutoModel.from_pretrained(model_name_or_path)
```