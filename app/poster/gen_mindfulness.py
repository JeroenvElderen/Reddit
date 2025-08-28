"""
Daily mindfulness prompt generator using OpenAI.
"""

import openai


def generate_mindfulness():
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a meditation guide for naturists."},
                {"role": "user", "content": "Write one naturist mindfulness or meditation prompt."}
            ],
            max_tokens=60
        )
        return resp.choices[0].message["content"].strip()
    except Exception as e:
        print(f"⚠️ Mindfulness generation failed: {e}")
        return "Take a moment to feel the breeze on your skin and breathe deeply."
