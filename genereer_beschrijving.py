import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("API_AI"))

def generate_description(titel: str, genre: str = None) -> str:
    prompt = f"""
     Schrijf een boeksamenvatting in 1 duidelijke alinea, met een witregel ertussen voor leesbaarheid.Zorg ervoor dat de samenvatting niet halverwege een zin stopt

        Titel: '{titel}'{f", genre: {genre}" if genre else ""}

        1. Begin met een pakkende introductie.
        2. Verhoog de spanning in de tweede alinea en eindig met een krachtige afsluiting.
        """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt.strip()}],
        max_tokens=300,
    )
    return response.choices[0].message.content.strip()

