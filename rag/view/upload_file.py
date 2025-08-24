from knowledge_system.errors import NexDATAError, NexDATAException
from drf_spectacular.utils import extend_schema
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view, parser_classes
from knowledge_system.utils.decorator import try_catch_decorator
from knowledge_system.responses import NexDATAResponse
from knowledge_system.settings import MEDIA_ROOT, COLLECTION
from knowledge_system.connection import Connection
from raghub.serializers import (
    UploadFileSerializer,
    MessageSerializer
)
from raghub.models import PdfTopicMap
from qdrant_client.http import models
from qdrant_client.http.models import PointStruct
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from langchain.text_splitter import CharacterTextSplitter
from sentence_transformers import SentenceTransformer
import os
from uuid import uuid4

CHUNK_SIZE = 300
CHUNK_OVERLAP = 20
VECTOR_SIZE = 768
MEMMAP_THRESHOLD = 200000
NEAR_NODE = 16
EF_CONSTRUCT = 100

@extend_schema(
    request=UploadFileSerializer,              # 告訴 Swagger 這是 multipart 的欄位
    responses={200: MessageSerializer},        # 回傳結構
    summary="上傳 PDF",
    description="以 multipart/form-data 上傳檔案，並指定 collection 與 permission_tags"
)
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
@try_catch_decorator
# 步驟
def upload_file(request):
    #參數驗證
    s = UploadFileSerializer(data = request.data)
    try:
        s.is_valid(raise_exception=True)
        file = s.validated_data["file"]
        topic = s.validated_data["topic"]
        permission_tags = s.validated_data["permission_tags"]
    except Exception as e:
        raise NexDATAException(NexDATAError.INVALID_PARAMETER, e) 
    
    # 檔案儲存
    filename = file.name
    chunks = file.chunks()
    _check_unique_file_topic(topic, filename)
    file_path = _file_save(filename, chunks, topic)
    full_text = _pdf_to_text(file_path)
    text_splitter = _split_text(full_text)
    document_id = _save_to_qdrant(topic, text_splitter, filename, permission_tags)
    return NexDATAResponse.to_json_response(document_id)   

def _check_unique_file_topic(topic, filename):
    if PdfTopicMap.objects.filter(pdf_name = filename, topic = topic).exists():
        raise NexDATAException(NexDATAError.DB_SERVER_ERROR, f"{filename}已經存在{topic}請勿重複上傳")

# 檔案儲存
def _file_save(filename, chunks, topic):
    file_path = os.path.join(MEDIA_ROOT, topic, filename)
    try:
        #不存在就建立
        if not os.path.exists(os.path.join(MEDIA_ROOT, topic)):
            os.makedirs(os.path.join(MEDIA_ROOT, topic), exist_ok=True)
        with open(file_path, 'wb+') as destination:
            for chunk in chunks:
                destination.write(chunk)
        return file_path
    except Exception as e:
        raise NexDATAException(NexDATAError.INTERNAL_SERVER_ERROR, e)
    
# 轉成文字
def _pdf_to_text(file_path):
    try:
        reader = PdfReader(file_path)
        full_text = ""
        for page in reader.pages:
            text = page.extract_text()
            full_text += text + "\n"
    except PdfReadError as e:
        raise NexDATAException(NexDATAError.INTERNAL_SERVER_ERROR, e)
    return full_text

# 文字切割
def _split_text(text):
    try:
        text_splitter = CharacterTextSplitter(
            separator="\n", chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
        ).split_text(text)
    except ValueError as e:
        raise NexDATAException(NexDATAError.INTERNAL_SERVER_ERROR, e)
    return text_splitter

def _save_to_qdrant(topic, text_splitter, filename, permission_tags):
    #建立collection
    try:
        if not Connection().qdrant_connection().collection_exists(COLLECTION):
            Connection().qdrant_connection().create_collection(
                COLLECTION, 
                vectors_config=models.VectorParams(
                    distance=models.Distance.COSINE, size=VECTOR_SIZE
                ),
                optimizers_config=models.OptimizersConfigDiff(memmap_threshold=MEMMAP_THRESHOLD),
                hnsw_config=models.HnswConfigDiff(on_disk=True, m=NEAR_NODE, ef_construct=EF_CONSTRUCT),
            )
    except Exception as e:
        raise NexDATAException(NexDATAError.QDRANT_SERVER_ERROR, e)
    #檢測collection是否存在
    embedding_func = SentenceTransformer("nomic-ai/nomic-embed-text-v1", trust_remote_code = True)
    document_id = str(uuid4())
    
    for i, text in enumerate(text_splitter):
        id = str(uuid4())
        try:
            response = embedding_func.encode([text])[0]
        except Exception as e:
            raise NexDATAException(NexDATAError.INTERNAL_SERVER_ERROR, message = e)        
        try:
            Connection().qdrant_connection().upsert(
                collection_name=COLLECTION,
                points=[
                    PointStruct(
                        id=id,
                        vector=response,
                        payload={
                            "text": text,
                            "pdf": filename,
                            "permission_tag": permission_tags,
                            "document_id": document_id,
                            "topic": topic
                        },
                    )
                ],
            )
        except Exception as e:
            raise NexDATAException(NexDATAError.QDRANT_SERVER_ERROR, message = e)
    #更新collection與檔案的對照表  
    try:
        PdfTopicMap.objects.get_or_create(
            document_id = document_id,
            pdf_name = filename,
            topic = topic
        )
    except Exception as e:
        NexDATAException(NexDATAError.DB_SERVER_ERROR, e)
    return document_id