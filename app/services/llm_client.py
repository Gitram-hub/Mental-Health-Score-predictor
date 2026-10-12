import os

from dotenv import load_dotenv
from groq import Groq


load_dotenv()


def get_groq_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured. Add it to the project-root .env "
            "file or set it as an environment variable."
        )

    return Groq(api_key=api_key)
