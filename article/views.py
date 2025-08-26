from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden, JsonResponse
from school.models import  Comment
from .models import Article
import random
from utils.s3 import upload_fileobj_to_s3, public_url

@login_required
def article_detail(request, article_id):
    article = get_object_or_404(Article, pk=article_id)
    comments = (Comment.objects
                .filter(receiver_content_type__model='article',
                        receiver_object_id=article.pk)
                .select_related('sender')
                .prefetch_related('children__sender')
                .prefetch_related('children')
                .order_by('-created_at'))
    return render(request, 'article.html', {
        'article': article,
        'comments': comments
    })




@login_required
def article_create(request):
    if request.method == 'POST':
        try:
            title = request.POST.get('title')
            content = request.POST.get('content')
            f = request.FILES.get("image")

            image_url = None
            if f:
                try:
                    f.open()
                except Exception:
                    pass

                try:
                    f.seek(0)
                except Exception:
                    pass

                key = upload_fileobj_to_s3(f, content_type=f.content_type)
                
                image_url = public_url(key)

            a = Article.objects.create(
                title=title,
                content=content,
                image=image_url,
                student=request.user
            )

            return redirect('Article', a.pk)
        except Exception as e:
            print(e)
            return render(request, 'article_form.html', {'article': None, 'error' : 'error while creating article'})

    return render(request, 'article_form.html', {'article': None})




@login_required
def article_update(request, article_id):
    article = get_object_or_404(Article, pk=article_id, student=request.user)

    if request.method == 'POST':
        # حدّث الحقول النصية
        article.title = request.POST.get('title') or article.title
        article.content = request.POST.get('content') or article.content

        # إن وُجد ملف جديد ارفعه إلى S3 واحفظ رابطَه
        f = request.FILES.get('image')
        if f:
            try:
                f.open()
            except Exception:
                pass
            try:
                f.seek(0)
            except Exception:
                pass

            key = upload_fileobj_to_s3(f, content_type=f.content_type)
                
            image_url = public_url(key)

            article.image = image_url #type:ignore

        article.save()
        return redirect('Article', article.pk)

    return render(request, 'article_form.html', {'article': article})


@login_required
@require_http_methods(['DELETE'])
def article_delete(request, article_id):
    is_teacher = getattr(request, 'is_teacher', None)
    is_supervisor = getattr(request, 'is_supervisor', None)
    teacher = getattr(request, 'teacher', None)
    article = get_object_or_404(Article, id=article_id)

    if teacher is None:
        return HttpResponseForbidden()
    if is_teacher is None:
        return HttpResponseForbidden()
    if is_supervisor is None:
        return HttpResponseForbidden()
    if article.student != request.user:
        return HttpResponseForbidden()
    
    article.delete()
    return JsonResponse({'message': 'article deleted successfully.'}, status=204)



def articles_list(request):
    articles = Article.objects.all().order_by("-created_at").select_related('student')
    paginator = Paginator(articles, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.page(page_number)
    return render(request, "article_list.html", { 'articles' : page_obj } )


@login_required
def my_articles(request):
    articles = Article.objects.filter(student=request.user).order_by("-created_at")
    paginator = Paginator(articles, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.page(page_number)
    return render(request, "article_list.html", { 'articles' : page_obj } )


@login_required
@require_http_methods(['POST'])
def comment_add_comment_article(request, article_id, comment_id):
    article = get_object_or_404(Article.objects.only('id'), id=article_id)
    parent = get_object_or_404(Comment.objects.only("id"), id=comment_id)
    content = request.POST.get('content')
    if content is None:
        return redirect("Article", article.pk)
    Comment.objects.create(
        content=content,
        sender=request.user,
        receiver=parent,
        )
    return redirect("Article", article.pk)



@login_required
@require_http_methods(["POST"])
def comment_add_article(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    content = request.POST.get('content')
    if content is None:
        return redirect("Article", article.pk)
    Comment.objects.create(
        content=content,
        sender=request.user,
        receiver=article,
        )
    return redirect("Article", article.pk)
