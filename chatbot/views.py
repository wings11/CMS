from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
import time
from .chatbot import (
    initialize_session, validate_input, find_match, generate_gemini_response,
    record_cost_and_check_limit, load_qa_data, company_data, MAX_MESSAGES_PER_SESSION
)

@csrf_exempt
def chatbot_view(request):
    ip = request.META.get('REMOTE_ADDR', 'unknown')
    now = time.time()
    ip_key = f"ip_rate_{ip}"
    ip_requests = cache.get(ip_key, [])
    ip_requests = [t for t in ip_requests if now - t < 60]
    if len(ip_requests) >= 50:
        return JsonResponse({'error': 'Too many requests from your IP. Please wait.'}, status=429)
    ip_requests.append(now)
    cache.set(ip_key, ip_requests, 60)
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)
    current_time = time.time()
    initialize_session(request, current_time)
    if request.session['chat_count'] >= MAX_MESSAGES_PER_SESSION:
        return JsonResponse({'error': 'You’ve reached the 500-message limit for this session.'}, status=429)
    request.session['question_timestamps'] = [t for t in request.session['question_timestamps'] if current_time - t < 60]
    if len(request.session['question_timestamps']) >= 10:
        return JsonResponse({'error': 'Rate limit exceeded. Please wait before asking more questions.'}, status=429)
    validation_error, user_question, lang = validate_input(request, ip)
    if validation_error:
        return JsonResponse(validation_error, status=400)
    data_lang = company_data[lang]
    request.session['question_timestamps'].append(current_time)
    request.session['last_activity'] = current_time
    request.session['chat_count'] += 1
    request.session.modified = True
    cache_key = f"response_{hash(user_question)}"
    cached_response = cache.get(cache_key)
    if cached_response:
        request.session['chat_history'].append({'question': user_question, 'answer': cached_response})
        request.session.modified = True
        return JsonResponse({'response': cached_response, 'history': request.session['chat_history'], 'remaining': MAX_MESSAGES_PER_SESSION - request.session['chat_count']})
    if record_cost_and_check_limit():
        fallback_response = "This chatbot is temporarily unavailable. Please try again later."
        request.session['chat_history'].append({'question': user_question, 'answer': fallback_response})
        request.session.modified = True
        return JsonResponse({'response': fallback_response, 'history': request.session['chat_history'], 'remaining': MAX_MESSAGES_PER_SESSION - request.session['chat_count']})
    qa_pairs = load_qa_data()
    lang_qa = [pair for pair in qa_pairs if pair.get('lang', 'en') == lang]
    match = find_match(user_question, lang_qa)
    chatbot_response = match if match else generate_gemini_response(user_question, lang_qa, data_lang, lang, request)
    cache.set(cache_key, chatbot_response, 300)
    request.session['chat_history'].append({'question': user_question, 'answer': chatbot_response})
    request.session.modified = True
    return JsonResponse({'response': chatbot_response, 'history': request.session['chat_history'], 'remaining': MAX_MESSAGES_PER_SESSION - request.session['chat_count']})