import json
import re
import os
from datetime import datetime
from io import BytesIO
from wsgiref.util import FileWrapper
from django.core.cache import cache
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse, StreamingHttpResponse
from django.template import RequestContext
from django.shortcuts import *
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, permissions, status
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.decorators import authentication_classes, permission_classes, api_view
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from django.http import FileResponse
from cloud.forms import DocumentForm
from cloud.models import Document
from cloud.serializers import FileSerializer
from django.views.decorators.cache import cache_page
from django.conf import settings
from django.core.cache.backends.base import DEFAULT_TIMEOUT
import uuid

CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)


class RangeFileWrapper(object):
    def __init__(self, filelike, blksize=8192, offset=0, length=None):
        self.filelike = filelike
        self.filelike.seek(offset, os.SEEK_SET)
        self.remaining = length
        self.blksize = blksize

    def close(self):
        if hasattr(self.filelike, 'close'):
            self.filelike.close()

    def __iter__(self):
        return self

    def __next__(self):
        if self.remaining is None:
            # If remaining is None, we're reading the entire file.
            data = self.filelike.read(self.blksize)
            if data:
                return data
            raise StopIteration()
        else:
            if self.remaining <= 0:
                raise StopIteration()
            data = self.filelike.read(min(self.remaining, self.blksize))
            if not data:
                raise StopIteration()
            self.remaining -= len(data)
            return data


# @cache_page(CACHE_TTL)
@login_required(login_url='/account/login/')
def index(request):
    # Handle file upload
    if request.method == 'POST':
        cache.set('aaa', 5)
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            user = request.user
            newdoc = Document(file=request.FILES['file'])
            newdoc.size = request.FILES['file'].size
            if user.profile.Upload + newdoc.size / 1073741824.0 > user.profile.Total_storage:
                return render(request,
                              'cloud/main.html', {'error': "you Do not have enough space on cloud"})
            newdoc.User = request.user
            newdoc.name = form.cleaned_data.get('file')
            newdoc.Status = newdoc.private
            newdoc.uniq_Id = uuid.uuid4()
            newdoc.save()
            user.profile.Upload += newdoc.size / 1073741824.0
            user.save()
            return HttpResponseRedirect(reverse('cloud:index'))
    else:
        form = DocumentForm()  # A empty, unbound form

    documents = Document.objects.filter(User_id__exact=request.user.id)
    return render(
        request,
        'cloud/main.html',
        {'documents': documents, 'form': form, 'user': request.user},
    )


# login_required
@api_view(['GET', 'POST'])
# @authentication_classes([SessionAuthentication, BasicAuthentication])
# @permission_classes([IsAuthenticated])
def download_file(request, uniqid):
    downloadable = False
    uniqid = str.replace(uniqid, '-', '')
    file = Document.objects.get(uniq_Id__exact=uniqid)
    if file.Status is file.private:
        if file.User == request.user:
            downloadable = True
    elif file.Status is file.public:
        downloadable = True

    if downloadable:
        range_header = request.META.get('HTTP_RANGE')
        if not (range_header and range_header.startswith('bytes=') and range_header.count('-') == 1):
            file.download_count = file.download_count + 1
            file.last_download = datetime.now()
            fl_path = str(file.file)
            filename = file.name
            if file.uniq_Id in cache:
                filecontent = cache.get(file.uniq_Id)
                response = FileResponse(filecontent)
            else:
                # response = FileResponse(open(fl_path, 'rb'))
                # myio = BytesIO()
                with open(fl_path, 'rb') as downfile:
                    buf = BytesIO(downfile.read())
                    response = FileResponse(downfile)
                    cache.set(str(file.uniq_Id), buf, timeout=CACHE_TTL)
            response['Content-Disposition'] = "attachment; filename=%s" % filename
            user = request.user
            if not request.user.is_anonymous:
                user.profile.Download += file.size / 1073741824.0
                user.save()
            file.save()
            return response
        else:
            range_re = re.compile(r'bytes\s*=\s*(\d+)\s*-\s*(\d*)', re.I)
            range_match = range_re.match(range_header)
            size = file.size
            # content_type, encoding = mimetypes.guess_type(file.file)
            # content_type = 'application/octet-stream'
            content_type = 'application/pdf'
            fl_path = str(file.file)
            if range_match:
                first_byte, last_byte = range_match.groups()
                first_byte = int(first_byte) if first_byte else 0
                last_byte = int(last_byte) if last_byte else size - 1
                if last_byte >= size:
                    last_byte = size - 1
                length = last_byte - first_byte + 1
                resp = StreamingHttpResponse(RangeFileWrapper(open(fl_path, 'rb'), offset=first_byte, length=length),
                                             status=206, content_type=content_type)
                resp['Content-Length'] = str(length)
                resp['Content-Range'] = 'bytes %s-%s/%s' % (first_byte, last_byte, size)
                resp['Content-Disposition'] = "attachment; filename=%s" % file.name
            else:
                resp = StreamingHttpResponse(FileWrapper(open(fl_path, 'rb')), content_type=content_type)
                resp['Content-Length'] = str(size)
            resp['Accept-Ranges'] = 'bytes'
            return resp
    else:
        raise PermissionDenied()


# @login_required
@csrf_exempt
@api_view(['GET', 'POST'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def api_file_list(request):
    if request.method == 'GET':
        doscs = Document.objects.filter(User_id__exact=request.user.id)
        serializer = FileSerializer(doscs, many=True)
        return JsonResponse(serializer.data, safe=False)

    elif request.method == 'POST':
        data = JSONParser().parse(request)
        serializer = FileSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)


# @csrf_exempt
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
@api_view(['DELETE'])
def file_delete(request):
    if request.method == 'DELETE':
        try:
            data = json.loads(request.body.decode('UTF-8'))
            uniq_id = data['uniq_Id']
            uniq_id = str.replace(uniq_id, '-', '')
            delete_able = False
            file = Document.objects.get(uniq_Id__exact=uniq_id)
            if file.User == request.user:
                delete_able = True
            else:
                return JsonResponse("You are not file owner", status=200, safe=False)
            if delete_able:
                file.delete()

            return JsonResponse("Delete file was successful", status=200, safe=False)
        except Exception as e:
            print()
            return JsonResponse("Something went wrong when deleting file", status=200, safe=False)


@csrf_exempt
@api_view(['GET', 'POST'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
# @login_required
def api_file_upload(request):
    """
    List all code snippets, or create a new snippet.
    """
    if request.method == 'GET':
        docs = Document.objects.filter(User_id__exact=request.user.id)
        serializer = FileSerializer(docs, many=True)
        return JsonResponse(serializer.data, safe=False)

    elif request.method == 'POST':
        data = JSONParser().parse(request)
        serializer = FileSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)


@csrf_exempt
# @api_view(['GET', 'POST', 'DELETE'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def file_status(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('UTF-8'))
            uniq_id = data['uniq_Id']
            uniq_id = str.replace(uniq_id, '-', '')
            file = Document.objects.get(uniq_Id__exact=uniq_id)
            if file.User == request.user:
                if file.Status == 1:
                    file.Status = 0
                else:
                    file.Status = 1

                file.save()
                return JsonResponse("file Status changed", status=200, safe=False)
        except:
            return JsonResponse("Something went wrong when change file status", status=200, safe=False)
