import logging
import os
from openai import OpenAI

APPROVED_USERS = os.getenv('APPROVED_USERS', '').split(',')
AI_GATEWAY_API_KEY = os.getenv('AI_GATEWAY_API_KEY')


def get_dynamic_text(prompt: str, user_handle: str, default: str = None) -> str:
    """Generate dynamic text using AI model based on the prompt."""
    logger = logging.getLogger(__name__)
    if user_handle not in APPROVED_USERS:
        if default:
            return default
        return "Unauthorized to use AI features!"
    try:
        client = OpenAI(
            api_key=AI_GATEWAY_API_KEY,
            base_url='https://ai-gateway.vercel.sh/v1'
        )
        response = client.chat.completions.create(
            model='openai/gpt-5-nano',
            messages=[
                {
                    'role': 'user',
                    'content': f"Give a warm and human like respnose to:\n{prompt}"
                }
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error("Error generating dynamic text: %s", e)
        if default:
            return default
        return "Sorry, I couldn't process that right now."
