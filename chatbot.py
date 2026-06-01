from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

def get_medicine_response(user_question, medicines):
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))  # ← add here
    ...
    medicine_list = ""
    for med in medicines:
        medicine_list += f"""
        - {med['name']} ({med['dosage']})
          Timing: {med['timing']}
          Remaining: {med['remaining']} tablets
          Taken Today: {'Yes' if med['taken_today'] else 'No'}
        """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": f"""You are MediBot — a helpful medical assistant for senior citizens.
                
                Patient's medicines:
                {medicine_list}
                
                Keep answers SHORT and SIMPLE!
                Always recommend consulting doctor for serious issues.
                Be warm and caring!"""
            },
            {
                "role": "user",
                "content": user_question
            }
        ]
    )
    
    return response.choices[0].message.content