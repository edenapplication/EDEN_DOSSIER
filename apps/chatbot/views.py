import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import ChatbotKnowledge, ChatbotUnknown


FALLBACK_RESPONSES = [
    "Je transmets votre question à notre équipe. Un conseiller EDEN GROUP vous répondra très prochainement.",
    "Excellente question ! Notre équipe spécialisée va vous apporter une réponse personnalisée sous 24h.",
    "Je note votre demande. Pour toute urgence, contactez-nous directement au +237 653 35 05 03.",
]

GREETINGS = ['bonjour', 'bonsoir', 'salut', 'hello', 'hi', 'bonne journée']


def get_chatbot_response(message):
    msg_lower = message.lower().strip()

    if any(g in msg_lower for g in GREETINGS):
        return "Bonjour ! Je suis Martin Assistant, votre conseiller immobilier personnel. Comment puis-je vous aider aujourd'hui ?"

    knowledges = ChatbotKnowledge.objects.filter(is_active=True)
    best_match = None
    best_score = 0

    for knowledge in knowledges:
        keywords = knowledge.get_keywords_list()
        score = sum(1 for kw in keywords if kw in msg_lower)
        if score > best_score:
            best_score = score
            best_match = knowledge

    if best_match and best_score > 0:
        return best_match.answer

    ChatbotUnknown.objects.create(question=message)
    return FALLBACK_RESPONSES[len(message) % len(FALLBACK_RESPONSES)]


@csrf_exempt
@require_POST
def chatbot_api(request):
    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        if not message:
            return JsonResponse({'error': 'Message vide'}, status=400)
        response = get_chatbot_response(message)
        return JsonResponse({'response': response, 'status': 'ok'})
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Format invalide'}, status=400)