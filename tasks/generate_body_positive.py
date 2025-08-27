def generate_body_positive():
    """Generate a longer uplifting body positivity message (2–5 sentences) with emojis."""
    try:
        for _ in range(5):
            resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a naturist body positivity coach. "
                            "Always write between 2 and 5 sentences. "
                            "Celebrate natural bodies, diversity, confidence, and freedom. "
                            "Use emojis like 🌞🌿🌊✨🌸💚 naturally throughout the message. "
                            "Each message must feel fresh, supportive, and uplifting. "
                            "Do not repeat previous prompts."
                        )
                    },
                    {"role": "user", "content": "Write one body positivity message for naturists."}
                ],
                max_tokens=200
            )
            message = resp.choices[0].message["content"].strip()

            # Check if already exists
            res = supabase.table("daily_bodypositive").select("id").eq("message", message).execute()
            if not res.data:
                # Save new message
                supabase.table("daily_bodypositive").insert({
                    "date_posted": datetime.now().date().isoformat(),
                    "message": message
                }).execute()
                return message

        # Fallback
        return "💚 Every body is unique and beautiful 🌿✨. Embrace your natural self with pride and confidence 🌞🌸🌊."

    except Exception as e:
        print(f"⚠️ Body-positive generation failed: {e}")
        return "🌞 Remember: your body is not something to fix — it's something to celebrate 🌿💚✨."
