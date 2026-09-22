from src.brain.router import IntentRouter
from src.brain.memory import ConversationMemory
mem = ConversationMemory()
router = IntentRouter()
res = router.classify_intent(mem, "English, my name is Divya and I am a new patient and I would like to visit the Cardio Department.")
print(res)
