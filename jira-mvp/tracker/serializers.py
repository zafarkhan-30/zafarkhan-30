from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Activity, Comment, Issue, Project

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['id', 'username', 'password']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class ProjectSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    members = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'key', 'name', 'description', 'owner', 'members', 'created_at']

    def validate_key(self, value):
        value = value.upper()
        if not value.isalpha():
            raise serializers.ValidationError('Key must contain letters only.')
        if self.instance and self.instance.key != value:
            raise serializers.ValidationError('Project key cannot be changed.')
        return value


class IssueSerializer(serializers.ModelSerializer):
    key = serializers.CharField(read_only=True)
    reporter = UserSerializer(read_only=True)
    assignee_id = serializers.PrimaryKeyRelatedField(
        source='assignee', queryset=User.objects.all(), allow_null=True, required=False)
    assignee = UserSerializer(read_only=True)

    class Meta:
        model = Issue
        fields = ['id', 'key', 'project', 'number', 'title', 'description', 'type', 'status',
                  'priority', 'labels', 'reporter', 'assignee', 'assignee_id',
                  'created_at', 'updated_at']
        read_only_fields = ['number', 'project']

    def validate_assignee_id(self, value):
        return value

    def validate(self, attrs):
        project = self.context['project']
        assignee = attrs.get('assignee')
        if assignee and not project.members.filter(pk=assignee.pk).exists():
            raise serializers.ValidationError({'assignee_id': 'Assignee must be a project member.'})
        new_status = attrs.get('status')
        if self.instance and new_status and new_status != self.instance.status:
            allowed = Issue.TRANSITIONS[Issue.Status(self.instance.status)]
            if Issue.Status(new_status) not in allowed:
                raise serializers.ValidationError(
                    {'status': f'Cannot move from {self.instance.status} to {new_status}.'})
        return attrs


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'author', 'body', 'created_at']


class ActivitySerializer(serializers.ModelSerializer):
    actor = UserSerializer(read_only=True)

    class Meta:
        model = Activity
        fields = ['id', 'actor', 'field', 'old_value', 'new_value', 'created_at']
