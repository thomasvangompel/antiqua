import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("API_AI"))

def generate_genre_and_tags(titel: str, auteur: str) -> tuple[str, list[str]]:
    prompt = f"""
Je bent een literaire assistent. Op basis van de titel en auteur geef je:

1. Het waarschijnlijke genre (één woord, zoals 'Thriller', 'Roman', 'Fantasy', enz.).
2. Maximaal 5 relevante tags die het boek beschrijven (zoals thema’s, sfeer, doelgroep, of setting).

Formaat output:

Genre:
<genre>

Tags:
<tag1>, <tag2>, <tag3>, ...
    
Titel: {titel}
Auteur: {auteur}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt.strip()}],
        max_tokens=200,
    )

    content = response.choices[0].message.content.strip()

    # Parser
    import re
    genre = "Onbekend"
    tags = []

    try:
        genre_match = re.search(r"Genre:\s*(.*?)\s*Tags:", content, re.DOTALL)
        tags_match = re.search(r"Tags:\s*(.*)", content)

        if genre_match:
            genre = genre_match.group(1).strip()
        if tags_match:
            tags = [t.strip() for t in tags_match.group(1).split(",") if t.strip()]
    except Exception as e:
        print("Parsing genre/tags fout:", e)

    return genre, tags[:5]
