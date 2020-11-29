from django.shortcuts import render,redirect,HttpResponse

from .models import Articles, Comments, Question
from django.views.generic import ListView, DetailView,CreateView, UpdateView,DeleteView
from django.views.generic.edit import FormMixin
from .forms import ArticleForm, AuthUserForm, RegisterUserForm,CommentForm
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, request
from django.db import models
from .serializers import QuestionSerializer, AnswerSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import generics, status, viewsets
from django.template import Context, Template
from .models import Question
from .serializers import QuestionSerializer


class HomeListView(ListView):
    model = Articles
    template_name = 'index.html'
    context_object_name = 'list_articles'


# class LoginRequiredMixin(AccessMixin):
#     """Verify that the current user is authenticated."""
#     def dispatch(self, request, *args, **kwargs):
#         if not request.user.is_authenticated:
#             return self.handle_no_permission()
#         return super().dispatch(request, *args, **kwargs)

class CustomSuccessMessageMixin:
    @property
    def success_msg(self):
        return False
        
    def form_valid(self,form):
        messages.success(self.request, self.success_msg)
        return super().form_valid(form)
    def get_success_url(self):
        return '%s?id=%s' % (self.success_url, self.object.id)



class HomeDetailView(CustomSuccessMessageMixin, FormMixin, DetailView):
    model = Articles
    template_name = 'detail.html'
    context_object_name = 'get_article'
    form_class = CommentForm
    success_msg = 'Комментарий успешно создан, ожидайте модерации'
    
    
    def get_success_url(self):
        return reverse_lazy('detail_page', kwargs={'pk':self.get_object().id})
    
    def post(self,request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
    
    def form_valid(self,form):
        self.object = form.save(commit=False)
        self.object.article = self.get_object()
        self.object.author = self.request.user
        self.object.save()
        return super().form_valid(form)
    



def update_comment_status(request, pk, type):
    item = Comments.objects.get(pk=pk)
    if request.user != item.article.author:
        return HttpResponse('deny')
    
    if type == 'public':
        import operator
        item.status = operator.not_(item.status)
        item.save()
        template = 'comment_item.html'
        context = {'item':item, 'status_comment':'Комментарий опубликован'}
        return render(request, template, context)
        
    elif type == 'delete':
        item.delete()
        return HttpResponse('''
        <div class="alert alert-success">
        Комментарий удален
        </div>
        ''')
    
    return HttpResponse('1')



class ArticleCreateView(LoginRequiredMixin, CustomSuccessMessageMixin, CreateView):
    login_url = reverse_lazy('login_page')
    model = Articles
    template_name = 'edit_page.html'
    form_class = ArticleForm
    success_url = reverse_lazy('edit_page')
    success_msg = 'Запись создана'
    def get_context_data(self,**kwargs):
        kwargs['list_articles'] = Articles.objects.all().order_by('-id')
        return super().get_context_data(**kwargs)
    def form_valid(self,form):
        self.object = form.save(commit=False)
        self.object.author = self.request.user
        self.object.save()
        return super().form_valid(form)


class ArticlesCreateView(LoginRequiredMixin, CustomSuccessMessageMixin, CreateView):
    login_url = reverse_lazy('login_page')
    model = Articles
    template_name = 'userroom.html'
    form_class = ArticleForm
    success_url = reverse_lazy('userroom')
    success_msg = 'Запись создана'
    def get_context_data(self,**kwargs):
        kwargs['list_articles'] = Articles.objects.all().order_by('-id')
        return super().get_context_data(**kwargs)
    def form_valid(self,form):
        self.object = form.save(commit=False)
        self.object.author = self.request.user
        self.object.save()
        return super().form_valid(form)
    

class ArticleUpdateView(LoginRequiredMixin, CustomSuccessMessageMixin,UpdateView):
    model = Articles
    template_name = 'edit_page.html'
    form_class = ArticleForm
    success_url = reverse_lazy('edit_page')
    success_msg = 'Запись успешно обновлена'
    def get_context_data(self,**kwargs):
        kwargs['update'] = True
        return super().get_context_data(**kwargs)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.user != kwargs['instance'].author:
            return self.handle_no_permission()
        return kwargs

class ArticlesUpdateView(LoginRequiredMixin, CustomSuccessMessageMixin,UpdateView):
    model = Articles
    template_name = 'userroom.html'
    form_class = ArticleForm
    success_url = reverse_lazy('userroom')
    success_msg = 'Запись успешно обновлена'
    def get_context_data(self,**kwargs):
        kwargs['update'] = True
        return super().get_context_data(**kwargs)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.user != kwargs['instance'].author:
            return self.handle_no_permission()
        return kwargs

class MyprojectLoginView(LoginView):
    template_name = 'login.html'
    form_class = AuthUserForm
    success_url = reverse_lazy('index')
    def get_success_url(self):
        return self.success_url

class RegisterUserView(CreateView):
    model = User
    template_name = 'register_page.html'
    form_class = RegisterUserForm
    success_url = reverse_lazy('index')
    success_msg = 'Пользователь успешно создан'
    def form_valid(self,form):
        form_valid = super().form_valid(form)
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]
        aut_user = authenticate(username=username,password=password)
        login(self.request, aut_user)
        return form_valid

class MyProjectLogout(LogoutView):
    next_page = reverse_lazy('index')

class ArticleDeleteView(LoginRequiredMixin, DeleteView):
    model = Articles
    template_name = 'edit_page.html'
    success_url = reverse_lazy('edit_page')
    success_msg = 'Запись удалена'
    def post(self,request,*args,**kwargs):
        messages.success(self.request, self.success_msg)
        return super().post(request)
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.request.user != self.object.author:
            return self.handle_no_permission()
        success_url = self.get_success_url()
        self.object.delete()
        return HttpResponseRedirect(success_url)

class ArticlesDeleteView(LoginRequiredMixin, DeleteView):
    model = Articles
    template_name = 'userroom.html'
    success_url = reverse_lazy('userroom')
    success_msg = 'Запись удалена'
    def post(self,request,*args,**kwargs):
        messages.success(self.request, self.success_msg)
        return super().post(request)
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.request.user != self.object.author:
            return self.handle_no_permission()
        success_url = self.get_success_url()
        self.object.delete()
        return HttpResponseRedirect(success_url)

# queryset = Question.objects.all()
class GetQuestion(viewsets.ModelViewSet):
    queryset = Question.objects.filter()
    permission_classes = (IsAuthenticated,)
    serializer_class = QuestionSerializer

    def get(self, request, format=None):
        questions = Question.objects.filter(visible=True, )
        last_point = QuestionSerializer(questions, many=True)
        return Response(last_point.data)



class QuestionAnswer(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = AnswerSerializer

    def post(self, request, format=None):
        answer = AnswerSerializer(data=request.data, context=request)
        if answer.is_valid(raise_exception=True):
            answer.save()
            return Response({'result': 'OK'})

def godevtest(GetQuestion):
    context = {
        'title': GetQuestion.object.title,
    }

    templates = 'godevtest.html'

    return render(request, templates, context)

def index(request):
    context = {

    }

    templates = 'index.html'

    return render(request, templates, context)


def GoDev(request):
    context = {

    }

    templates = 'godev.html'

    return render(request, templates, context)


def about(request):
    context = {

    }

    templates = 'about2.html'

    return render(request, templates, context)


def careers(request):
    context = {

    }

    templates = 'careers.html'

    return render(request, templates, context)


def comingsoon(request):
    context = {

    }

    templates = 'coming_soon.html'

    return render(request, templates, context)


def contact(request):
    context = {

    }

    templates = 'contact.html'

    return render(request, templates, context)


def portfolio(request):
    context = {

    }

    templates = 'portfolio.html'

    return render(request, templates, context)


def userroom(request):
    templates = 'userroom.html'
    context = {

    }
    return render(request, templates, context)





    
    
    

    
    
    
    
    
    
