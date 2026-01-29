import streamlit as st
import random
import uuid
from utils import save_data, generate_ai_content


import os
import sys
from streamlit.web import cli as stcli

def handler(request):
    # 将入口指向你的主程序，例如 main.py
    sys.argv = ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
    stcli.main()
    
# --- 页面配置 ---
st.set_page_config(page_title="创意实验", layout="wide")

# --- 状态初始化 ---
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = str(uuid.uuid4())

if 'group' not in st.session_state:
    # 随机分配 4 个实验组 
    # 1: Control (无AI), 2: Div-AI (发散AI), 3: Conv-AI (收敛AI), 4: Both-AI (两阶段AI)
    st.session_state['group'] = 1#random.choice([1, 2, 3, 4]) 

if 'step' not in st.session_state:
    st.session_state['step'] = 0 # 0: Welcome, 1: Pre-test, 2: Brief, 3: Ideation, 4: Implementation, 5: Post-test

# --- 辅助函数：翻页 ---
def next_step():
    st.session_state['step'] += 1
    st.rerun()

# ================= 页面路由逻辑 =================

# --- P0: 欢迎与登录 ---
if st.session_state['step'] == 0:
    st.title("欢迎参加创意实验")
    st.info("本实验全程约耗时 10 分钟。请在电脑端完成。")
    st.write(f"您的 ID: {st.session_state['user_id']}")
    # 可以在这里加一个简单的登录框或直接开始
    if st.button("开始实验"):
        save_data(st.session_state['user_id'], "meta", {"group": st.session_state['group']})
        next_step()

# --- P1: Q1 前测问卷 ---
elif st.session_state['step'] == 1:
    st.header("阶段 1/5: 个人背景调查")
    with st.form("pre_survey"):
        st.subheader("1. DAT 创意能力测试")
        st.write("请写出 10 个意思尽可能不相关的名词。这些词之间应该在含义、类别和用途上尽量没有联系。例如，‘猫’和‘狗’非常相似，而‘猫’和‘民主’则非常不同。")
        unrelated_words = st.text_area("输入 10 个词汇（请用逗号分隔）")

        st.divider()
        st.subheader("2. 设计专业知识 (Self-Report)")
        expert_1 = st.select_slider("我擅长此类设计任务。", options=range(1, 8), value=4, help="1=极其不同意, 7=极其同意")
        expert_2 = st.select_slider("我知道如何做好此类设计任务。", options=range(1, 8), value=4)

        st.divider()
        st.subheader("3. AI 工具熟悉度与态度")
        ai_fam = st.select_slider("您对生成式人工智能 (GenAI) 工具的熟悉程度如何？", options=range(1, 8), value=4, help="1=完全不熟悉, 7=极其熟悉")
        ai_freq = st.selectbox("您使用生成式人工智能工具（如 LLM）的频率如何？", ["从不", "极少", "有时", "经常", "每天"])
        
        st.write("您对生成式人工智能工具的总体态度是什么？(1=负向, 7=正向)")
        att_1 = st.select_slider("不太认同 / 认同", options=range(1, 8), value=4)
        att_2 = st.select_slider("差 / 好", options=range(1, 8), value=4)
        att_3 = st.select_slider("消极 / 积极", options=range(1, 8), value=4)

        st.divider()
        st.subheader("4. 人口统计学信息")
        age = st.number_input("您的年龄？", min_value=18, max_value=100, step=1)
        gender = st.radio("您的性别？", ["男", "女", "非二元/其他", "拒绝回答"], horizontal=True)
        edu = st.selectbox("您的教育背景？", ["高中及以下", "本科在读/毕业", "硕士在读/毕业", "博士在读/毕业"])

        if st.form_submit_button("提交并开始构思"):
            save_data(st.session_state['user_id'], "pre_survey", {
                "dat_words": unrelated_words,
                "expertise": [expert_1, expert_2],
                "ai_familiarity": ai_fam,
                "ai_frequency": ai_freq,
                "ai_attitude": [att_1, att_2, att_3],
                "demographics": {"age": age, "gender": gender, "edu": edu}
            })
            next_step()

# --- P2: 创意 Brief ---
elif st.session_state['step'] == 2:
    st.header("阶段 2/5: 创意简报 (Creative Brief)")
    st.markdown("""
    * **客户**: “VerdeSip” (基于微藻技术的有机能量饮料)
    * **目标受众**: Gen Z (Z 世代)
    * **核心信息**: “Energy that creates life, not debt.”
    * **品牌调性**: 前卫 (Edgy)、未来感 (Futuristic)、充满希望 (Hopeful)
    * **任务**: 撰写一个 **60秒短视频脚本**。
    """)
    if st.button("我已阅读，开始构思"):
        next_step()

# --- P3: 发散/构思阶段 (Ideation) ---
elif st.session_state['step'] == 3:
    st.header("阶段 3/5: 创意构思 (Ideation)")
    st.write("任务：请提交一份脚本大纲。")
    
    group = st.session_state['group']
    ai_suggestions = ""

    # 实验操纵：C2 和 C4 组在发散阶段有 AI 介入 
    if group in [2, 4]:
        st.success("🤖 AI 助手已激活")
        if st.button("获取 AI 创意灵感"):
            with st.spinner("AI 正在生成概念..."):
                # 调用 utils 中的函数，使用 的 Prompt
                ai_suggestions = generate_ai_content("divergent")
                st.session_state['ai_ideation_result'] = ai_suggestions
        
        if 'ai_ideation_result' in st.session_state:
            st.info("AI 提供的参考概念：")
            st.markdown(st.session_state['ai_ideation_result'])

    with st.form("ideation_main_form"):
        ideation_text = st.text_area("请提交您的脚本大纲：", height=200)
        st.divider()
        st.subheader("Q2: 阶段反馈问卷")
        
        att_check_ai = st.radio("您在此阶段是否使用了 AI 工具激发灵感？", ["是", "否"], horizontal=True)
        ai_influence = st.slider("AI 内容在多大程度上影响了您？(0=无影响, 100=完全基于AI)", 0, 100, 0)
        
        st.write("**1. 感知努力程度** (1=极其不同意, 7=极其同意)")
        eff_1 = st.select_slider("执行此任务非常容易。", options=range(1, 8), value=4)
        eff_2 = st.select_slider("我投入了大量精力。", options=range(1, 8), value=4)
        eff_3 = st.select_slider("完成此任务是一项轻松的任务。", options=range(1, 8), value=4)
        
        self_creativity = st.select_slider("评价您提交内容的创造力水平？", options=range(1, 6), value=3, help="1=非常低, 5=非常高")
        
        st.write("**2. 认知刺激**")
        stim_1 = st.select_slider("我觉得自己受到了许多设计想法的启发。", options=range(1, 8), value=4)
        stim_2 = st.select_slider("我相信我脑中产生了许多不同的设计风格。", options=range(1, 8), value=4)
        
        st.write("**3. 选择超载**")
        over_1 = st.select_slider("当有很多选项时，我发现很难做出选择。", options=range(1, 8), value=4)
        over_2 = st.select_slider("选项太多让我感到困惑，使决策更困难。", options=range(1, 8), value=4)

        if st.form_submit_button("提交并进入下一阶段"):
            save_data(st.session_state['user_id'], "ideation_stage", {
                "content": ideation_text,
                "q2_feedback": {
                    "att_check": att_check_ai, "influence": ai_influence,
                    "effort": [eff_1, eff_2, eff_3], "creativity": self_creativity,
                    "stimulation": [stim_1, stim_2], "overload": [over_1, over_2]
                }
            })
            st.session_state['draft_outline'] = ideation_text
            next_step()

# --- P4: 收敛/执行阶段 (Implementation) ---
elif st.session_state['step'] == 4:
    st.header("阶段 4/5: 执行与完善 (Implementation)")
    st.write("任务：将选定的大纲发展为完整的 60 秒分镜脚本。")
    
    group = st.session_state['group']
    draft = st.session_state.get('draft_outline', "")
    
    # 实验操纵：C3 和 C4 组在收敛阶段有 AI 介入 
    if group in [3, 4]:
        st.success("🤖 AI 润色助手已激活")
        st.write("当前草稿：", draft)
        if st.button("使用 AI 格式化并润色"):
            with st.spinner("AI 正在改写..."):
                # 使用 的 Prompt
                polished_script = generate_ai_content("convergent", user_input=draft)
                st.session_state['ai_polished_result'] = polished_script
        
        if 'ai_polished_result' in st.session_state:
            st.info("AI 优化后的脚本：")
            st.text_area("AI 建议", st.session_state['ai_polished_result'], height=300)

    with st.form("final_stage_form"):
        final_script = st.text_area("请提交最终确定的 60 秒分镜脚本：", 
                                   value=st.session_state.get('ai_polished_result', draft), height=300)
        
        st.divider()
        st.subheader("Q3: 最终阶段反馈")
        
        att_check_ai_2 = st.radio("您在此阶段是否使用了 AI 工具？", ["是", "否"], horizontal=True)
        
        st.write("**1. 感知努力程度**")
        eff_p4_1 = st.select_slider("执行此任务非常容易。 ", options=range(1, 8), value=4)
        eff_p4_2 = st.select_slider("我投入了大量精力。 ", options=range(1, 8), value=4)
        
        conf = st.select_slider("在执行任务时，我感到很有信心。", options=range(1, 8), value=4)
        mood = st.select_slider("描述您在任务期间的情绪？(1=非常消极, 7=非常积极)", options=range(1, 8), value=4)
        engage = st.select_slider("您感觉自己的参与度如何？(1=完全没参与, 7=非常参与)", options=range(1, 8), value=4)
        
        st.write("**2. 工作常规化**")
        routine_1 = st.select_slider("此工作与我通常遵循的重复性常规流程吻合。", options=range(1, 8), value=4)
        routine_2 = st.select_slider("此工作与我日常所做的工作有所不同。", options=range(1, 8), value=4)
        
        st.write("**3. 选择超载 (针对执行环节)**")
        over_p4 = st.select_slider("评估许多选项需要耗费大量的精力和体力。", options=range(1, 8), value=4)

        if st.form_submit_button("提交最终作品"):
            save_data(st.session_state['user_id'], "implementation_stage", {
                "final_content": final_script,
                "q3_feedback": {
                    "att_check": att_check_ai_2, "effort": [eff_p4_1, eff_p4_2],
                    "confidence": conf, "mood": mood, "engagement": engage,
                    "routine": [routine_1, routine_2], "overload": over_p4
                }
            })
            next_step()

# --- P5: 结束 ---
elif st.session_state['step'] == 5:
    st.balloons()
    st.header("实验完成")
    st.success("您的数据已成功保存。感谢您为学术研究做出的贡献！")
    st.write(f"实验凭证 ID: {st.session_state['user_id']}")
    st.stop()