import logging
from django.views import generic
from .models import Post
from rest_framework import viewsets
from .serializers import PostSerializer
from .models import Post
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from .forms import NewUserForm

logger = logging.getLogger(__name__)


class PostList(generic.ListView):
    queryset = Post.objects.filter(status=1).order_by('-created_on')
    template_name = 'index.html'
    context_object_name = 'post_list'
    
    def get_queryset(self):
        logger.info("PostList: Fetching blog posts from database")
        logger.debug(f"Filtering posts with status=1, ordered by created_on")
        return super().get_queryset()


class PostDetail(generic.DetailView):
    model = Post
    template_name = 'post_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.get_object()
        logger.info(f"PostDetail: Viewing post with slug: {post.slug}")
        context['comments'] = post.comments.all()
        logger.debug(f"Found {post.comments.count()} comments for this post")
        return context
    
    def post(self, request, *args, **kwargs):
        post = self.get_object()
        comment_text = request.POST.get('comment_text')
        if comment_text and request.user.is_authenticated:
            from .models import Comment
            Comment.objects.create(
                post=post,
                author=request.user,
                text=comment_text
            )
            logger.warning(f"New comment added to post '{post.title}' by user {request.user.username}")
            logger.info(f"Comment content: {comment_text[:50]}...")
        else:
            logger.warning(f"Failed comment attempt on post '{post.title}' - User authenticated: {request.user.is_authenticated}")
        return redirect('post_detail', slug=post.slug)


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    
    def perform_create(self, serializer):
        logger.info(f"API: New post created via REST API")
        serializer.save()


def register_request(request):
    if request.method == "POST":
        form = NewUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful.")
            logger.info(f"New user registered: {user.username} (email: {user.email})")
            return redirect("home")
        messages.error(request, "Unsuccessful registration. Invalid information.")
        logger.warning(f"Failed registration attempt - Form errors: {form.errors}")
    form = NewUserForm()
    return render(request, "register.html", {"register_form": form})


def login_request(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"You are now logged in as {username}.")
                logger.info(f"Successful login: {username}")
                return redirect("home")
            else:
                messages.error(request, "Invalid username or password.")
                logger.warning(f"Failed login attempt for username: {username}")
        else:
            messages.error(request, "Invalid username or password.")
            logger.warning(f"Login form invalid - errors: {form.errors}")
    form = AuthenticationForm()
    return render(request, "login.html", {"login_form": form})


def logout_request(request):
    username = request.user.username if request.user.is_authenticated else "Unknown"
    logout(request)
    messages.info(request, "You have successfully logged out.")
    logger.info(f"User logged out: {username}")
    return redirect("home")