from rest_framework import serializers


class UploadFileSerializer(serializers.Serializer):
    file = serializers.FileField()
    topic = serializers.CharField()
    permission_tags = serializers.CharField()

class MessageSerializer(serializers.Serializer):
    message = serializers.CharField()