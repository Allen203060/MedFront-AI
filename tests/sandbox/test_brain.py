import asyncio
import logging
from src.brain.orchestrator import AgenticBrainOrchestrator

logging.basicConfig(level=logging.INFO)

async def main():
    brain = AgenticBrainOrchestrator()
    print("Calling process_turn...")
    try:
        output = brain.process_turn("ਇੰਗਲਿਸ਼।")
        print(output)
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(main())
