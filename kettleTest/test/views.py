from django.shortcuts import render, redirect, get_object_or_404
from .models import Test, Question, Answer, Result, Category
from .forms import TestForm
from django.views.generic import DetailView
from collections import defaultdict

def test_home(request):
    tests = Test.objects.all()
    return render(request, 'test/home.html', {'tests':tests})

def test_detail(request, pk):
    test = get_object_or_404(Test, pk=pk)
    questions = Question.objects.filter(test=test).prefetch_related("answers")

    if request.method == "POST":
        user_answers = {}
        for q in questions:
            answer_id = request.POST.get(f"q{q.id}")
            if answer_id:
                user_answers[q.id] = int(answer_id)

        request.session[f"test_{test.id}_answers"] = user_answers

        return redirect("test_result", pk=test.id)

    return render(request, "test/detail.html", {
        "test": test,
        "questions": questions,
    })

def test_result(request, pk):
    test = get_object_or_404(Test, pk=pk)

    user_answers = request.session.get(f"test_{pk}_answers", {})

    scores = defaultdict(int)

    for qid, aid in user_answers.items():
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

    return render(request, "test/result.html", {"result": matching_results, "test": test})

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