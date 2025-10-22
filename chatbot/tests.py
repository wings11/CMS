import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.5-flash')
prompt = (
    "You are CMSBot, an expert for Civil Master Solution (CMS). "
    "Specialize in construction and engineering solutions. "
    "Answer: Mission: Deliver innovative construction solutions. Vision: Lead in modern construction technologies."
)
try:
    response = model.generate_content(prompt)
    print(response.text)
except Exception as e:
    print(f"Error: {e}")