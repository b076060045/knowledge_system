from django.http import JsonResponse

SUCCESSFUL_CODE = 0


class NexDATAResponse:
    """
    定義成功回應的靜態工具類
    """

    @staticmethod
    def to_json_response(data={}, status=200):
        """
        返回標準化的 JsonResponse 成功響應
        :param data: 可選的數據
        :param status: HTTP 狀態碼，默認為 200
        :return: JsonResponse 對象
        """
        return JsonResponse({
            "code": SUCCESSFUL_CODE,
            "data": data
        }, status=status)
