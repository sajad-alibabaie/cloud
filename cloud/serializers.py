from cloud.models import Document
from rest_framework import serializers


class FileSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Document
        fields = ['uniq_Id', 'name', 'Status', 'upload_time', 'last_download', 'download_count', 'size']
