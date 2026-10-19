from django.conf import settings
from django.db import models, transaction


class Project(models.Model):
    key = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='owned_projects')
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='projects', blank=True)
    issue_counter = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.key}: {self.name}'

    def next_issue_number(self):
        with transaction.atomic():
            project = Project.objects.select_for_update().get(pk=self.pk)
            project.issue_counter += 1
            project.save(update_fields=['issue_counter'])
            return project.issue_counter


class Issue(models.Model):
    class Type(models.TextChoices):
        TASK = 'task', 'Task'
        BUG = 'bug', 'Bug'
        STORY = 'story', 'Story'

    class Status(models.TextChoices):
        TODO = 'todo', 'To Do'
        IN_PROGRESS = 'in_progress', 'In Progress'
        DONE = 'done', 'Done'

    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'

    # Allowed workflow transitions.
    TRANSITIONS = {
        Status.TODO: {Status.IN_PROGRESS},
        Status.IN_PROGRESS: {Status.TODO, Status.DONE},
        Status.DONE: {Status.IN_PROGRESS},
    }

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='issues')
    number = models.PositiveIntegerField(editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=10, choices=Type.choices, default=Type.TASK)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.TODO)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    labels = models.CharField(max_length=200, blank=True, help_text='Comma-separated')
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='reported_issues')
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='assigned_issues')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('project', 'number')]
        ordering = ['-created_at']

    @property
    def key(self):
        return f'{self.project.key}-{self.number}'

    def __str__(self):
        return f'{self.key} {self.title}'

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = self.project.next_issue_number()
        super().save(*args, **kwargs)


class Comment(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']


class Activity(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='activity')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    field = models.CharField(max_length=30)
    old_value = models.CharField(max_length=200, blank=True)
    new_value = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'id']
