

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("API_AI"))

def generate_author_description(author: str) -> str:
    prompt = f"""
    Schrijf een korte, pakkende en informatieve auteursbeschrijving in 1 duidelijke alinea. 
    Noem het genre waar de auteur vooral bekend om is, en benadruk zijn/haar stijl of bijzondere kenmerken.
    Zorg dat de beschrijving prettig leesbaar is en uitnodigt om meer te willen lezen. veel verkochte exemplaren?

    Auteur: '{author}'
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt.strip()}],
        max_tokens=200,
    )
    return response.choices[0].message.content.strip()
