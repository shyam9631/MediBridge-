from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

def get_medicine_response(user_question, medicines):
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    medicine_list = ""
    for med in medicines:
        medicine_list += f"""
        - {med['name']} ({med['dosage']})
          Timing: {med['timing']}
          Remaining: {med['remaining']} tablets
          Taken Today: {'Yes' if med['taken_today'] else 'No'}
        """

    if not medicine_list:
        medicine_list = "No medicines added yet."

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": f"""You are MediBot, a helpful medical assistant for senior citizens.

Patient's current medicines:
{medicine_list}

Rules:
- Keep answers SHORT and SIMPLE (2-3 sentences max)
- Always recommend consulting a doctor for serious issues
- Be warm, caring and easy to understand
- Answer only medicine/health related questions"""
            },
            {
                "role": "user",
                "content": user_question
            }
        ],
        max_tokens=300,
        temperature=0.5
    )

    return response.choices[0].message.content
