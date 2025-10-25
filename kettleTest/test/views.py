from django.shortcuts import render, redirect, get_object_or_404
from .models import Test, Question, Answer, Result, Category
from .forms import TestForm
from django.views.generic import DetailView
from collections import defaultdict
from datetime import datetime, timedelta
import logging
from django.conf import settings
from django.core.mail import EmailMessage
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from datetime import datetime
from django.utils.dateparse import parse_datetime
from django.utils.timezone import (
    localtime, make_aware, get_current_timezone, is_naive
)
import json
from django.http import JsonResponse
from django.core.mail import send_mail

def test_home(request):
    tests = Test.objects.all()
    return render(request, 'test/home.html', {'tests':tests})

def test_detail(request, pk):
    test = get_object_or_404(Test, pk=pk)
    questions = Question.objects.filter(test=test).prefetch_related("answers")
    attempts_key = f"test_{test.id}"

    if request.method == "POST":
        user_answersq = {}
        for q in questions:
            answer_id = request.POST.get(f"q{q.id}")
            if answer_id:
                user_answersq[q.id] = int(answer_id)
        
        scores = defaultdict(int)

        for _, aid in user_answersq.items():
            try:
                answer = Answer.objects.get(id=aid)
                category = answer.question.category
                scores[category] += answer.score
            except Answer.DoesNotExist:
                continue

        category_results = []
        for cat_name, score in scores.items():
            range_match = Category.objects.filter(
                name=cat_name,
                minVal__lte=score,
                maxVal__gte=score
            ).first()

            if range_match:
                if range_match.PlusOrMinus:
                    category_results.append(f"{cat_name}+")
                else:
                    category_results.append(f"{cat_name}-")
            
        all_results = Result.objects.all()

        matching_results = [
        result for result in all_results
        if set(result.categories).issubset(set(category_results))
        ]

        attempts = request.session.get(attempts_key, [])

        attempts.append({
            "at_id": len(attempts),
            "result_ids": [r.id for r in matching_results],
            "date": now().isoformat(),
        })

        request.session[attempts_key] = attempts

        return redirect("test_result", pk=test.id, atId=len(attempts)-1)

    return render(request, "test/detail.html", {
        "test": test,
        "questions": questions,
    })

def test_result(request, pk, atId):
    test = get_object_or_404(Test, pk=pk)
    result_ids = []
    info = request.session.get(f"test_{test.id}", [])
    for inf in info: 
        if inf.get("at_id") == atId:
            result_ids = inf.get("result_ids", [])
            break
    matching_results = Result.objects.filter(id__in=result_ids)

    return render(request, "test/result.html", {"result": matching_results, "test": test})

def results_list(request):
    tests_data = []

    for key, value in request.session.items():
        if key.startswith("test_"):
            test_id = key.split("_")[1]
            try:
                test = Test.objects.get(id=test_id)

                for attempt in value:
                    raw_date = attempt.get("date")
                    date_obj = None

                    if raw_date:
                        date_obj = parse_datetime(raw_date)
                        if date_obj:
                            # если дата naive — делаем aware с текущей таймзоной
                            if is_naive(date_obj):
                                date_obj = make_aware(date_obj, timezone=get_current_timezone())
                            # приводим к локальному времени Django
                            date_obj = localtime(date_obj)

                    tests_data.append({
                        "id": test.id,
                        "title": test.title,
                        "date": date_obj,
                        "at_id" : attempt.get("at_id"),
                    })
            except Test.DoesNotExist:
                continue

    # сортировка с приведением всех к aware
    aware_min = make_aware(datetime.min, timezone=get_current_timezone())
    tests_data.sort(key=lambda x: x["date"] or aware_min, reverse=True)

    return render(request, "test/results_list.html", {"tests": tests_data})

# def test_create(request):
#     error = ''
#     if request.method == 'POST':    
#         form = TestForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return  redirect('test_home')
#         else: 
#             error = 'Форма была неверной'
    
#     form = TestForm(request.POST or None)
    
#     data = {'form': form, 'error': error}
    
#     return render(request, 'test/test_create.html', data)

# def detail(request, id):
#     test = Test.objects.get(id=id)
#     return render(request, 'test/test_detail.html', {'test': test})

@require_POST
@csrf_protect
def send_result_telegram(request):

    return JsonResponse({"ok": True})
    


@require_POST
@csrf_protect
def send_result_email(request):
    """
    Ожидает JSON: { "test_id": int, "at_id": int, "email": str }
    Отправляет итог теста (с реальными результатами, как на странице test_result).
    """
    try:
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception:
            return JsonResponse({"ok": False, "error": "Неверный формат JSON"}, status=400)

        test_id = data.get("test_id")
        atId = data.get("at_id")
        email = data.get("email")

        if test_id is None or atId is None or not email:
            return JsonResponse({"ok": False, "error": "Не указаны обязательные поля"}, status=400)

        test = get_object_or_404(Test, id=test_id)
        attempts_key = f"test_{test.id}"
        info = request.session.get(attempts_key, [])
        ourInf = {}
        
        for inf in info: 
            if str(inf.get("at_id")) == atId:
                ourInf = inf
                break
         # --- проверяем наличие попытки ---
        if not ourInf:
            return JsonResponse({"ok": False, "error": "Попытка не найдена"}, status=404)

        matching_results = Result.objects.filter(id__in=ourInf.get("result_ids", []))

        # attempt = attempts[int(attempt_index)-1]
        # answers = attempt.get("answers", {})
        raw_date = ourInf.get("date")

        # --- дата прохождения ---
        date_obj = None
        if raw_date:
            date_obj = parse_datetime(raw_date)
            if date_obj and is_naive(date_obj):
                date_obj = make_aware(date_obj, timezone=get_current_timezone())
            if date_obj:
                date_obj = localtime(date_obj)


        # --- формируем тело письма ---
        body_lines = [
            f"Результаты теста: {test.title}",
            f"Дата прохождения: {date_obj.strftime('%d.%m.%Y %H:%M') if date_obj else '—'}",
            "",
            "Итог:",
        ]

        if matching_results:
            for res in matching_results:
                body_lines.append(f"- {res.name}")
                body_lines.append(f"{res.description}")
        else:
            body_lines.append("Подходящий результат не найден.")

        body_text = "\n".join(body_lines)

        # --- отправляем письмо ---
        send_mail(
            subject=f"Результаты теста '{test.title}'",
            message=body_text,
            from_email=None,
            recipient_list=[email],
            fail_silently=False,
        )

        return JsonResponse({"ok": True})

    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)
    
