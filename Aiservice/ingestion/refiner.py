"""
ingestion/refiner.py — LLM-driven knowledge distillation and classification.
Uses a specialized System Instruction to convert raw chunks into structured JSON.
"""

import json
import logging
import re
from functools import partial
import asyncio

from rag.llm_client import generate

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = """
SYSTEM INSTRUCTION:

You are an expert software documentation analyst and classifier.
Your task is to process raw technical content and convert it into structured knowledge for an AI learning system.
You MUST analyze the content and extract structured metadata so it can be stored in a vector database and retrieved efficiently.

---

OBJECTIVES:

1. Identify the correct:
   - framework (e.g., react, express, node, vue, angular)
   - topic (broad category)
   - subtopic (specific concept)

2. Clean and refine the content:
   - Remove noise, repetition, and irrelevant text
   - Keep only meaningful, educational content
   - Ensure clarity and correctness

3. Preserve technical accuracy:
   - Do NOT change meaning
   - Keep code snippets intact (if present)

4. Optimize for retrieval:
   - Content should be concise but informative
   - Should answer a specific concept clearly

---

CLASSIFICATION RULES:

Framework:
- react -> React.js related content
- express -> Express.js backend
- node -> Node.js general
- javascript -> core JS concepts
- other -> if none match

Topic Examples:
- fundamentals
- components
- hooks
- state-management
- routing
- api-handling
- middleware
- performance

Subtopic Examples:
- useState
- useEffect
- props
- context-api
- lifecycle
- event-handling

---

OUTPUT FORMAT (STRICT JSON):

{{
  "framework": "react",
  "topic": "hooks",
  "subtopic": "useState",
  "cleaned_text": "Refined explanation of the concept...",
  "keywords": ["react", "useState", "state", "hook"],
  "difficulty": "beginner | intermediate | advanced"
}}

---

IMPORTANT RULES:

- Always return ONLY valid JSON
- Do NOT include explanations outside JSON
- If unsure, choose the closest matching category
- Keep cleaned_text under 150 words but meaningful
- Keywords must help semantic search
- Difficulty must be inferred from complexity

---

INPUT CONTENT:
{raw_text_chunk}
"""

def _extract_json(text: str) -> dict | None:
    """Attempt to extract and parse JSON from LLM output."""
    try:
        # 1. Direct parse
        return json.loads(text.strip())
    except json.JSONDecodeError:
        # 2. Try to find JSON block via regex if model included preamble
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                return None
    return None

async def refine_chunk(raw_text: str) -> dict:
    """
    Process a raw text chunk through the LLM refiner.
    Returns a dict with processed fields or fallback to raw if error.
    """
    if not raw_text.strip():
        return {}

    prompt = SYSTEM_INSTRUCTION.format(raw_text_chunk=raw_text)
    
    try:
        # Run synchronous LLM call in a thread pool
        loop = asyncio.get_event_loop()
        # We use a smaller max_tokens since the instruction says < 150 words
        response = await loop.run_in_executor(None, partial(generate, prompt, max_tokens=600))
        
        refined_data = _extract_json(response)
        
        if refined_data:
            logger.debug("Refined chunk successfully: %s -> %s", 
                         refined_data.get("framework"), refined_data.get("topic"))
            return refined_data
            
        logger.warning("LLM returned invalid JSON for chunk. Falling back to raw text.")
    except Exception as exc:
        logger.error("Refinement failed: %s", exc)

    # Fallback to raw text if anything fails
    return {
        "framework": "other",
        "topic": "general",
        "subtopic": "unknown",
        "cleaned_text": raw_text,
        "keywords": [],
        "difficulty": "intermediate"
    }
