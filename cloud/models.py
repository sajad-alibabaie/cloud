from django.db import models
from django.contrib.auth.models import User
import uuid
import os


def get_file_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (uuid.uuid4(), ext)
    return os.path.join('documents/upload', filename)


class Document(models.Model):
    User = models.ForeignKey(User, on_delete=models.PROTECT)
    file = models.FileField(upload_to=get_file_path)
    name = models.CharField("name", max_length=50)
    uniq_Id = models.UUIDField(uuid.uuid4())
    upload_time = models.DateTimeField('Upload Date', auto_now_add=True)
    last_download = models.DateTimeField('Last Download', null=True)
    download_count = models.BigIntegerField('Download Count', default=0)
    public = 0
    private = 1
    status_choices = (
        (public, 'public file'),
        (private, 'private file'),
    )
    Status = models.IntegerField('وضعیت', choices=status_choices)
    size = models.FloatField('size', null=True)

    def __str__(self):
        return self.name
