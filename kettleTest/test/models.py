from django.db import models

class Test(models.Model):
    title = models.CharField('Название', max_length=100)
    description = models.TextField('Описание')
    createdate = models.DateTimeField('Дата создания', auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Тест'
        verbose_name_plural = 'Тесты'

class Question(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    category = models.CharField(max_length=5, null=True, blank=True)

    def __str__(self):
        return f'{self.text}, {str(self.id)}, {self.category}'

    class Meta:
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'

class Answer(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="answers" 
    )
    text = models.CharField(max_length=255)
    score = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.text}, {str(self.id)}, {self.score}'

    class Meta:
        verbose_name = 'Ответ'
        verbose_name_plural = 'Ответы'

class Category(models.Model):
    name = models.CharField(max_length=5) # например, A, B, C и т.д.
    PlusOrMinus = models.BooleanField(default=True)  # True для плюса, False для минуса
    minVal = models.IntegerField(default=0)
    maxVal = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

class Result(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField()
    categories = models.JSONField(default=list)

    def __str__(self):
        return f'{self.id} {self.name} {self.categories}'

    class Meta:
        verbose_name = 'Результат'
        verbose_name_plural = 'Результаты'


class Direction(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField()
    categories = models.JSONField(default=list)

    def __str__(self):
        return f'{self.id} {self.name} {self.categories}'

    class Meta:
        verbose_name = 'Направление'
        verbose_name_plural = 'Направления'


class LuscherColor(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class  LuscherPositionRule(models.Model):

    POSITION_GROUPS = [
        ("goal", "Goal (1-2)"),
        ("state", "State (3-4)"),
        ("suppressed", "Suppressed (5-6)"),
        ("stress", "Stress (7-8)"),
    ]

    position_group = models.CharField(max_length=20, choices=POSITION_GROUPS)
    color = models.ForeignKey(LuscherColor, on_delete=models.CASCADE)
    result_text = models.TextField()

    def __str__(self):
        return f"{self.position_group} - {self.color.name}"


class LuscherMainPair(models.Model):

    first_color = models.ForeignKey(
        LuscherColor,
        on_delete=models.CASCADE,
        related_name="first_pairs",
    )

    second_color = models.ForeignKey(
        LuscherColor,
        on_delete=models.CASCADE,
        related_name="second_pairs",
    )

    result_text = models.TextField()

    def __str__(self):
        return f"{self.first_color.name} + {self.second_color.name}"


class LuscherConflictRule(models.Model):

    color_a = models.ForeignKey(
        LuscherColor,
        on_delete=models.CASCADE,
        related_name="conflict_a",
    )

    color_b = models.ForeignKey(
        LuscherColor,
        on_delete=models.CASCADE,
        related_name="conflict_b",
    )

    result_text = models.TextField()

    def __str__(self):
        return f"{self.color_a.name} vs {self.color_b.name}"
    

class TestResult(models.Model):
    STATUS_CHOICES = [
        ('school', 'Школьник'),
        ('student', 'Студент'),
        ('worker', 'Работающий'),
    ]

    DIRECTION_CHOICES = [
        ('science', 'Естественные науки'),
        ('social', 'Социальные науки'),
        ('humanities', 'Гуманитарные науки'),
        ('technical', 'Технические'),
        ('economics', 'Экономика'),
    ]

    # 👇 ВАЖНО
    session_key = models.CharField(max_length=100)

    # данные пользователя
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    age = models.IntegerField()
    gender = models.CharField(max_length=10)

    education_direction = models.CharField(
        max_length=50, choices=DIRECTION_CHOICES, null=True, blank=True
    )
    work_direction = models.CharField(
        max_length=50, choices=DIRECTION_CHOICES, null=True, blank=True
    )

    avg_score = models.FloatField(null=True, blank=True)

    # тест
    test = models.ForeignKey('Test', on_delete=models.CASCADE)

    # результат
    result_text = models.TextField()

    # дата
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.test.name} vs {self.created_at}"