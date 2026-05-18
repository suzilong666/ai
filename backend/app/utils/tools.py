"""
工具函数定义 - 供 Agent 使用的工具
"""
import requests
from langchain.tools import tool


@tool
def get_weather(city: str) -> str:
    """获取城市的天气信息。
    
    Args:
        city: 城市名称
        
    Returns:
        天气信息字符串
    """
    try:
        url = "https://uapis.cn/api/v1/misc/weather"
        params = {"city": city}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.Timeout:
        return f"获取 {city} 天气超时，请稍后重试"
    except requests.exceptions.RequestException as e:
        return f"获取 {city} 天气失败：{str(e)}"