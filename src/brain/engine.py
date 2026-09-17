import os
from typing import Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types
from src.brain.prompts import RECEPTIONIST_SYSTEM_PROMPT

# Load environment variables from .env file
load_dotenv()


class ConversationEngine:
    """
    Manages multi-turn conversation state and Google Gemini API interactions.
    """

    def __init__(self, system_prompt: str = RECEPTIONIST_SYSTEM_PROMPT) -> None:
        """
        Initializes the Google GenAI client and creates a multi-turn chat session.
        """
        self.api_key = os.getenv("GEMINI_API_KEY")
# Change line 22 to:
        self.model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-3.6-flash")
        self.system_prompt = system_prompt

        # Validate API key presence
        if not self.api_key:
            raise ValueError(
                "Missing GEMINI_API_KEY in environment variables. "
                "Please add GEMINI_API_KEY to your .env file."
            )

        # 1. Initialize Google GenAI Client
        self.client = genai.Client(api_key=self.api_key)

        # 2. Configure Chat Options with System Instruction
        self.config = types.GenerateContentConfig(
            system_instruction=self.system_prompt,
            temperature=0.7,
            max_output_tokens=300,
        )

        # 3. Create the multi-turn Chat Session
        self.chat = self.client.chats.create(
            model=self.model_name,
            config=self.config
        )

    def process_message(self, user_text: str) -> str:
        """
        Sends user text to the Gemini chat session and returns the assistant's response.
        """
        clean_text = user_text.strip()
        if not clean_text:
            return "I didn't catch that. Could you please repeat?"

        try:
            # Send message to active chat session (history is managed automatically by Gemini SDK)
            response = self.chat.send_message(clean_text)
            
            # Extract text from response payload
            assistant_response = response.text if response.text else ""
            return assistant_response

        except Exception as e:
            # Handle API timeouts, rate limits, or connectivity issues gracefully
            return f"Error communicating with AI engine: {str(e)}"

    def reset_conversation(self) -> None:
        """
        Resets the conversation session, clearing all previous turn memory.
        """
        self.chat = self.client.chats.create(
            model=self.model_name,
            config=self.config
        )
