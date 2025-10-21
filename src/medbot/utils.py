import logging
import sys
from typing import Optional
import os


def setup_logging(log_level=logging.INFO, log_file: Optional[str] = None):
    """Configure logging for the entire package."""
    # Create a root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Prevent adding handlers multiple times if called again
    if logger.handlers:
        return logger

    # Formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s [%(levelname)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Log to stdout
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # Optional log to file
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_dynamic_text(prompt: str, default: str = None) -> str:
    """Generate dynamic text using AI model based on the prompt."""
    logger = logging.getLogger(__name__)
    try:
        client = OpenAI(
            api_key=os.getenv('AI_GATEWAY_API_KEY'),
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
        return response
    except Exception as e:
        logger.error("Error generating dynamic text: %s", e)
        if default:
            return default
        return "Sorry, I couldn't process that right now."
