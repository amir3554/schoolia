from typing import Any
from django.db.models.query import QuerySet
from django.forms import BaseModelForm
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.urls import reverse
from django.views.generic import CreateView, UpdateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods 
from django.shortcuts import get_object_or_404
from school.models import Course, Unit, Lesson, Comment
from django.http import JsonResponse
from teacher.forms import CourseModelForm, UnitModelForm, LessonModelForm
from utils.s3 import upload_fileobj_to_s3, public_url
import os


class CoursesManageListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Course
    template_name = "operations/main_manage.html"


    def test_func(self):
        is_teacher = getattr(self.request, 'is_teacher', None)
        is_supervisor = getattr(self.request, 'is_supervisor', None)
        teacher = getattr(self.request, 'teacher', None)
        if teacher is None:
           return False
        if is_teacher is None:
           return False
        if is_supervisor is None:
           return False
        
        return is_supervisor or is_teacher

    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset()
        

class UnitsManageListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Unit
    template_name = "operations/manage_units.html"


    def test_func(self):
        is_teacher = getattr(self.request, 'is_teacher', None)
        is_supervisor = getattr(self.request, 'is_supervisor', None)
        teacher = getattr(self.request, 'teacher', None)
        if teacher is None:
           return False
        if is_teacher is None:
           return False
        if is_supervisor is None:
           return False
        
        return is_supervisor or is_teacher


    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        course_id = self.kwargs.get('course_id')
        if course_id is not None:
            course = get_object_or_404(Course.objects.only('id'), id=course_id)
            context['course'] = course
        return context


    def get_queryset(self) -> QuerySet[Any]:
        qs = (
            super()
            .get_queryset()
            .select_related("course")   # جلب FK بكفاءة
            .order_by('-created_at')
        )
        course_id = self.kwargs.get("course_id")
        if course_id is not None:
            qs = qs.filter(course_id=course_id)  # <-- احفظ الناتج
        return qs



class LessonsManageListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Lesson
    template_name = "operations/manage_lessons.html"


    def test_func(self):
        is_teacher = getattr(self.request, 'is_teacher', None)
        is_supervisor = getattr(self.request, 'is_supervisor', None)
        teacher = getattr(self.request, 'teacher', None)
        if teacher is None:
           return False
        if is_teacher is None:
           return False
        if is_supervisor is None:
           return False
        
        return is_supervisor or is_teacher


    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        course_id = self.kwargs['course_id']
        unit_id = self.kwargs['unit_id']
        course = get_object_or_404(Course.objects.only('id'), id=course_id)
        unit = get_object_or_404(Unit.objects.only('id'), id=unit_id)
        context['course'] = course
        context['unit'] = unit
        return context


    def get_queryset(self) -> QuerySet[Any]:
        qs = (
            super()
            .get_queryset()
            .select_related("unit")   # جلب FK بكفاءة
            .order_by('-created_at')
        )
        unit_id = self.kwargs.get("unit_id")
        if unit_id is not None:
            qs = qs.filter(unit_id=unit_id)  # <-- احفظ الناتج
        return qs




class CommentsManageListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Comment
    template_name = "operations/comments_manage.html"
    context_object_name = 'comments'


    def test_func(self):
        is_teacher = getattr(self.request, 'is_teacher', None)
        is_supervisor = getattr(self.request, 'is_supervisor', None)
        teacher = getattr(self.request, 'teacher', None)
        if teacher is None:
           return False
        if is_teacher is None:
           return False
        if is_supervisor is None:
           return False
        
        return is_supervisor or is_teacher

    def get_queryset(self) -> QuerySet[Any]:
        qs =  super().get_queryset()
        qs.select_related('sender').order_by('-created_at')
        return qs





class CourseCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Course
    form_class = CourseModelForm
    template_name = 'operations/create_course.html'

    
    def test_func(self):
        is_teacher = getattr(self.request, 'is_teacher', None)
        is_supervisor = getattr(self.request, 'is_supervisor', None)
        teacher = getattr(self.request, 'teacher', None)
        if teacher is None:
           return False
        if is_teacher is None:
           return False
        if is_supervisor is None:
           return False
        
        return is_supervisor
    

    def form_valid(self, form):

        self.object = form.save(commit=False)

        f = self.request.FILES.get("image")
        if f:
            _, ext = os.path.splitext(f.name)
            if ext:
                if ext in ('.jpg', '.jpeg', '.png'):

                    key = upload_fileobj_to_s3(f, content_type=f.content_type)
                    self.object.image = public_url(key)

                    form.cleaned_data["image"] = None
                    if "image" in form.files:
                        del form.files["image"]

        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        return reverse('CoursesManage')


class UnitCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Unit
    form_class = UnitModelForm
    template_name = 'operations/create_unit.html'

    
    def test_func(self):
        is_teacher = getattr(self.request, 'is_teacher', None)
        is_supervisor = getattr(self.request, 'is_supervisor', None)
        teacher = getattr(self.request, 'teacher', None)
        if teacher is None:
           return False
        if is_teacher is None:
           return False
        if is_supervisor is None:
           return False
        
        return is_supervisor


    def get_form(self, form_class = None):
        form = super().get_form(form_class)
        course_id = self.kwargs['course_id']
        form.fields['course'].queryset = form.fields['course'].queryset.filter(id=course_id) #type:ignore
        return form



    def form_valid(self, form):
        self.object = form.save()
        return super().form_valid(form)




    def get_success_url(self):
        return reverse('UnitsManage', args=[self.object.course.pk])


class LessonCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Lesson
    form_class = LessonModelForm
    template_name = 'operations/create_lesson.html'

    
    def test_func(self):
        is_teacher = getattr(self.request, 'is_teacher', None)
        is_supervisor = getattr(self.request, 'is_supervisor', None)
        teacher = getattr(self.request, 'teacher', None)
        if teacher is None:
           return False
        if is_teacher is None:
           return False
        if is_supervisor is None:
           return False
        
        return is_supervisor


    def get_form(self, form_class = None):
        form = super().get_form(form_class)
        unit_id = self.kwargs['unit_id']
        form.fields['unit'].queryset = form.fields['unit'].queryset.filter(id=unit_id) #type:ignore
        return form

    def form_valid(self, form):

        self.object = form.save(commit=False)

        image = self.request.FILES.get("image")
        if image:
            _, ext = os.path.splitext(image.name)
            if ext:
                if ext in ('.jpg', '.jpeg', '.png'):
                    key = upload_fileobj_to_s3(image, content_type=image.content_type)
                    self.object.image = public_url(key)

                    form.cleaned_data["image"] = None
                    if "image" in form.files:
                        del form.files["image"]

        video = self.request.FILES.get("video")
        if video:
            _, ext = os.path.splitext(video.name)
            if ext:
                if ext in ('.mp4',):
                    key = upload_fileobj_to_s3(video, content_type=video.content_type)
                    self.object.video = public_url(key)

                    form.cleaned_data["video"] = None
                    if "video" in form.files:
                        del form.files["video"]

        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


    def get_success_url(self):
        return reverse('LessonsManage', args=[self.object.unit.course.pk, self.object.unit.pk])
    



class CourseUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Course
    form_class = CourseModelForm
    template_name = 'operations/create_course.html'


    
    def test_func(self):
        is_teacher = getattr(self.request, 'is_teacher', None)
        is_supervisor = getattr(self.request, 'is_supervisor', None)
        teacher = getattr(self.request, 'teacher', None)
        if teacher is None:
           return False
        if is_teacher is None:
           return False
        if is_supervisor is None:
           return False
        
        return is_supervisor or is_teacher


    def form_valid(self, form):

        self.object = form.save(commit=False)

        f = self.request.FILES.get("image")
        if f:
            _, ext = os.path.splitext(f.name)
            if ext:
                if ext in ('.jpg', '.jpeg', '.png'):

                    key = upload_fileobj_to_s3(f, content_type=f.content_type)
                    self.object.image = public_url(key)

                    form.cleaned_data["image"] = None
                    if "image" in form.files:
                        del form.files["image"]

        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


    def get_success_url(self) -> str:
        return reverse('CoursesManage')


class UnitUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Unit
    form_class = UnitModelForm
    template_name = 'operations/create_unit.html'

    
    def test_func(self):
        is_teacher = getattr(self.request, 'is_teacher', None)
        is_supervisor = getattr(self.request, 'is_supervisor', None)
        teacher = getattr(self.request, 'teacher', None)
        if teacher is None:
           return False
        if is_teacher is None:
           return False
        if is_supervisor is None:
           return False
        
        return is_supervisor or is_teacher


    def get_form(self, form_class = None):
        form = super().get_form(form_class)
        course_id = self.kwargs['course_id']
        form.fields['course'].queryset = form.fields['course'].queryset.filter(id=course_id) #type:ignore
        return form

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        self.object = form.save()
        return super().form_valid(form)

    
    def get_success_url(self):
        return reverse('UnitsManage', args=[self.object.course.pk])


class LessonUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Lesson
    form_class = LessonModelForm
    template_name = 'operations/create_lesson.html'

    
    def test_func(self):
        is_teacher = getattr(self.request, 'is_teacher', None)
        is_supervisor = getattr(self.request, 'is_supervisor', None)
        teacher = getattr(self.request, 'teacher', None)
        if teacher is None:
           return False
        if is_teacher is None:
           return False
        if is_supervisor is None:
           return False
        
        return is_supervisor or is_teacher


    def get_form(self, form_class = None):
        form = super().get_form(form_class)
        unit_id = self.kwargs['unit_id']
        form.fields['unit'].queryset = form.fields['unit'].queryset.filter(id=unit_id) #type:ignore
        return form


    def form_valid(self, form):

        self.object = form.save(commit=False)

        image = self.request.FILES.get("image")
        if image:
            _, ext = os.path.splitext(image.name)
            if ext:
                if ext in ('.jpg', '.jpeg', '.png'):
                    key = upload_fileobj_to_s3(image, content_type=image.content_type)
                    self.object.image = public_url(key)

                    form.cleaned_data["image"] = None
                    if "image" in form.files:
                        del form.files["image"]

        video = self.request.FILES.get("video")
        if video:
            _, ext = os.path.splitext(video.name)
            if ext:
                if ext in ('.mp4'):
                    key = upload_fileobj_to_s3(video, content_type=video.content_type)
                    self.object.video = public_url(key)

                    form.cleaned_data["video"] = None
                    if "video" in form.files:
                        del form.files["video"]

        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


    def get_success_url(self):
        return reverse('LessonsManage', args=[self.object.unit.course.pk, self.object.unit.pk])
    
    





@login_required
@require_http_methods(['DELETE'])
def delete_course(request, pk):

    is_supervisor = getattr(request, 'is_supervisor', None)
    teacher = getattr(request, 'teacher', None)

    if teacher and is_supervisor: 
        course = get_object_or_404(Course, id=pk)
        course.delete()
        return JsonResponse({'message': 'course deleted successfully.'}, status=204)
    else:
        return HttpResponseForbidden()


@login_required
@require_http_methods(['DELETE'])
def delete_unit(request, pk):
    is_supervisor = getattr(request, 'is_supervisor', None)
    teacher = getattr(request, 'teacher', None)

    if teacher and is_supervisor: 
        unit = get_object_or_404(Unit, id=pk)
        unit.delete()
        return JsonResponse({'message': 'unit deleted successfully.'}, status=204)
    else:
        return HttpResponseForbidden()


@login_required
@require_http_methods(['DELETE'])
def delete_lesson(request, pk):
    is_supervisor = getattr(request, 'is_supervisor', None)
    teacher = getattr(request, 'teacher', None)

    if teacher and is_supervisor: 
        lesson = get_object_or_404(Lesson, id=pk)
        lesson.delete()
        return JsonResponse({'message': 'lesson deleted successfully.'}, status=204)
    else:
        return HttpResponseForbidden()


@login_required
@require_http_methods(['DELETE'])
def delete_comment(request, pk):
    is_teacher = getattr(request, 'is_teacher', None)
    is_supervisor = getattr(request, 'is_supervisor', None)
    teacher = getattr(request, 'teacher', None)

    if teacher is None:
        return HttpResponseForbidden()
    if is_teacher is None:
        return HttpResponseForbidden()
    if is_supervisor is None:
        return HttpResponseForbidden()
    
    comment = get_object_or_404(Comment, id=pk)
    comment.delete()
    return JsonResponse({'message': 'comment deleted successfully.'}, status=204)
