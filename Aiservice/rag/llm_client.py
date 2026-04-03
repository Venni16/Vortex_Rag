"""
rag/llm_client.py — Lightweight LLM singleton.
Default: TinyLlama/TinyLlama-1.1B-Chat-v1.0 via HuggingFace transformers (CPU).
Optional: GGUF via llama-cpp-python (set LLM_USE_LLAMA_CPP=true in .env).

Performance notes:
- n_threads defaults to os.cpu_count() for maximum CPU utilisation.
- n_batch=512 speeds up prompt evaluation (token batching).
- use_mlock=True pins model pages in RAM to prevent OS page-outs mid-inference.
- generate() is intentionally synchronous; pipeline.py runs it via run_in_executor.
"""

import logging
import os

logger = logging.getLogger(__name__)

_llm = None          # HuggingFace pipeline OR llama_cpp.Llama instance
_use_llama: bool = False


def load_llm() -> None:
    """Load the LLM into memory. Called once at application startup."""
    global _llm, _use_llama
    from config import get_settings
    settings = get_settings()

    if settings.LLM_USE_LLAMA_CPP:
        _load_llama_cpp(settings)
    else:
        _load_hf_pipeline(settings)


def _load_hf_pipeline(settings) -> None:
    global _llm, _use_llama
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

    logger.info("Loading HuggingFace model: %s ...", settings.LLM_MODEL_NAME)
    tokenizer = AutoTokenizer.from_pretrained(
        settings.LLM_MODEL_NAME,
        trust_remote_code=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        settings.LLM_MODEL_NAME,
        torch_dtype=torch.float32,
        trust_remote_code=True,
        low_cpu_mem_usage=True,
    )
    _llm = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=settings.LLM_MAX_NEW_TOKENS,
        temperature=settings.LLM_TEMPERATURE,
        do_sample=True,
        repetition_penalty=1.1,
        pad_token_id=tokenizer.eos_token_id,
    )
    _use_llama = False
    logger.info("HuggingFace pipeline ready (%s).", settings.LLM_MODEL_NAME)


def _load_llama_cpp(settings) -> None:
    global _llm, _use_llama
    from llama_cpp import Llama
    from huggingface_hub import hf_hub_download

    repo_id = settings.LLAMA_CPP_MODEL_PATH
    filename = settings.LLAMA_CPP_MODEL_FILE

    if not repo_id:
        raise ValueError("LLAMA_CPP_MODEL_PATH must be set when LLM_USE_LLAMA_CPP=true")

    # 0 in config means auto-detect all logical CPU cores
    n_threads = settings.LLAMA_CPP_N_THREADS or os.cpu_count() or 4

    logger.info(
        "Downloading/Loading llama-cpp model: %s / %s (threads=%d, n_batch=%d, n_ctx=%d)",
        repo_id, filename, n_threads, settings.LLAMA_CPP_N_BATCH, settings.LLAMA_CPP_N_CTX,
    )
    model_path = hf_hub_download(repo_id=repo_id, filename=filename)

    _llm = Llama(
        model_path=model_path,
        n_ctx=settings.LLAMA_CPP_N_CTX,        # context window
        n_threads=n_threads,                    # all available CPU cores
        n_batch=settings.LLAMA_CPP_N_BATCH,    # token batch size (faster prompt eval)
        use_mlock=True,                         # pin model in RAM, no OS page-outs
        verbose=False,
    )
    _use_llama = True
    logger.info(
        "llama-cpp model ready. threads=%d  n_batch=%d  n_ctx=%d",
        n_threads, settings.LLAMA_CPP_N_BATCH, settings.LLAMA_CPP_N_CTX,
    )


def get_llm():
    """Return the loaded LLM instance."""
    if _llm is None:
        raise RuntimeError("LLM not loaded. Call load_llm() first.")
    return _llm


def generate(prompt: str, max_tokens: int | None = None) -> str:
    """
    Generate a response from the LLM.

    SYNCHRONOUS — always call via asyncio.run_in_executor so it does not
    block the FastAPI event loop during inference.

    Args:
        prompt:     The full formatted prompt string.
        max_tokens: Override max new tokens.

    Returns:
        The generated text (LLM output only, prompt stripped).
    """
    from config import get_settings
    settings = get_settings()
    mt = max_tokens or settings.LLM_MAX_NEW_TOKENS

    llm = get_llm()

    if _use_llama:
        # Llama-3 instruction stop tokens: <|eot_id|> and <|end_of_text|>
        stop_tokens = [
            "<|eot_id|>",
            "<|end_of_text|>",
            "<" + "|eot_id|" + ">", # backup for different tokenizers
        ]
        output = llm(
            prompt,
            max_tokens=mt,
            temperature=settings.LLM_TEMPERATURE,
            echo=False,
            stop=stop_tokens,
        )
        return output["choices"][0]["text"].strip()
    else:
        results = llm(prompt)
        full_text: str = results[0]["generated_text"]
        # Strip the prompt prefix — return only new tokens
        response = full_text[len(prompt):].strip()
        return response

