from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response

from .models import Activity, Comment, Issue, Project
from .serializers import (ActivitySerializer, CommentSerializer, IssueSerializer,
                          ProjectSerializer, RegisterSerializer, UserSerializer)

User = get_user_model()
TRACKED_FIELDS = ['title', 'description', 'type', 'status', 'priority', 'labels', 'assignee']


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        token, _ = Token.objects.get_or_create(user_id=response.data['id'])
        response.data = {'id': response.data['id'], 'username': response.data['username'], 'token': token.key}
        return response


class LoginView(ObtainAuthToken):
    authentication_classes = []


class UserListView(generics.ListAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.order_by('username')


class ProjectListCreateView(generics.ListCreateAPIView):
    serializer_class = ProjectSerializer

    def get_queryset(self):
        return Project.objects.filter(members=self.request.user).order_by('key')

    def perform_create(self, serializer):
        project = serializer.save(owner=self.request.user)
        project.members.add(self.request.user)


class ProjectMixin:
    """Resolve the project from the URL and enforce membership (404 for non-members)."""

    def get_project(self):
        if not hasattr(self, '_project'):
            self._project = get_object_or_404(
                Project, key=self.kwargs['key'].upper(), members=self.request.user)
        return self._project

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        if getattr(self, 'swagger_fake_view', False):
            return ctx
        ctx['project'] = self.get_project()
        return ctx


class ProjectDetailView(ProjectMixin, generics.RetrieveUpdateAPIView):
    serializer_class = ProjectSerializer

    def get_object(self):
        project = self.get_project()
        if self.request.method not in permissions.SAFE_METHODS and project.owner_id != self.request.user.id:
            self.permission_denied(self.request, message='Only the owner can edit the project.')
        return project


class MemberView(ProjectMixin, generics.GenericAPIView):
    serializer_class = ProjectSerializer

    def post(self, request, key):
        project = self.get_project()
        if project.owner_id != request.user.id:
            self.permission_denied(request, message='Only the owner can add members.')
        user = get_object_or_404(User, username=request.data.get('username'))
        project.members.add(user)
        return Response(ProjectSerializer(project).data, status=status.HTTP_201_CREATED)


class IssueListCreateView(ProjectMixin, generics.ListCreateAPIView):
    serializer_class = IssueSerializer

    def get_queryset(self):
        qs = (Issue.objects.filter(project=self.get_project())
              .select_related('project', 'reporter', 'assignee'))
        p = self.request.query_params
        for param in ('status', 'type', 'priority'):
            if p.get(param):
                qs = qs.filter(**{param: p[param]})
        if p.get('assignee'):
            qs = qs.filter(assignee__username=p['assignee'])
        if p.get('q'):
            qs = qs.filter(Q(title__icontains=p['q']) | Q(description__icontains=p['q']))
        return qs

    def perform_create(self, serializer):
        serializer.save(project=self.get_project(), reporter=self.request.user)


class IssueDetailView(ProjectMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = IssueSerializer

    def get_object(self):
        return get_object_or_404(
            Issue.objects.select_related('project', 'reporter', 'assignee'),
            project=self.get_project(), number=self.kwargs['number'])

    def perform_update(self, serializer):
        before = {f: str(getattr(serializer.instance, f) or '') for f in TRACKED_FIELDS}
        issue = serializer.save()
        for f in TRACKED_FIELDS:
            after = str(getattr(issue, f) or '')
            if before[f] != after:
                Activity.objects.create(issue=issue, actor=self.request.user, field=f,
                                        old_value=before[f][:200], new_value=after[:200])


class CommentListCreateView(ProjectMixin, generics.ListCreateAPIView):
    serializer_class = CommentSerializer

    def get_issue(self):
        return get_object_or_404(Issue, project=self.get_project(), number=self.kwargs['number'])

    def get_queryset(self):
        return Comment.objects.filter(issue=self.get_issue()).select_related('author')

    def perform_create(self, serializer):
        serializer.save(issue=self.get_issue(), author=self.request.user)


class ActivityListView(ProjectMixin, generics.ListAPIView):
    serializer_class = ActivitySerializer

    def get_queryset(self):
        issue = get_object_or_404(Issue, project=self.get_project(), number=self.kwargs['number'])
        return Activity.objects.filter(issue=issue).select_related('actor')
