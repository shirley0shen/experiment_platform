import streamlit as st
import pymongo
from openai import OpenAI
import datetime
import time
import random

# 1. 初始化 MongoDB 连接
# 在 Streamlit Secrets 中配置: [mongo] uri = "mongodb+srv://..."
@st.cache_resource
def init_connection():
    return pymongo.MongoClient(st.secrets["mongo"]["uri"])

client = init_connection()
db = client.experiment_db
collection = db.user_records

# 2. 初始化 AI 客户端 (建议使用 DeepSeek 或 Kimi 以确保国内访问稳定)
# 在 Streamlit Secrets 中配置: [ai] api_key = "sk-...", base_url = "https://api.deepseek.com"
client_ai = OpenAI(
    api_key=st.secrets["ai"]["api_key"],
    base_url=st.secrets["ai"]["base_url"]
)

# 3. 数据保存函数
def save_data(user_id, stage, data):
    """将数据更新到 MongoDB"""
    collection.update_one(
        {"user_id": user_id},
        {"$set": {
            f"stages.{stage}": data,
            "last_updated": datetime.datetime.now()
        }},
        upsert=True
    )

# 4. AI 生成函数 (对应实验设计)
def generate_ai_content(prompt_type, user_input=None):
    """
    根据实验组别调用 AI
    引用 和 的 Prompt
    """
    system_prompt = ""
    user_content = ""

    if prompt_type == "divergent": # 发散期 Prompt 
        system_prompt = "你是一位拥有无限想象力的儿童绘本作家，专精于为4-7岁儿童创作故事。你擅长用最简单的语言构建出奇妙的世界观。\
        请以“勇气”为核心主题，进行头脑风暴，构思 3 个截然不同的故事核心创意。\
        **一句话概括**：每个创意只能用一句话描述，要短小精悍，吸引人。\
        **差异化**：请确保这3个故事发生在完全不同的场景。\
        **受众**：确保内容适合4-7岁儿童的认知水平，不要过于抽象。"
        user_content = "请提供3个创意概念。"
    
    elif prompt_type == "convergent": # 收敛期 Prompt 
        system_prompt = "你是一位资深的儿童故事作家。请将以下用户提供的创意扩展成一份详细的故事情节概要，字数控制在200字左右。\
        请按照故事世界观设定、简单情节发展、预期的教育/情感效果三个方面进行展开。优化语言使其更符合4-7岁儿童的理解水平。\
        但不要改变核心故事情节和创意原点。"
        user_content = f"这是我的创意：\n{user_input}"
    
    # --- 增加重试逻辑 ---
    max_retries = 3  # 最大重试次数
    base_delay = 2   # 基础等待秒数

    for attempt in range(max_retries):
        try:
            # 尝试调用 API
            response = client_ai.chat.completions.create(
                model="deepseek-chat", 
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=1,
                timeout=60 # 设置一个合理的超时时间，防止无限卡死
            )
            return response.choices[0].message.content
        
        except Exception as e:
            # 检查是否是速率限制 (429) 或 服务器过载 (50x)
            error_str = str(e)
            if "429" in error_str or "500" in error_str or "502" in error_str:
                if attempt < max_retries - 1:
                    # 智能退避：等待时间随重试次数增加 (2s, 4s, 8s...)
                    # 增加一点随机数，防止所有失败的请求在同一毫秒重试
                    sleep_time = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    print(f"API 请求繁忙，正在进行第 {attempt + 1} 次重试，等待 {sleep_time:.2f} 秒...")
                    time.sleep(sleep_time)
                    continue # 跳回循环开头重试
            
            # 如果是其他错误（比如 Prompt 格式不对）或重试次数用尽，则返回错误
            return f"AI 生成服务暂时繁忙，请稍后重试。（错误信息: {e}）"
            
    return "AI 服务响应超时，请刷新页面重试。"

# 5. AI 自定义问题函数（支持用户自由提问）
def ask_ai_custom_question(user_question):
    """
    允许用户向 AI 提出自定义问题
    user_question: 用户的问题
    """
    system_prompt = "你是一位儿童故事创作专家，擅长为4-7岁儿童创作故事。你的回答应该简洁、富有启发性，帮助创作者打开思路。"
    user_content = user_question
    
    # 使用相同的重试逻辑
    max_retries = 3
    base_delay = 2

    for attempt in range(max_retries):
        try:
            response = client_ai.chat.completions.create(
                model="deepseek-chat", 
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.8,
                timeout=60
            )
            return response.choices[0].message.content
        
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "500" in error_str or "502" in error_str:
                if attempt < max_retries - 1:
                    sleep_time = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    print(f"API 请求繁忙，正在进行第 {attempt + 1} 次重试，等待 {sleep_time:.2f} 秒...")
                    time.sleep(sleep_time)
                    continue
            
            return f"AI 生成服务暂时繁忙，请稍后重试。（错误信息: {e}）"
            
    return "AI 服务响应超时，请刷新页面重试。"



