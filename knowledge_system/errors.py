from xmlrpc.client import INTERNAL_ERROR
from django.http import HttpResponse, JsonResponse
from rest_framework import status as http_status


class NexDATAError:
    @staticmethod
    def to_json_response(error, status, message):
        """
        返回標準化的 JsonResponse 錯誤響應
        :param error: 錯誤字典（例如 NexDATAError.INVALID_API）
        :param status: HTTP 狀態碼，默認為 400
        :param message: 可選的附加訊息
        :return: JsonResponse 對象
        """
        error_message = error["message"]
        if message:
            error_message = f"{error_message} {message}"

        return JsonResponse({
            "code": error["code"],
            "message": error_message,
        }, status=status)
    
    # API 路由問題
    INVALID_API = {
        "code": 1001, "message": "[Invalid API Error]", "status": http_status.HTTP_400_BAD_REQUEST}

    # 登入者問題
    UNAUTHORIZED_TOKEN = {
        "code": 1101, "message": "[Unauthorized Token Error]", "status": http_status.HTTP_401_UNAUTHORIZED}
    INVALID_IDENTITY = {
        "code": 1102, "message": "[Invalid Identity Error]", "status": http_status.HTTP_401_UNAUTHORIZED}

    # 登入者權限問題
    PERMISSION_DENIED = {
        "code": 1201, "message": "[Permission Denied Error]", "status": http_status.HTTP_403_FORBIDDEN}

    # API 參數問題
    INVALID_PARAMETER = {
        "code": 1301, "message": "[Invalid Parameter Error]", "status": http_status.HTTP_400_BAD_REQUEST}
    INSUFFICIENT_PARAMETER = {
        "code": 1302, "message": "[Insufficient Parameter Error]", "status": http_status.HTTP_400_BAD_REQUEST}
    
    # 檔案相關問題
    INVALID_FILE_SIZE = {
        "code": 1401, "message": "[File Size Error]", "status": http_status.HTTP_400_BAD_REQUEST
    }

    # 其他問題
    API_GATEWAY_SERVER_ERROR = {
        "code": 9991, "message": "[Api Gateway Server Error]", "status": http_status.HTTP_400_BAD_REQUEST}
    QDRANT_SERVER_ERROR = {
        "code": 9992, "message": "[Qdrant Server Error]", "status": http_status.HTTP_400_BAD_REQUEST
    }

    REQUEST_TIMEOUT = {
        "code": 9998, "message": "[Request Timeout Error]", "status": http_status.HTTP_408_REQUEST_TIMEOUT}
    INTERNAL_SERVER_ERROR = {
        "code": 9999, "message": "[Internal Server Error]", "status": http_status.HTTP_500_INTERNAL_SERVER_ERROR}
    OPENAI_SERVER_ERROR = {
        "code": 9997, "message": "[Openai Server Error]", "status": http_status.HTTP_408_REQUEST_TIMEOUT
    }
    OLLAMA_SERVER_ERROR = {
        "code": 9996, "message": "[Ollama Server Error]", "status": http_status.HTTP_408_REQUEST_TIMEOUT
    }
    DB_SERVER_ERROR = {
        "code": 9995, "message": "[Database Server Error]", "status": http_status.HTTP_408_REQUEST_TIMEOUT
    }


class NexDATAException(Exception):
    def __init__(self, error, message=None, status=http_status.HTTP_400_BAD_REQUEST):
        """
        初始化異常
        :param error: 錯誤字典（如 NexDATAError.INVALID_PARAMETER）
        :param message: 附加的詳細資訊
        :param status: HTTP 狀態碼，默認為 400
        """
        self.error = error
        self.message = message
        self.status = error.get("status", status)

        super().__init__(self.error['message'])

    def to_response(self):
        """
        轉換為 JsonResponse 格式
        :return: JsonResponse
        """
        return NexDATAError.to_json_response(self.error, status=self.status, message=self.message)
