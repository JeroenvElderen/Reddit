def generate_trivia():
    """Generate a unique trivia question and store it in Supabase."""
    try:
        for _ in range(5):  # try up to 5 times to avoid duplicates
            resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a trivia generator for a naturist Reddit community. "
                            "Always create varied and engaging questions: true/false, "
                            "multiple choice, or open-ended. Cover history, culture, "
                            "environment, health, famous naturist places, and body positivity. "
                            "Use emojis naturally. Never repeat previous ones."
                        )
                    },
                    {"role": "user", "content": "Write one unique naturist trivia question now."}
                ],
                max_tokens=100
            )
            question = resp.choices[0].message["content"].strip()

            # Check if already exists
            res = supabase.table("daily_trivia").select("id").eq("question", question).execute()
            if not res.data:
                # Save new question
                supabase.table("daily_trivia").insert({
                    "date_posted": datetime.now().date().isoformat(),
                    "question": question
                }).execute()
                return question

        # Fallback if all retries were duplicates
        return "🌿 In which decade did modern naturism first gain popularity in Europe?"

    except Exception as e:
        print(f"⚠️ Trivia generation failed: {e}")
        return "🌞 True or False: Naturism encourages respect for both people and nature."
