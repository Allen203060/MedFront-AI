import json
import sys
import warnings

# Suppress google-genai SDK automatic function calling warning printed to terminal
warnings.filterwarnings("ignore", category=UserWarning, message=".*automatic function calling.*")

from src.brain.orchestrator import AgenticBrainOrchestrator


def run_agentic_cli() -> None:
    """
    Interactive Terminal Harness for MedFront-AI Agentic Brain.
    """
    print("=" * 70)
    print("  MedFront AI Receptionist (Aura) - Agentic Brain CLI")
    print("  Features: Intent Classification | RAG Routing | Tool Execution")
    print("  - Type 'exit' to quit | Type 'reset' to clear conversation memory")
    print("=" * 70)

    try:
        orchestrator = AgenticBrainOrchestrator()
    except Exception as e:
        print(f"\n[Initialization Failure]: {e}")
        sys.exit(1)

    print("\n[Aura]: Hello! Thank you for calling MedFront. May I know your preferred language for this conversation: English, Hindi, or Punjabi?\n")

    while True:
        try:
            user_input = input("[You]: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit"]:
                print("\n[Aura]: Thank you for calling MedFront. Have a wonderful day! Goodbye.")
                break

            if user_input.lower() == "reset":
                orchestrator.reset()
                print("\n--- Conversation memory and orchestrator state reset. ---\n")
                continue

            # Execute Agentic Turn
            output = orchestrator.process_turn(user_input)

            # Display Intent & Routing Diagnostics
            print("\n" + "-" * 55)
            print(f"| INTENT DETECTED : {output.intent_detected.value}")
            print(f"| RAG USED        : {output.rag_used}")
            print(f"| TOOL EXECUTED   : {output.tool_used}")
            print("-" * 55)

            # Display Output 1: Text-to-Speech (TTS) Payload
            print(f"\n[Aura (TTS Output)]: {output.speech_text}\n")

            # Display Output 2: RAG Ingestion Metadata Payload
            print(f"[RAG Ingestion Payload]:\n{json.dumps(output.patient_ingestion_payload, indent=2)}")
            print("-" * 55 + "\n")

        except KeyboardInterrupt:
            print("\nSession terminated.")
            break


if __name__ == "__main__":
    run_agentic_cli()
