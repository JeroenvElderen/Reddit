"""
Daily naturist fact generator using OpenAI.
"""

from datetime import datetime
import openai
from app.clients.supabase import supabase


def generate_naturist_fact():
    """Generate a longer naturist fact (up to 5 sentences, with emojis)."""
    try:
        for _ in range(5):
            resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a naturist historian and educator. "
                            "Write one naturist-related fact in 2–5 sentences. "
                            "Facts can include history, culture, health, famous naturist places, or environmental aspects. "
                            "Always weave in emojis naturally (🌿🌞🌊✨💚). "
                            "Make it sound friendly and engaging for a naturist community. "
                            "Avoid repeating previous facts."
                        )
                    },
                    {"role": "user", "content": "Give one unique naturist fact now."}
                ],
                max_tokens=200
            )
            fact = resp.choices[0].message["content"].strip()

            res = supabase.table("daily_facts").select("id").eq("fact", fact).execute()
            if not res.data:
                supabase.table("daily_facts").insert({
                    "date_posted": datetime.now().date().isoformat(),
                    "fact": fact
                }).execute()
                return fact

        return "🌞 Did you know? Naturism has deep roots in early 20th century Europe, promoting health, freedom, and a closer bond with nature 🌿✨."

    except Exception as e:
        print(f"⚠️ Fact generation failed: {e}")
        return "🌿 Naturism celebrates respect for the earth, body positivity, and living freely under the sun 🌞."
