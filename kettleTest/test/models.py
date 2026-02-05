from django.db import models

class Test(models.Model):
    title = models.CharField('Название', max_length=100)
    description = models.TextField('Описание')
    createDate = models.DateTimeField('Дата создания', auto_now_add=True)

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