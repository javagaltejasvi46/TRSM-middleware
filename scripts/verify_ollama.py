"""Diagnostic script to verify Ollama local daemon connectivity and model inference."""

import asyncio
import os
import sys

# Ensure backend package is in pythonpath
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.config import settings
from app.runtime.adapters.ollama_adapter import OllamaAdapter


async def main():
    print("=" * 65)
    print("TRSM OLLAMA CONNECTIVITY & MODEL VERIFICATION")
    print("=" * 65)
    print(f"Configured Ollama URL: {settings.OLLAMA_BASE_URL}")
    print(f"Configured Default Model: {settings.DEFAULT_MODEL}")
    print("-" * 65)

    adapter = OllamaAdapter()

    # 1. Health check
    print("Checking connection to Ollama daemon...")
    healthy = await adapter.check_health()
    if not healthy:
        print("\n[FAIL] Ollama daemon is NOT reachable on " + str(settings.OLLAMA_BASE_URL))
        print("\nTo set up Ollama:")
        print("  1. Install Ollama: run 'winget install Ollama.Ollama' or download from https://ollama.com")
        print("  2. Launch the Ollama application (it runs in the system tray)")
        print(f"  3. Pull a model in terminal: ollama pull {settings.DEFAULT_MODEL}")
        print("  4. Re-run this script: python scripts/verify_ollama.py")
        return

    print("[SUCCESS] Ollama daemon is online and responsive!")

    # 2. Check installed models
    models = await adapter.list_models()
    print(f"\nInstalled Local Models ({len(models)} found):")
    if not models:
        print("  (None found yet)")
        print("\n[ACTION NEEDED] Pull a model to get started:")
        print(f"  ollama pull {settings.DEFAULT_MODEL}")
        print("  or for lower memory: ollama pull llama3.2:3b")
        return

    for m in models:
        is_default = " (DEFAULT)" if settings.DEFAULT_MODEL in m else ""
        print(f"  - {m}{is_default}")

    # 3. Test prompt generation
    test_model = settings.DEFAULT_MODEL if any(settings.DEFAULT_MODEL in m for m in models) else models[0]
    print(f"\nTesting prompt generation using '{test_model}'...")
    try:
        response = await adapter.generate(
            model=test_model,
            prompt="Respond in one sentence: TRSM is active.",
        )
        print(f"[SUCCESS] Model Response:\n  \"{response.strip()}\"")
        print("\nTRSM is ready for live Ollama inference!")
    except Exception as exc:
        print(f"[FAIL] Inference error: {exc}")


if __name__ == "__main__":
    asyncio.run(main())
