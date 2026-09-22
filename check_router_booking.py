from src.brain.router import IntentRouter
from src.brain.memory import ConversationMemory
mem = ConversationMemory()
mem.add_user_message("English, my name is Divya and I am a new patient and I would like to visit the Cardio Department.")
mem.add_assistant_message("Thank you, Divya — to complete your registration as a new patient and send your appointment confirmation ticket, may I please have your full name as you’d like it on file, your Date of Birth, and your contact phone number?")
mem.add_user_message("1st March 2006.")
mem.add_assistant_message("Which slot would you like (tomorrow 10:00 AM, tomorrow 2:00 PM, or the day after at 11:30 AM), and may I please have your contact phone number?")
mem.add_user_message("Tomorrow at 2:00 PM.")
mem.add_assistant_message("To finalize your new-patient registration and send the appointment confirmation, may I please have your contact phone number?")
router = IntentRouter()
res = router.classify_intent(mem, "1231231231")
print(res)
