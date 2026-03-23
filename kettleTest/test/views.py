from django.shortcuts import render, redirect, get_object_or_404
from .models import Test, Question, Answer, Result, Category, Direction
from django.db.models.expressions import RawSQL
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
from .models import LuscherMainPair, LuscherPositionRule, LuscherConflictRule,TestResult
import json
from django.http import JsonResponse
from django.core.mail import send_mail
def test_home(request):

    if request.session.get('user_data'):
        tests = Test.objects.all()
        return render(request, 'test/home.html', {
            'tests': tests,
            'user_data': True
        })

    if request.method == "POST":
        request.session['user_data'] = {
            'status': request.POST.get('status'),
            'age': request.POST.get('age'),
            'gender': request.POST.get('gender'),
            'education_direction': request.POST.get('education_direction'),
            'avg_score': request.POST.get('avg_score'),
            'work_direction': request.POST.get('work_direction'),
        }
        return redirect('test_home')

    tests = Test.objects.all()
    return render(request, 'test/home.html', {
        'tests': tests,
        'user_data': False
    })

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
        
        scoreskettle = defaultdict(int)
        scoresholland = defaultdict(int)
        

        if test.id == 3:
            for _, aid in user_answersq.items():
                try:
                    answer = Answer.objects.get(id=aid)
                    category = answer.question.category
                    scoreskettle[category] += answer.score
                except Answer.DoesNotExist:
                    continue

            category_results = []
            for cat_name, score in scoreskettle.items():
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


            directions = Direction.objects.all()

            input_set = set(category_results)

            best = []
            max_match = 0

            for d in directions:
                match = len(set(d.categories) & input_set)
                if match > max_match:
                    best = [d]
                    max_match = match
                elif match == max_match:
                    best.append(d)

            if len(best) == 0 :
                best = Direction.objects.all()

            attempts = request.session.get(attempts_key, [])

            attempts.append({
                "at_id": len(attempts),
                "result_ids": [r.id for r in matching_results],
                "date": now().isoformat(),
                "direction": [b.name for b in best],
            })

            request.session[attempts_key] = attempts

            return redirect("test_result", pk=test.id, atId=len(attempts)-1)
        elif test.id == 4: 
            for _, aid in user_answersq.items():
                try:
                    answer = Answer.objects.get(id=aid)
                    scoresholland[answer.score] += 1
                except Answer.DoesNotExist:
                    continue

            max_key = max(scoresholland, key=scoresholland.get)
            
            res = [
                r for r in Result.objects.filter(test=test.id)
                if max_key in r.categories
            ]
            res = res[0] if res else None
            attempts = request.session.get(attempts_key, [])

            attempts.append({
                "at_id": len(attempts),
                "result": res.id if res else None,
                "date": now().isoformat(),
            })

            request.session[attempts_key] = attempts
                
            return redirect("test_result", pk=test.id, atId=len(attempts)-1)
        elif test.id == 5:
            first_attempt = request.POST.get("first_attempt")
            second_attempt = request.POST.get("second_attempt")

            first = [int(x) for x in first_attempt.split(",")]
            second = [int(x) for x in second_attempt.split(",")]

            result_text = analyze_luscher(first, second)
            result_objects = []

            attempts = request.session.get(attempts_key, [])

            attempts.append({
            "at_id": len(attempts)-1,
            "name": "Тест Люшера",
            "description": result_text,
            "date": now().isoformat(),
            })

            result_objects.append({
            "at_id": len(attempts),
            "name": "Тест Люшера",
            "description": result_text,
            "date": now().isoformat(),
            })

            request.session[attempts_key] = result_objects

            return redirect("test_result", pk=test.id, atId=len(attempts)-1)
    if test.id == 5:
        return render(request, "test/lusher_detail.html", {"test": test, "questions": questions})
    return render(request, "test/detail.html", {
        "test": test,
        "questions": questions,
    })

def test_result(request, pk, atId):
    test = get_object_or_404(Test, pk=pk)
    result_ids = []
    info = request.session.get(f"test_{test.id}", [])
    if test.id == 3 :
        for inf in info: 
            if inf.get("at_id") == atId:
                result_ids = inf.get("result_ids", [])
                direction = inf.get("direction", [])
                break
        matching_results = Result.objects.filter(id__in=result_ids)

        save_test_result(request, test, "\n\n".join([f"{r.name}\n{r.description}" for r in matching_results]))
        return render(request, "test/result.html", {"result": matching_results, "test": test, "direction": direction})
    elif test.id == 4: 
        for inf in info: 
            if inf.get("at_id") == atId:
                result_ids = inf.get("result", 0)
                break
        result = Result.objects.filter(id=result_ids).first() if result_ids else None

        save_test_result(request, test, result.description if result else "")
        return render(request, "test/result.html", {"result": [result] if result else [],"test": test}) 
    elif test.id == 5: 
        save_test_result(
            request,
            test,
            "\n\n".join([f"{r['name']}\n{r['description']}" for r in info])) 
        return render(request, "test/result.html", {"result": info if info else [],"test": test})
    

def results_list(request):
    session_key = get_session_key(request)

    results = TestResult.objects.filter(
        session_key=session_key
    ).select_related('test').order_by('-created_at')

    return render(request, "test/results_list.html", {"tests": results})

@require_POST
@csrf_protect
def send_result_telegram(request):

    return JsonResponse({"ok": True})
    

@require_POST
@csrf_protect
def send_result_email(request):
    try:
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception:
            return JsonResponse({"ok": False, "error": "Неверный формат JSON"}, status=400)

        test_id = data.get("test_id")
        at_id = data.get("at_id")
        email = data.get("email")

        if not test_id or not at_id or not email:
            return JsonResponse({"ok": False, "error": "Не указаны обязательные поля"}, status=400)

        test = get_object_or_404(Test, id=test_id)

        session_key = get_session_key(request)

        attempt = TestResult.objects.filter(
            session_key=session_key, test=test, id=at_id
        ).select_related('test').order_by('-created_at').first()

        # 📅 Дата
        date_obj = attempt.created_at
        if date_obj:
            if is_naive(date_obj):
                date_obj = make_aware(date_obj, timezone=get_current_timezone())
            date_obj = localtime(date_obj)

        body_lines = [
            f"Результаты теста: {test.title}",
            f"Дата прохождения: {date_obj.strftime('%d.%m.%Y %H:%M') if date_obj else '—'}",
            "",
            f"Итог: {attempt.result_text}",
        ]



        send_mail(
            subject=f"Результаты теста '{test.title}'",
            message="\n".join(body_lines),
            from_email=None,
            recipient_list=[email],
            fail_silently=False,
        )

        return JsonResponse({"ok": True})

    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


def analyze_luscher(first_attempt, second_attempt):
    """
    first_attempt и second_attempt — списки из 8 id цветов
    Возвращает готовый текст психологического отчета
    """
    text_parts = []

    goal = first_attempt[:2]
    state = first_attempt[2:4]
    suppressed = first_attempt[4:6]
    stress = first_attempt[6:8]

    pair = LuscherMainPair.objects.filter(
        first_color_id=goal[0],
        second_color_id=goal[1]
    ).first()
    if pair:
        text_parts.append("Главная тенденция:\n" + pair.result_text)

    for color in goal:
        rule = LuscherPositionRule.objects.filter(
            position_group="goal",
            color_id=color
        ).first()
        if rule:
            text_parts.append(rule.result_text)

    for color in stress:
        rule = LuscherPositionRule.objects.filter(
            position_group="stress",
            color_id=color
        ).first()
        if rule:
            text_parts.append(rule.result_text)

    for c1 in first_attempt:
        for c2 in first_attempt:
            conflict = LuscherConflictRule.objects.filter(
                color_a_id=c1,
                color_b_id=c2
            ).first()
            if conflict:
                text_parts.append(conflict.result_text)

    changes = []
    for idx, color in enumerate(first_attempt):
        try:
            pos2 = second_attempt.index(color)
        except ValueError:
            continue 
        if abs(pos2 - idx) >= 3:
            color_name = LuscherPositionRule.objects.filter(color_id=color).first().color.name
            changes.append(f"Изменение позиции цвета {color_name} между попытками ({idx+1} → {pos2+1}) может говорить о компенсации или изменении приоритетов.")

    if changes:
        text_parts.append("\nОсобенности изменений между попытками:\n" + "\n".join(changes))

    return "\n\n".join(text_parts)


def get_session_key(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key

def save_test_result(request, test, result_text):
    user_data = request.session.get('user_data')

    if not user_data:
        return

    session_key = get_session_key(request)

    TestResult.objects.create(
        session_key=session_key,
        status=user_data.get('status'),
        age=user_data.get('age'),
        gender=user_data.get('gender'),
        education_direction=user_data.get('education_direction'),
        work_direction=user_data.get('work_direction'),
        avg_score=user_data.get('avg_score'),
        test=test,
        result_text=result_text
    )