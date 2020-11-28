from django.db import models
from django.contrib.auth.models import User
from .middleware import get_current_user
from django.db.models import Q

# Create your models here.
class Articles(models.Model):
    author = models.ForeignKey(User, on_delete = models.CASCADE, verbose_name='Владелец резюме', blank = True, null = True )
    create_date = models.DateTimeField(auto_now=True)
    name= models.CharField(max_length=200, verbose_name='user')
    last_name = models.CharField(max_length=200, verbose_name='Фамилия', default="default_name")
    first_name = models.CharField(max_length=200, verbose_name='Имя', default="some_value")
    phone = models.TextField(max_length=12, null=False, blank=False, unique=True, default="8900000000")
    mail = models.EmailField(max_length=254, default='@mail.ru')
    text = models.TextField(verbose_name='Описание')
    textinteres = models.TextField(verbose_name='Область научных интересов', blank=True)
    textwork = models.TextField(verbose_name='Предыдущий опыт', blank=True)
    textkeys = models.TextField(verbose_name='Ключевые компетенции', blank=True)
    
    def __str__(self):
        return self.first_name
    
    class Meta:
        verbose_name='Резюме'
        verbose_name_plural='Резюме'

class StatusFilterComments(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(Q(status=False, author = get_current_user()) | Q(status=False, article__author=get_current_user()) | Q(status=True))
    


class Comments(models.Model):
    article = models.ForeignKey(Articles, on_delete = models.CASCADE, verbose_name='Статья', blank = True, null = True,related_name='comments_articles' )
    author = models.ForeignKey(User, on_delete = models.CASCADE, verbose_name='Автор комментария', blank = True, null = True )
    create_date = models.DateTimeField(auto_now=True)
    text = models.TextField(verbose_name='Текст комментария')
    status = models.BooleanField(verbose_name='Видимость статьи', default=False)
    objects = StatusFilterComments()

