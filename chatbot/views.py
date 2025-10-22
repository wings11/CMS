import os
import json
import time
import threading
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
import google.generativeai as genai

# Configure logging
logger = logging.getLogger(__name__)

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Global lock for concurrency (limits simultaneous API calls)
api_lock = threading.Lock()

# Session limits
MAX_MESSAGES_PER_SESSION = 500
MAX_WORDS_PER_QUESTION = 70

# Company details (English and Thai)
company_data = {
    'en': {
        'name': 'Civil Master Solution (CMS)',
        'specialty': 'construction and engineering solutions',
        'services': ['design', 'supervision', 'testing', 'consultancy'],
        'products': ['Industrial Flooring', 'Pavements', 'Precast Concrete', 'DUCTIL steel fibers', 'Armour Joints', 'DELTABEAM'],
        'note': 'You can only provide CMS information. Answer in 1-2 short sentences. If the question is not in the Q&A examples or the question is not related, please only ask company related questions and else if you do not know the details which are related to the company information, contact CMS via email cms@civilmastersolution.com.',
        'contact': 'Email cms@civilmastersolution.com.'
    },
    'th': {
        'name': 'Civil Master Solution (CMS)',
        'specialty': 'โซลูชันการก่อสร้างและวิศวกรรม',
        'services': ['ออกแบบ', 'ดูแล', 'ทดสอบ', 'ให้คำปรึกษา'],
        'products': ['พื้นอุตสาหกรรม', 'ทางเดิน', 'คอนกรีตสำเร็จรูป', 'เส้นใยเหล็ก DUCTIL', 'ข้อต่อ Armour', 'DELTABEAM'],
        'note': 'คุณสามารถให้ข้อมูล CMS เท่านั้น ตอบใน 1-2 ประโยคสั้นๆ หากคำถามอยู่นอกหัวข้อหรือไม่รู้รายละเอียด ติดต่อ CMS ทางอีเมล cms@civilmastersolution.com หรือเยี่ยมชม www.civilmastersolution.com',
        'contact': 'ส่งอีเมลถึง cms@civilmastersolution.com หรือเยี่ยมชม www.civilmastersolution.com.'
    }
}

# Load Q&A from JSON
def load_qa_data():
    try:
        with open('qa_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data['qa_pairs']
    except FileNotFoundError:
        return [{"question": "Error", "answer": "Q&A file not found.", "lang": "en"}]
    except json.JSONDecodeError:
        return [{"question": "Error", "answer": "Invalid Q&A file format.", "lang": "en"}]

# Detect language
def detect_language(text):
    if any('\u0E00' <= char <= '\u0E7F' for char in text):
        return 'th'
    return 'en'

# Count words
def count_words(text):
    return len(text.split())

@csrf_exempt
def chatbot_view(request):
    ip = request.META.get('REMOTE_ADDR', 'unknown')
    now = time.time()
    
    # Global IP rate limiting (50 requests/min per IP) - prevents flooding
    ip_key = f"ip_rate_{ip}"
    ip_requests = cache.get(ip_key, [])
    ip_requests = [t for t in ip_requests if now - t < 60]
    if len(ip_requests) >= 50:
        logger.warning(f"IP {ip} hit global rate limit")
        return JsonResponse({'error': 'Too many requests from your IP. Please wait.'}, status=429)
    ip_requests.append(now)
    cache.set(ip_key, ip_requests, 60)
    
    if request.method == 'POST':
        # Initialize session
        if 'chat_history' not in request.session:
            request.session['chat_history'] = []
        if 'question_timestamps' not in request.session:
            request.session['question_timestamps'] = []
        if 'last_activity' not in request.session:
            request.session['last_activity'] = time.time()
        if 'chat_count' not in request.session:
            request.session['chat_count'] = 0

        # Check session timeout
        current_time = time.time()
        if current_time - request.session['last_activity'] > 3600: # 1 hour
            request.session.flush()
            request.session['chat_history'] = []
            request.session['question_timestamps'] = []
            request.session['chat_count'] = 0
            request.session['last_activity'] = current_time

        # Check session message limit
        if request.session['chat_count'] >= MAX_MESSAGES_PER_SESSION:
            return JsonResponse({'error': 'You’ve reached the 500-message limit for this session.'}, status=429)

        # Session rate limit: 10 questions per minute
        request.session['question_timestamps'] = [t for t in request.session['question_timestamps'] if current_time - t < 60]
        if len(request.session['question_timestamps']) >= 10:
            return JsonResponse({'error': 'Rate limit exceeded. Please wait before asking more questions.'}, status=429)

        # Get and validate input
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                user_question = data.get('question', '').strip()
                honeypot = data.get('honeypot', '')
            else:
                user_question = request.POST.get('question', '').strip()
                honeypot = request.POST.get('honeypot', '')
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        # Honeypot check
        if honeypot.strip():
            logger.warning(f"Honeypot triggered by IP {ip}")
            return JsonResponse({'error': 'Spam detected'}, status=400)

        if not user_question:
            return JsonResponse({'error': 'No question provided'}, status=400)
        
        # Check word limit
        if count_words(user_question) > MAX_WORDS_PER_QUESTION:
            return JsonResponse({'error': f'Question too long (max {MAX_WORDS_PER_QUESTION} words)'}, status=400)

        # Detect language
        lang = detect_language(user_question)
        data_lang = company_data[lang]

        # Add timestamp and increment count
        request.session['question_timestamps'].append(current_time)
        request.session['last_activity'] = current_time
        request.session['chat_count'] += 1
        request.session.modified = True

        # Check cache for repeated questions (avoids API calls)
        cache_key = f"response_{hash(user_question)}"
        cached_response = cache.get(cache_key)
        if cached_response:
            request.session['chat_history'].append({
                'question': user_question,
                'answer': cached_response
            })
            request.session.modified = True
            return JsonResponse({
                'response': cached_response,
                'history': request.session['chat_history'],
                'remaining': MAX_MESSAGES_PER_SESSION - request.session['chat_count']
            })

        # Load Q&A
        qa_pairs = load_qa_data()
        lang_qa = [pair for pair in qa_pairs if pair.get('lang', 'en') == lang]

        # Build prompt
        prompt = (
            f"You are CMSBot, an expert for {data_lang['name']}. "
            f"Specialize in {data_lang['specialty']}. "
            f"Services: {', '.join(data_lang['services'])}. "
            f"Products: {', '.join(data_lang['products'])}. "
            f"Answer in 1-2 short sentences. "
            f"Follow: {data_lang['note']}. Contact: {data_lang['contact']}.\n\n"
            "Examples:\n"
        )
        for pair in lang_qa[:5]:
            prompt += f"User: {pair['question']}\nChatbot: {pair['answer']}\n\n"

        for item in request.session.get('chat_history', []):
            prompt += f"User: {item['question']}\nChatbot: {item['answer']}\n"

        prompt += f"User: {user_question}\nChatbot:"

        # Call Gemini with concurrency control (lock prevents overload)
        chatbot_response = None
        with api_lock:
            try:
                model = genai.GenerativeModel('gemini-2.5-flash')
                response = model.generate_content(prompt)
                chatbot_response = response.text.strip()
                cache.set(cache_key, chatbot_response, 300)  # Cache for 5 min
            except Exception as e:
                logger.error(f"Gemini API error: {str(e)}")
                chatbot_response = 'Service temporarily unavailable. Please try again later.'

        # Save to history
        request.session['chat_history'].append({
            'question': user_question,
            'answer': chatbot_response
        })
        request.session.modified = True

        return JsonResponse({
            'response': chatbot_response,
            'history': request.session['chat_history'],
            'remaining': MAX_MESSAGES_PER_SESSION - request.session['chat_count']
        })

    return JsonResponse({'error': 'Invalid method'}, status=405)