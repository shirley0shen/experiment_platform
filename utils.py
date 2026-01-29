import streamlit as st
import pymongo
from openai import OpenAI
import datetime
import uuid

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
        system_prompt = "作为 VerdeSip 的创意总监，请生成 3 个针对 Z 世代的、风格前卫的 60 秒视频脚本概念。每个概念必须有独特的视觉钩子（ Visual Hook ）和叙事转折。"
        user_content = "请提供创意概念。"
    
    elif prompt_type == "convergent": # 收敛期 Prompt 
        system_prompt = "你是一个专业的视频脚本编辑。请将以下用户提供的草稿重写为标准的双栏视频脚本格式（视觉 vs. 听觉）。优化语言使其更符合 Gen Z 的口语习惯，但不要改变核心故事情节和创意原点。"
        user_content = f"这是我的草稿：\n{user_input}"

    try:
        response = client_ai.chat.completions.create(
            model="deepseek-chat", # 或 gpt-3.5-turbo, moonshot-v1-8k
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI 生成出错: {e}"