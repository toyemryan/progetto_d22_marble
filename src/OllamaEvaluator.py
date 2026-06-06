import json
import os
import requests
from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase
from utils.file_utils import load_from_file
from json_repair import repair_json

EVALUATION_MODEL = os.getenv("EVALUATION_MODEL", "qwen3:1.7b")
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMPT_PATH = os.path.join(BASE_DIR, "prompts", "evaluator_prompt.txt")

class OllamaJudgeMetric(BaseMetric):
    def __init__(self, name: str, criteria: str, evaluation_steps: list[str], threshold: float = 0.6):
        self.name = name
        self.criteria = criteria
        self.evaluation_steps = evaluation_steps
        self.threshold = threshold
        self.score = None
        self.reason = None

    def measure(self, test_case: LLMTestCase) -> float:
        steps_text = "\n".join(f"- {s}" for s in self.evaluation_steps)
        template = load_from_file(PROMPT_PATH)  # restituisce stringa

        prompt = template.format(
            criteria=self.criteria,
            steps_text=steps_text,
            input=test_case.input,
            actual_output=test_case.actual_output
        )

        url = os.getenv("OLLAMA_URL", "")
        response = requests.post(
            url,
            json={
                "model": EVALUATION_MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "think": False
            },
            timeout=120
        )

        parsed = response.json()
        raw_response = parsed.get("response", "")
        repaired = repair_json(raw_response)
        raw = json.loads(repaired)

        self.score = float(raw.get("score", 0.0))
        self.reason = raw.get("motivation", "")
        return self.score

    def is_successful(self) -> bool:
        return self.score is not None and self.score >= self.threshold