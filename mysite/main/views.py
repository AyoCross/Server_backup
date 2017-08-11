
from django.http import HttpResponse, Http404, HttpResponseForbidden
from django.views.generic import View
from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
# from django.utils.encoding import smart_text
from django.db.models import Count, Q
from django.contrib.auth.models import User

from guardian.shortcuts import assign_perm, get_perms
from guardian.core import ObjectPermissionChecker
from guardian.decorators import permission_required

# import markdown2  # 在models中使用

from . import models, forms, misc

# Create your views here.

PER_PAGE = settings.MY_SITE['PER_PAGE']
PER_PAGE_ADMIN = settings.MY_SITE['PER_PAGE_ADMIN']


def get_site_meta():
    seo = {}
    try:
        record = models.BlogMeta.objects.get(key='blog_name')
        seo['title'] = record.value
    except models.BlogMeta.DoesNotExist:
        pass

    try:
        record = models.BlogMeta.objects.get(key='blog_desc')
        seo['desc'] = record.value
    except models.BlogMeta.DoesNotExist:
        pass

    try:
        record = models.BlogMeta.objects.get(key='owner')
        seo['author'] = record.value
    except models.BlogMeta.DoesNotExist:
        pass

    try:
        record = models.BlogMeta.objects.get(key='keywords')
        seo['keywords'] = record.value
    except models.BlogMeta.DoesNotExist:
        pass

    try:
        record = models.BlogMeta.objects.get(key='blog_subtitle')
        seo['subtitle'] = record.value
    except models.BlogMeta.DoesNotExist:
        pass

    try:
        record = models.BlogMeta.objects.get(key='google_verify')
        seo['google_verify'] = record.value
    except models.BlogMeta.DoesNotExist:
        pass

    try:
        record = models.BlogMeta.objects.get(key='baidu_verify')
        seo['baidu_verify'] = record.value
    except models.BlogMeta.DoesNotExist:
        pass

    return seo


def get_user_info(user):
    try:
        data = {
            'username': user.username,
            'display_name': user.account.display_name,
            'biography': user.account.biography,
            'homepage': user.account.homepage,
            'weixin': user.account.weixin,
            'douban': user.account.douban,
            'zhihu': user.account.zhihu,
            'github': user.account.github,
            'weibo': user.account.weibo,
        }
    except:
        data = None

    return data


class Index(View):  # 通用视图
    template_name = 'main/index.html'

    def get(self, request):
        data = {}

        tag = request.GET.get('tag')
        category = request.GET.get('category')
        keywords = request.GET.get('keywords')
        try:
            tag = int(tag) if tag else 0
            category = int(category) if category else 0
        except:
            raise Http404

        if tag:  # 点击tag或者category来给主页分类。
            posts = filter_posts_by_tag(tag)
        elif category:
            posts = filter_posts_by_category(category)
        else:
            posts = models.Post.objects.all()  # 所有博文
        posts = posts.filter(is_draft=False).order_by('-id')  # 过滤，
        if keywords:
            posts = posts.filter(Q(title__contains=keywords) | Q(raw__contains=keywords))
            # Q可以对关键字参数进行封装，从而更好地应用多个查询。可与关键字参数查询一起用，不过要把Q对象放在关键字参数查询的前面。
            data['keywords'] = keywords
        post_pages = models.Page.objects.filter(is_draft=False)

        paginator = Paginator(posts, PER_PAGE)  # 分页功能

        page = request.GET.get('page')
        try:
            posts = paginator.page(page)  # 获取某页对应的记录
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            posts = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            posts = paginator.page(paginator.num_pages)  # 最后一页

        tags = models.Tag.objects.all()
        catagories = models.Category.objects.annotate(num_posts=Count('post'))  # 博客分类计数
        # 如果你正在操作一个Blog列表，你可能想知道每个Blog有多少Entry

        data['posts'] = posts
        data['pages'] = post_pages
        data['tags'] = tags
        data['catagories'] = catagories
        data['category_id'] = category
        data['tag_id'] = tag

        data['seo'] = get_site_meta()

        return render(request, self.template_name, data)  # 送到HTML中进行渲染


class Post(View):
    template_name = 'main/post.html'

    def get(self, request, pk):
        try:
            pk = int(pk)
            post = models.Post.objects.get(pk=pk)  # 获取博文内容
        except models.Post.DoesNotExist:
            raise Http404
        data = {'post': post}
        tags = post.tags.all()
        data['tags'] = tags

        comment_type = settings.MY_SITE['COMMENT_TYPE']
        comment_type_id = settings.MY_SITE['COMMENT_OPT'].get(comment_type)

        if not comment_type_id:
            comment_script = 'no comment script for {0}'.format(comment_type)
        else:
            comment_func = misc.get_comment_func(comment_type)
            # url_partial = [request.META['SERVER_NAME'], ':', request.META['SERVER_PORT'], request.path]
            # post_url = ''.join(url_partial)
            post_url = request.build_absolute_uri()
            comment_script = comment_func(request, comment_type_id, post.id, post.title, post_url)

        data['comment_script'] = comment_script

        data['jiathis_share'] = misc.jiathis_share(request)

        # data['allow_donate'] = settings.MY_SITE['ALLOW_DONATE']

        seo = {
            'title': post.title,
            'desc': post.abstract,
            'author': post.author.username,
            'keywords': ', '.join([tag.name for tag in tags])
        }

        data['seo'] = seo

        post_pages = models.Page.objects.filter(is_draft=False)
        data['pages'] = post_pages

        return render(request, self.template_name, data)


class Page(View):
    template_name = 'main/page.html'

    def get(self, request, pk):
        try:
            pk = int(pk)
            page = models.Page.objects.get(pk=pk)
        except models.Page.DoesNotExist:
            raise Http404
        data = {'page': page}
        data['seo'] = get_site_meta()

        post_pages = models.Page.objects.filter(is_draft=False)
        data['pages'] = post_pages

        return render(request, self.template_name, data)


class Archive(View):  # 归档
    template_name = 'main/archive.html'

    def get(self, request):
        data = {}
        data['seo'] = get_site_meta()

        posts = models.Post.objects.filter(is_draft=False)
        paginator = Paginator(posts, PER_PAGE)

        page = request.GET.get('page')
        try:
            posts = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            posts = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            posts = paginator.page(paginator.num_pages)

        data['posts'] = posts

        post_pages = models.Page.objects.filter(is_draft=False)
        data['pages'] = post_pages

        return render(request, self.template_name, data)


class Author(View):
    template_name = 'main/author.html'

    def get(self, request, pk):
        data = {}
        data['seo'] = get_site_meta()
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise Http404
        data['user'] = user
        data['account_info'] = user.account

        posts = models.Post.objects.filter(is_draft=False, author=user)
        paginator = Paginator(posts, PER_PAGE)

        page = request.GET.get('page')
        try:
            posts = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            posts = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            posts = paginator.page(paginator.num_pages)

        data['posts'] = posts

        return render(request, self.template_name, data)


class AdminIndex(View):
    template_name = 'blog_admin/index.html'

    @method_decorator(login_required)
    def get(self, request):
        data = {'site_info': get_site_meta(), 'account_info': get_user_info(request.user)}
        return render(request, self.template_name, data)


class AdminBlogMeta(View):
    template_name = 'main/simple_form.html'

    @method_decorator(permission_required('main.add_blogmeta', accept_global_perms=True))
    def get(self, request, form=None):
        if not form:
            form = forms.BlogMetaForm(initial=get_site_meta())

        data = {'form': form}
        return render(request, self.template_name, data)

    @method_decorator(permission_required('main.add_blogmeta', accept_global_perms=True))
    def post(self, request):
        form = forms.BlogMetaForm(request.POST)
        if form.is_valid():
            record = models.BlogMeta.objects.get(key='blog_name')
            record.value = form.cleaned_data['title']
            record.save()

            record = models.BlogMeta.objects.get(key='blog_desc')
            record.value = form.cleaned_data['desc']
            record.save()

            record = models.BlogMeta.objects.get(key='owner')
            record.value = form.cleaned_data['author']
            record.save()

            record = models.BlogMeta.objects.get(key='keywords')
            record.value = form.cleaned_data['keywords']
            record.save()

            record = models.BlogMeta.objects.get(key='blog_subtitle')
            record.value = form.cleaned_data['subtitle']
            record.save()

            record = models.BlogMeta.objects.get(key='google_verify')
            record.value = form.cleaned_data['google_verify']
            record.save()

            record = models.BlogMeta.objects.get(key='baidu_verify')
            record.value = form.cleaned_data['baidu_verify']
            record.save()

            msg = 'Succeed to update blog meta'
            messages.add_message(request, messages.SUCCESS, msg)
            url = reverse('main:admin_index')

            return redirect(url)

        return self.get(request, form)


# 处理表单


class AdminPosts(View):
    template_name_posts = 'blog_admin/posts.html'
    template_name_pages = 'blog_admin/pages.html'

    @method_decorator(permission_required('main.add_post', accept_global_perms=True))
    def get(self, request, is_blog_page=False):
        data = {}
        draft = request.GET.get('draft')
        if draft and draft.lower() == 'true':
            flag = True
        else:
            flag = False
        if is_blog_page:
            if not request.user.has_perm('main.change_page'):
                return HttpResponseForbidden()
            posts = models.Page.objects.all()
            template_name = self.template_name_pages
        else:
            posts = models.Post.objects.all()
            if not request.user.has_perm('main.change_post'):
                posts = posts.filter(author=request.user)
            template_name = self.template_name_posts

        posts = posts.filter(is_draft=flag)
        key = request.GET.get('key')
        if key:
            posts = posts.filter(Q(title__icontains=key) | Q(raw__icontains=key))
        posts = posts.order_by('-update_time')

        paginator = Paginator(posts, PER_PAGE_ADMIN)
        page = request.GET.get('page')
        try:
            posts = paginator.page(page)
        except PageNotAnInteger:
            posts = paginator.page(1)
        except EmptyPage:
            posts = paginator.page(paginator.num_pages)

        data['posts'] = posts
        data['is_blog_page'] = is_blog_page
        data['allow_search'] = True

        return render(request, template_name, data)


class AdminPost(View):  # 博文只能通过后台的 admin/posts/n 来修改
    template_name = 'blog_admin/post.html'

    # @method_decorator(login_required)
    # 添加博文 是通过get
    @method_decorator(permission_required('main.add_post', accept_global_perms=True))
    def get(self, request, pk=0, form=None):
        data = {}
        form_data = {}
        if pk:
            try:
                pk = int(pk)
                post = models.Post.objects.get(pk=pk)

                #############################
                # It works!
                #############################
                # if not 'change_post' in get_perms(request.user, post):
                #     raise HttpResponseForbidden()

                #############################
                # It works, too!
                #############################
                checker = ObjectPermissionChecker(request.user)
                if not request.user.has_perm('main.change_post') \
                        and not checker.has_perm('change_post', post):
                    return HttpResponse('Forbidden')

                form_data['title'] = post.title
                form_data['content'] = post.raw
                form_data['abstract'] = post.abstract
                form_data['author_id'] = post.author.id
                data['edit_flag'] = True
            except models.Post.DoesNotExist:
                raise Http404
        else:
            post = None
        if not form:
            form = forms.NewPost(initial=form_data)
        data['form'] = form
        data['posted_tags'] = [tag for tag in post.tags.all()] if post else None
        data['posted_category'] = post.category if post else None
        tags = models.Tag.objects.all()
        data['tags'] = tags
        catagories = models.Category.objects.all()
        data['catagories'] = catagories
        data['pk'] = pk
        return render(request, self.template_name, data)

    @method_decorator(permission_required('main.add_post', accept_global_perms=True))
    def post(self, request, pk=0, form=None):
        form = forms.NewPost(request.POST)
        if form.is_valid():
            if not pk:
                cur_post = models.Post()
            else:
                try:
                    pk = int(pk)
                    cur_post = models.Post.objects.get(pk=pk)
                    checker = ObjectPermissionChecker(request.user)
                    if not checker.has_perm('change_post', cur_post) \
                            and not request.user.has_perm('main.change_post'):
                        return HttpResponseForbidden('forbidden1')
                except models.Post.DoesNotExist:
                    raise Http404
            cur_post.title = form.cleaned_data['title']
            cur_post.raw = form.cleaned_data['content']
            cur_post.abstract = form.cleaned_data['abstract']
            if not cur_post.abstract:
                cur_post.abstract = cur_post.raw[0:140]
            # html = markdown2.markdown(cur_post.raw, extras=['code-friendly', 'fenced-code-blocks'])
            # cur_post.content_html = smart_text(html)
            cur_post.author = User.objects.get(pk=form.cleaned_data['author_id']) if form.cleaned_data[
                'author_id'] else request.user
            # cur_post.author = request.user
            tag_ids = request.POST.getlist('tags')
            category_id = request.POST.get('category', None)
            # return HttpResponse(len(tag_ids))
            if request.POST.get('publish'):
                cur_post.is_draft = False

                msg = 'Post has been pulished!'
                messages.add_message(request, messages.SUCCESS, msg)
                url = reverse('main:admin_posts')

            else:
                cur_post.is_draft = True
                if request.POST.get('preview'):
                    cur_post.save()
                    return HttpResponse(cur_post.id)

                msg = 'Draft has been saved!'
                messages.add_message(request, messages.SUCCESS, msg)
                url = '{0}?draft=true'.format(reverse('main:admin_posts'))

            cur_post.category_id = category_id
            cur_post.save()
            cur_post.tags.clear()
            cur_post.tags.add(*tag_ids)

            assign_perm('main.change_post', request.user, cur_post)  # 当前用户具有这篇博文的更改和删除权限
            assign_perm('main.delete_post', request.user, cur_post)

            if request.POST.get('preview'):
                url = reverse('main:post', kwargs={'pk': cur_post.id})
            return redirect(url)

        return self.get(request, form)  # 表单 is not valid


class AdminPage(View):
    template_name = 'blog_admin/page.html'

    @method_decorator(permission_required('main.add_page', accept_global_perms=True))
    def get(self, request, pk=0, form=None):
        data = {}
        form_data = {}
        if pk:
            try:
                pk = int(pk)
                page = models.Page.objects.get(pk=pk)
                form_data['title'] = page.title
                form_data['content'] = page.raw
                form_data['slug'] = page.slug
                form_data['author_id'] = page.author.id
                data['edit_flag'] = True
            except models.Post.DoesNotExist:
                raise Http404
        else:
            page = None
        if not form:
            form = forms.NewPage(initial=form_data)
        data['form'] = form

        return render(request, self.template_name, data)

    @method_decorator(permission_required('main.add_page', accept_global_perms=True))
    def post(self, request, pk=0, form=None):
        form = forms.NewPage(request.POST)
        if form.is_valid():
            if not pk:
                cur_post = models.Page()
            else:
                try:
                    pk = int(pk)
                    cur_post = models.Page.objects.get(pk=pk)
                except models.Page.DoesNotExist:
                    raise Http404
            cur_post.title = form.cleaned_data['title']
            cur_post.raw = form.cleaned_data['content']
            cur_post.slug = form.cleaned_data['slug']
            # html = markdown2.markdown(cur_post.raw, extras=['code-friendly', 'fenced-code-blocks'])
            # cur_post.content_html = smart_text(html)
            # cur_post.author = request.user
            cur_post.author = User.objects.get(pk=form.cleaned_data['author_id']) if form.cleaned_data[
                'author_id'] else request.user

            if request.POST.get('publish'):
                cur_post.is_draft = False

                msg = 'Page has been pulished!'
                messages.add_message(request, messages.SUCCESS, msg)
                url = reverse('main:admin_pages')

            else:
                cur_post.is_draft = True

                msg = 'Draft has been saved!'
                messages.add_message(request, messages.SUCCESS, msg)
                url = '{0}?draft=true'.format(reverse('main:admin_pages'))

            cur_post.save()

            return redirect(url)

        return self.get(request, form)


class DeletePost(View):
    @method_decorator(permission_required('main.delete_post', (models.Post, 'id', 'pk'), accept_global_perms=True))
    def get(self, request, pk):
        try:
            pk = int(pk)
            cur_post = models.Post.objects.get(pk=pk)
            is_draft = cur_post.is_draft

            # checker = ObjectPermissionChecker(request.user)
            # if not request.user.has_perm('main.delete_post') \
            #     and not checker.has_perm('delete_post', cur_post):
            #     return HttpResponse('forbidden')

            url = reverse('main:admin_posts')  # 这个就等于 ^main/admin/posts
            if is_draft:
                url = '{0}?draft=true'.format(url)
            cur_post.delete()
        except models.Post.DoesNotExist:
            raise Http404

        return redirect(url)


class DeletePage(View):
    @method_decorator(permission_required('main.delete_page', accept_global_perms=True))
    def get(self, request, pk):
        try:
            pk = int(pk)
            cur_post = models.Page.objects.get(pk=pk)
            is_draft = cur_post.is_draft

            checker = ObjectPermissionChecker(request.user)
            if not checker.has_perm('delete_page', cur_post):
                # return HttpResponseForbidden('forbidden')
                return HttpResponse('forbidden')

            url = reverse('main:admin_pages')
            if is_draft:
                url = '{0}?draft=true'.format(url)
            cur_post.delete()
        except models.Page.DoesNotExist:
            raise Http404

        return redirect(url)


class AdminTags(View):
    template_name = 'blog_admin/tags.html'

    @method_decorator(permission_required('main.add_tag', accept_global_perms=True))
    def get(self, request, form=None):
        if not form:
            form = forms.TagForm()
        tags = models.Tag.objects.all()

        paginator = Paginator(tags, PER_PAGE_ADMIN)
        page = request.GET.get('page')

        try:
            tags = paginator.page(page)

        except PageNotAnInteger:
            tags = paginator.page(1)
        except EmptyPage:
            tags = paginator.page(paginator.num_pages)

        data = {'tags': tags, 'form': form}

        return render(request, self.template_name, data)

    @method_decorator(permission_required('main.add_tag', accept_global_perms=True))
    def post(self, request, form=None):
        form = forms.TagForm(request.POST)
        if form.is_valid():
            tags = form.cleaned_data['tags'].split(',')
            for tag in tags:
                tag_model, created = models.Tag.objects.get_or_create(name=tag.strip())

            msg = 'Succeed to create tags'
            messages.add_message(request, messages.SUCCESS, msg)
            url = reverse('main:admin_tags')
            return redirect(url)
        else:
            return self.get(request, form=form)


class AdminCategory(View):
    template_name = 'blog_admin/category.html'

    @method_decorator(permission_required('main.add_category', accept_global_perms=True))
    def get(self, request, form=None):
        if not form:
            form = forms.CategoryForm()
        catagories = models.Category.objects.all()
        paginator = Paginator(catagories, PER_PAGE_ADMIN)
        page = request.GET.get('page')
        try:
            catagories = paginator.page(page)
        except PageNotAnInteger:
            catagories = paginator.page(1)
        except EmptyPage:
            catagories = paginator.page(paginator.num_pages)

        data = {'catagories': catagories, 'form': form}

        return render(request, self.template_name, data)

    @method_decorator(permission_required('main.add_category', accept_global_perms=True))
    def post(self, request, form=None):
        form = forms.CategoryForm(request.POST)
        if form.is_valid():
            category = models.Category()
            category.name = form.cleaned_data['name']
            category.save()

            msg = 'Succeed to create new category'
            messages.add_message(request, messages.SUCCESS, msg)
            url = reverse('main:admin_category')
            return redirect(url)
        else:
            return self.get(request, form=form)


class AdminFilterPosts(View):
    template_name = 'blog_admin/posts.html'

    @method_decorator(permission_required('main.add_post', accept_global_perms=True))
    def get(self, request):
        tag_id = request.GET.get('tag')
        category_id = request.GET.get('category')

        if tag_id:
            posts = filter_posts_by_tag(tag_id)
        elif category_id:
            posts = filter_posts_by_category(category_id)
        else:
            url = reverse('main:admin_posts')
            return redirect(url)

        if posts == None:
            raise Http404

        paginator = Paginator(posts, PER_PAGE_ADMIN)
        page = request.GET.get('page')
        try:
            posts = paginator.page(page)
        except PageNotAnInteger:
            posts = paginator.page(1)
        except EmptyPage:
            posts = paginator.page(paginator.num_pages)

        data = {'posts': posts}
        return render(request, self.template_name, data)


def filter_posts_by_tag(pk):
    try:
        tag = models.Tag.objects.get(pk=pk)
    except models.Tag.DoesNotExist:
        return None

    posts = tag.post_set.all()
    return posts


def filter_posts_by_category(pk):
    try:
        category = models.Category.objects.get(pk=pk)
    except models.Category.DoesNotExist:
        return None

    posts = category.post_set.all()  # 所有跟当前category 对应的博客进行返回
    return posts


# In permission system, if you can change tags,
# you can also change categories


@permission_required('main.change_tag', accept_global_perms=True)
def simple_update(request, pk, flag=None):
    # flag = request.GET.get('flag', '')
    if not flag:
        raise Http404

    if flag.lower() == 'tag':
        model = models.Tag
    elif flag.lower() == 'category':
        model = models.Category
    else:
        return HttpResponse(flag)

        # raise Http404

    name = request.GET.get('name', '')
    if not name:
        return HttpResponse('Please post the correct name')

    record = model.objects.get(pk=pk)
    record.name = name
    record.save()

    return HttpResponse('Succeed to update {0}'.format(flag))


# In permission system, if you can delete tags,
# you can also delete categories


@permission_required('main.delete_tag', accept_global_perms=True)
def simple_delete(request, pk, flag=None):
    # flag = request.GET.get('flag', '')
    if not flag:
        raise Http404

    if flag.lower() == 'tag':
        model = models.Tag
    elif flag.lower() == 'category':
        model = models.Category
    else:
        raise Http404

    record = model.objects.get(pk=pk)
    record.delete()

    return HttpResponse('Succeed to delete {0}'.format(flag))

