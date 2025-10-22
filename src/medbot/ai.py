import logging
import os
from openai import OpenAI

APPROVED_USERS = os.getenv('APPROVED_USERS', '').split(',')
AI_GATEWAY_API_KEY = os.getenv('AI_GATEWAY_API_KEY')


def get_dynamic_text(prompt: str, user_handle: str, default: str = None) -> str:
    """Generate dynamic text using AI model based on the prompt."""
    logger = logging.getLogger(__name__)
    if user_handle not in APPROVED_USERS:
        logger.warning("Unauthorized user %s attempted to use AI features.", user_handle)
        if default:
            return default
        return "Unauthorized to use AI features!"
    try:
        client = OpenAI(
            api_key=AI_GATEWAY_API_KEY,
            base_url='https://ai-gateway.vercel.sh/v1'
        )
        if not AI_GATEWAY_API_KEY:
            raise RuntimeError("AI_GATEWAY_API_KEY is not set")

        system_msg = (
            "You are a friendly, human-like Telegram bot that sends medication reminders. "
            "Keep the tone warm, concise, and easy to understand. "
            "Only return the message text to be sent to the user — do not include explanations, markup, metadata or any response from user or offering any help via replies."
        )
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt}
        ]

        response = client.chat.completions.create(
            model="openai/gpt-5-nano",
            messages=messages,
            temperature=0.7
        )
        response_text = response.choices[0].message.content.strip()
        logger.info("Generated dynamic text for user %s: %s", user_handle, response_text)
        return response_text
    except Exception as e:
        logger.error("Error generating dynamic text: %s", e)
        if default:
            return default
        return "Sorry, I couldn't process that right now."
