from operator import call
from knowledge_system.errors import KMsystemError, KMsystemException
from drf_spectacular.utils import extend_schema
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view, parser_classes
from knowledge_system.utils.decorator import try_catch_decorator
from knowledge_system.responses import KMsystemResponse
from knowledge_system.settings import COLLECTION
from knowledge_system.connections import Connection
from rag.serializers import (
    MessageSerializer,
    AskSerializer
)
from rag.models import QARecord
from rag.utils.connect_llm import LlmConfig, call_llm
from sentence_transformers import SentenceTransformer
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

"""
step: 
1. 根據問題去分類collection然後去找尋相關的文件
2. 去搜尋該帳號的歷史紀錄
3. 組成prompt問LLM
4. 紀錄歷史紀錄
"""
@extend_schema(
    request=AskSerializer,              # 告訴 Swagger 這是 multipart 的欄位
    responses={200: MessageSerializer},        # 回傳結構
    summary="詢問LLM",
    description="以 multipart/form-data 上傳檔案，並指定 provider 與 model"
)
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
@try_catch_decorator
def ask_question(request):
    s = AskSerializer(data = request.data)
    try:
        s.is_valid(raise_exception=True)
        prompt = s.validated_data["prompt"]
        user_name = s.validated_data["user_name"]
        user_id = s.validated_data["user_id"]
        topic = s.validated_data["topic"]
        provider = s.validated_data["provider"]
        model    = s.validated_data["model"] 
        llm_config = LlmConfig(provider, model)
    except Exception as e:
        raise KMsystemException(KMsystemError.INVALID_PARAMETER, e) 

    relative_doc = _retrieve_relevant_chunks(prompt, topic)
    record = _get_record_history()
    full_prompt = _ans_with_context(relative_doc, record, prompt)
    ans = call_llm(full_prompt, llm_config)
    _add_record_history(prompt, ans)
    return KMsystemResponse.to_json_response(ans)

"""
def _choose_topic(prompt, llm_config:LLMConfig):
    topic_list = show_topic_list()
    topic_list = ",".join(topic_list)
    topic_list_ans = "或".join(topic_list)
    prompt = (
        f"使用者的問題是：\n{prompt}\n\n"
        f"目前有以下 topic 可供選擇：\n"
        f"{topic_list}\n\n"
        f"請從這些 collection 中選出最符合問題主題的一個選項。\n"
        f"你只能回答以下其中一個選項：{topic_list_ans}\n"
        f"不能解釋，不能補充，不能說明原因。\n"
        f"請只輸出 collection 名稱。"
    )
    return call_llm(prompt, llm_config)
"""

def _retrieve_relevant_chunks(prompt, topic):
    try:
        f = Filter(
        must=[
            FieldCondition(key="topic", match=MatchValue(value=topic)),     # topic 必須是 HR
        ],
        )
        query_vector = SentenceTransformer("nomic-ai/nomic-embed-text-v1", trust_remote_code = True).encode([prompt])[0]
        results = Connection().qdrant_connection().search(
            collection_name=COLLECTION,
            query_vector=query_vector,  # 一個 list 或 numpy array，長度要和建立時設定的維度一致
            limit=5,  # 回傳前幾筆最相近的資
            query_filter= f
            )
        relative_doc = ''
        for result in results:
            relative_doc += result.payload['text']
        return relative_doc
    except:
        pass

def _ans_with_context(relative_doc, record, prompt):
    if record:
        prompt = (
            f"請注意： \n"
            f"- 如果回答內容不在資料中，請誠實說「我不知道」。\n"
            f"- 絕對不要自行添加資料，也不要使用常識或推測回答，千萬不要用之前的記憶來回答。\n"
            f"以下是一些文件內容段落：\n\n{relative_doc}\n\n"
            f"這邊提供之前聊天的問答紀錄：\n\n{record}\n\n"
            f"請根據這些內容回答問題：\n\n{prompt}"
        )
    else:
        prompt = (
            f"請注意： \n"
            f"- 如果回答內容不在資料中，請誠實說「我不知道」。\n"
            f"- 絕對不要自行添加資料，也不要使用常識或推測回答，千萬不要用之前的記憶來回答。\n"
            f"以下是一些文件內容段落：\n\n{relative_doc}\n\n"
            f"請根據這些內容回答問題：\n\n{prompt}"
        )
    return prompt

def _add_record_history(question, ans):
    QARecord.objects.create(
        question=question,
        answer = ans
    )

def _get_record_history():
    records = QARecord.objects.filter(id = 1)
    full_record = ''
    for record in records:
        full_record += f"問題：{record.question}\n"
        full_record += f"回答：{record.answer}\n\n"
    return full_record
