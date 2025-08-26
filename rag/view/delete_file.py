from knowledge_system.errors import KMsystemError, KMsystemException
from drf_spectacular.utils import extend_schema
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view, parser_classes
from knowledge_system.utils.decorator import try_catch_decorator
from knowledge_system.responses import KMsystemResponse
from knowledge_system.settings import COLLECTION, MEDIA_ROOT
from knowledge_system.connections import Connection
from rag.serializers import (
    MessageSerializer,
    DeleteFileSerializer)
from rag.models import PdfTopicMap
from qdrant_client.models import Filter, FieldCondition, MatchValue
from uuid import UUID
import os


"""
step: 
1. 根據檔案名找尋所屬的collections
2. 到qdrant把向量刪除
3. 刪掉系統上的檔案
4. 更新collection_map
"""
@extend_schema(
    request=DeleteFileSerializer,              # 告訴 Swagger 這是 multipart 的欄位
    responses={200: MessageSerializer},        # 回傳結構
    summary="刪除 PDF",
    description="以 multipart/form-data 上傳檔案，並指定 collection 與 permission_tags"
)
@api_view(['DELETE'])
@parser_classes([MultiPartParser, FormParser])
@try_catch_decorator
def delete_file(request):
    s = DeleteFileSerializer(data = request.data)
    try:
        s.is_valid(raise_exception=True)
        document_id = str(UUID(s.validated_data['document_id']))
    except Exception as e:
        raise KMsystemException(KMsystemError.INVALID_PARAMETER, e)
    filename, topic = _delete_from_qdrant(document_id)
    _file_delete(filename, document_id, topic)
    
    return KMsystemResponse.to_json_response('檔案成功刪除')

def _delete_from_qdrant(document_id):
    delete_filter = Filter(
        must=[
            FieldCondition(key="document_id", match=MatchValue(value=f"{document_id}")),
        ]
    )
    try:
        filename = PdfTopicMap.objects.get(document_id = document_id).pdf_name
        topic = PdfTopicMap.objects.get(document_id = document_id).topic
    except Exception as e:
        raise KMsystemException(KMsystemError.DB_SERVER_ERROR, e)
    response = Connection().qdrant_connection().delete(
        collection_name = COLLECTION,
        points_selector=delete_filter
    )
    if response.status.value != "completed":
        raise KMsystemException(KMsystemError.QDRANT_SERVER_ERROR, "刪除過程出錯")
    return filename, topic
        
def _file_delete(filename, document_id, topic):
    file_path = os.path.join(MEDIA_ROOT, topic, filename)
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        raise KMsystemException(KMsystemError.INTERNAL_SERVER_ERROR, e)
    try:
        obj = PdfTopicMap.objects.get(
            document_id = document_id
        )
        obj.delete()
    except Exception as e:
        raise KMsystemException(KMsystemError.DB_SERVER_ERROR ,e)
    
    