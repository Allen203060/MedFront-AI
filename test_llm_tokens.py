import asyncio
from src.brain.orchestrator import AgenticBrainOrchestrator
from src.brain.prompts import RECEPTIONIST_SYSTEM_PROMPT

brain = AgenticBrainOrchestrator()
prompt = "Respond naturally to the patient:\n[MANDATORY LANGUAGE]: Reply in clear, professional English."
res = brain.client.chat.completions.create(
    model=brain.deployment_name,
    messages=[
        {"role": "system", "content": RECEPTIONIST_SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ],
    max_tokens=100
)
print(f"LLM Reply with max_tokens: '{res.choices[0].message.content}'")
