import streamlit as st
import random
import uuid
import datetime
from utils import save_data,ask_ai_custom_question
import time  # <--- 新增


# 定义一个滚动到顶部的函数
def scroll_to_top():
    js = """
    <script>
        var body = window.parent.document.querySelector(".main");
        console.log(body);
        body.scrollTo(0, 0);
    </script>
    """
    st.components.v1.html(js, height=0)

# --- 辅助函数：记录时间 ---
def record_duration(stage_name):
    """
    计算从进入当前页面到现在的时长，并保存到 session_state
    """
    end_time = time.time()
    start_time = st.session_state['current_page_start_time']
    duration = end_time - start_time
    
    # 保存时长 (单位：秒)，保留2位小数
    st.session_state['time_logs'][stage_name] = round(duration, 2)
    
    # 重置计时器，为下一个页面做准备
    st.session_state['current_page_start_time'] = end_time
    
    # 打印日志方便调试 (可选)
    #print(f"[{stage_name}] 耗时: {duration:.2f} 秒")

# --- 辅助函数：翻页 ---
def next_step():
    st.session_state['step'] += 1
    st.rerun()

# --- 辅助函数：渲染AI助手（通用） ---
def render_ai_helper(stage_key, max_helps=3):
    """
    渲染AI助手界面，支持多次自定义提问
    stage_key: 阶段标识（如 'ideation', 'implementation'），用于区分不同阶段的session state
    max_helps: 最多可以求助的次数（默认3次）
    """
    
    
    # 初始化该阶段的求助次数和对话记录
    help_count_key = f'{stage_key}_ai_help_count'
    conversations_key = f'{stage_key}_ai_conversations'
    
    if help_count_key not in st.session_state:
        st.session_state[help_count_key] = 0
    if conversations_key not in st.session_state:
        st.session_state[conversations_key] = {}  # 改为字典
    
    remaining_helps = max_helps - st.session_state[help_count_key]
    
    if remaining_helps > 0:
        st.success(f"AI 助手已激活 | 剩余求助次数：{remaining_helps}/{max_helps}")
        
        # 用户输入问题
        with st.form(key=f"ai_help_form_{stage_key}_{st.session_state[help_count_key]}", clear_on_submit=True):
            user_question = st.text_input(
                "向AI提问（例如：如何让故事更有创意？）",
                placeholder="输入你想问的问题..."
            )
            submit_question = st.form_submit_button("提问AI")
            
            if submit_question and user_question.strip():
                with st.spinner("AI 正在思考...请稍候"):
                    ai_answer = ask_ai_custom_question(user_question)

                    # 保存对话记录到字典，使用 round_N 作为键
                    current_round = st.session_state[help_count_key] + 1
                    round_key = f'round_{current_round}'
                    st.session_state[conversations_key][round_key] = {
                        'question': user_question,
                        'answer': ai_answer,
                    }
                    st.session_state[help_count_key] += 1
                st.rerun()  # 刷新页面显示新的对话
    else:
        st.warning(f"⚠️ 您已用完{max_helps}次AI求助机会，请根据AI的建议完成创作！")
    
    # 显示所有历史对话
    if st.session_state[conversations_key]:
        st.markdown("---")
        st.subheader("AI 对话记录")
        for round_key in sorted(st.session_state[conversations_key].keys()):
            conv = st.session_state[conversations_key][round_key]
            idx = int(round_key.split('_')[1])
            with st.expander(f"第 {idx} 次提问：{conv['question'][:30]}...", expanded=(idx == len(st.session_state[conversations_key]))):
                st.markdown(f"**你的问题：** {conv['question']}")
                st.markdown(f"**AI 的回答：**")
                st.info(conv['answer'])




#================= 页面配置 =================
# --- 页面配置 ---
st.set_page_config(page_title="创意实验", layout="wide")

# --- 全局样式 ---
st.markdown(
    """
    <style>
    div[data-testid="stTextArea"] textarea {
        width: 100%;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- 状态初始化 ---
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = str(uuid.uuid4())

if 'group' not in st.session_state:
    # 随机分配 4 个实验组 
    # 1: Control (无AI), 2: Div-AI (发散AI), 3: Conv-AI (收敛AI), 4: Both-AI (两阶段AI)
    st.session_state['group'] = 4 #random.choice([1, 2, 3, 4]) 

if 'step' not in st.session_state:
    st.session_state['step'] = 0 # 0: Welcome, 1: Pre-test, 2: Brief, 3: Ideation, 4: Implementation, 5: Post-test

# [新增] 初始化时间记录相关的状态
if 'time_logs' not in st.session_state:
    st.session_state['time_logs'] = {} # 用于存储各阶段耗时

if 'current_page_start_time' not in st.session_state:
    st.session_state['current_page_start_time'] = time.time() # 记录当前页面开始的时间


# ================= 页面逻辑 =================

# --- P0: 欢迎与登录 ---
if st.session_state['step'] == 0:
    st.title("欢迎参加创意生成实验")
    st.info("本实验全程约耗时 20 分钟。请在电脑端完成。")
    #st.write(f"您的 ID: {st.session_state['user_id']}")
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
        unrelated_words_1 = st.text_input("第一个词")
        unrelated_words_2 = st.text_input("第二个词")
        unrelated_words_3 = st.text_input("第三个词")
        unrelated_words_4 = st.text_input("第四个词")
        unrelated_words_5 = st.text_input("第五个词")
        unrelated_words_6 = st.text_input("第六个词")
        unrelated_words_7 = st.text_input("第七个词")
        unrelated_words_8 = st.text_input("第八个词")
        unrelated_words_9 = st.text_input("第九个词")
        unrelated_words_10 = st.text_input("第十个词")


        st.divider()
        st.subheader("2. AI 工具熟悉度与态度")
        ai_fam = st.select_slider("您对生成式人工智能 (GenAI) 工具的熟悉程度如何？(1=完全不熟悉, 7=极其熟悉)", options=range(1, 8))
        ai_freq = st.selectbox("您使用生成式人工智能工具（如 LLM）的频率如何？", ["从不", "极少", "有时", "经常", "每天"])
        
        att_0 = st.select_slider("您对生成式人工智能工具的总体态度是什么？(1=负向, 7=正向)", options=range(1, 8))
        att_1 = st.select_slider("您对生成式人工智能工具好用吗？（1=不好用，7=好用", options=range(1, 8))
        att_2 = st.select_slider("您对生成式人工智能工具可信吗？（1=不可信，7=可信", options=range(1, 8))


        st.divider()
        st.subheader("3. 人口统计学信息")
        age = st.number_input("您的年龄？", min_value=10, max_value=90, step=1)
        gender = st.radio("您的性别？", ["男", "女"], index=None,horizontal=True)
        edu = st.radio("您的教育背景？", ["高中及以下", "本科在读/毕业", "硕士在读/毕业", "博士在读/毕业"], index=None,horizontal=True)

        if st.form_submit_button("提交并开始构思"):
            # 统一验证：检查所有必填字段
            dat_words = [unrelated_words_1, unrelated_words_2, unrelated_words_3, unrelated_words_4, unrelated_words_5, 
                        unrelated_words_6, unrelated_words_7, unrelated_words_8, unrelated_words_9, unrelated_words_10]
            
            validation_passed = True
            error_messages = []
            
            # 检查10个词
            if not all(word.strip() for word in dat_words):
                validation_passed = False
                error_messages.append("• 请填写全部 10 个不相关的名词")
            
            # 检查性别
            if gender is None:
                validation_passed = False
                error_messages.append("• 请选择您的性别")
            
            # 检查学历
            if edu is None:
                validation_passed = False
                error_messages.append("• 请选择您的学历")

            # 显示验证结果
            if not validation_passed:
                st.error("❌ 表单填写不完整，请先完成以下内容：\n" + "\n".join(error_messages))
            else:
                record_duration("P1_PreSurvey")
                save_data(st.session_state['user_id'], "q1_survey", {
                    "dat_words": dat_words,
                    "ai_familiarity": ai_fam,
                    "ai_frequency": ai_freq,
                    "ai_attitude": [att_0, att_1, att_2],
                    "demographics": {"age": age, "gender": gender, "edu": edu},
                    "q1_Presurvey_duration_sec": st.session_state['time_logs'].get("P1_PreSurvey", 0)
                })
                next_step()

# --- P2: 创意 Brief ---
elif st.session_state['step'] == 2:
    st.header("阶段 2/5: 创意任务要求")
    st.markdown("""
                请以“勇气”为主题，请构思一个面向4-7岁儿童的原创睡前故事，使故事极具吸引力。
                
                您可以从以下几个方面进行思考：故事世界观设定、简单情节发展、预期的教育/情感效果。
                尽可能发挥你的想象力，你可以写任何你想写的内容。

                后续主要有两个阶段的任务。
                
                阶段一：发散阶段 (Divergence)
                任务： 请基于“勇气”这个主题，快速构思3个截然不同的故事核心创意（每个故事创意请用一句话描述）。

                阶段二：收敛阶段 (Convergence) 
                任务： 请从你刚才的3个创意中挑选最棒的一个，完成一份故事情节概要。请不要直接写故事全文（约200字左右）

                现在，请花一些时间仔细阅读任务要求，并准备开始您的创意构思。    

  """)
    
    # 检查是否需要倒计时（分组为1, 3, 5, 7）
    # group = st.session_state['group']
    # if group in [1, 3, 5, 7]:
    #     # 初始化倒计时状态
    #     if 'incubation_start_time' not in st.session_state:
    #         st.session_state['incubation_start_time'] = time.time()
    #     
    #     # 计算剩余时间
    #     elapsed = time.time() - st.session_state['incubation_start_time']
    #     remaining = max(0, 60 - elapsed)  # 60秒 = 1分钟
    #     
    #     if remaining > 0:
    #         st.info(f"⏱️ 请花一分钟时间思考和酝酿创意...")
    #         # 显示倒计时
    #         countdown_placeholder = st.empty()
    #         countdown_placeholder.metric("倒计时", f"{int(remaining)} 秒")
    #         time.sleep(1)
    #         st.rerun()
    #     else:
    #         st.success("✅ 酝酿时间已结束，现在可以开始构思了！")
    #         if st.button("我已阅读，开始构思"):
    #             record_duration("P2_Brief")
    #             next_step()
    # else:
    #     # 其他分组不需要倒计时
    #     if st.button("我已阅读，开始构思"):
    #         record_duration("P2_Brief")
    #         next_step()
    
    if st.button("我已阅读，开始构思"):
        next_step()

# --- P3: 发散/构思阶段 (Ideation) ---
elif st.session_state['step'] == 3:
    
    st.header("阶段 3/5: 创意构思 (Ideation)")
    st.markdown("""
    请以"勇气"为主题，请构思一个面向4-7岁儿童的原创睡前故事，使故事极具吸引力。  
    您可以从以下几个方面进行思考：故事世界观设定、简单情节发展、预期的教育/情感效果。
    尽可能发挥你的想象力，你可以写任何你想写的内容。

    现在进入第一个发散阶段。
    任务： 请基于"勇气"这个主题，快速构思3个截然不同的故事核心创意（每个故事创意请用一句话描述）。
    """)
    
    # AI 逻辑 - 使用通用AI助手函数
    group = st.session_state['group']
    
    if group in [2, 4]:
        render_ai_helper(
            stage_key='ideation',
            max_helps=3
        )

    # 输入区域：3个创意概念
    st.subheader("请提交您的3个创意概念：")
    concept_1 = st.text_area("创意概念 1：", height=50, value=st.session_state.get('concept_1', ""))
    concept_2 = st.text_area("创意概念 2：", height=50, value=st.session_state.get('concept_2', ""))
    concept_3 = st.text_area("创意概念 3：", height=50, value=st.session_state.get('concept_3', ""))
     

    # 验证是否所有概念都已填写
    concepts = [concept_1, concept_2, concept_3]
    if not all(c.strip() for c in concepts):
        st.warning("请填写全部3个创意概念。")
    else:
        record_duration("P3_Ideation")
        # 保存所有概念到session_state
        st.session_state['concept_1'] = concept_1
        st.session_state['concept_2'] = concept_2
        st.session_state['concept_3'] = concept_3
        st.session_state['all_concepts'] = concepts
    st.info("请根据您刚才完成构思任务的体验，填写以下问卷。")


    with st.form("ideation_feedback_form"):
        st.subheader("Q2: 阶段反馈问卷")
        att_check_ai = st.radio("请告诉我们，您在构思阶段（即您刚刚经历的阶段）是否使用了生成式人工智能来激发您的灵感？（请如实回答：您的真实回答将有助于我们的研究。您的回答不会影响您的报酬。）", ["是", "否"], index=None,horizontal=True)
        ai_influence = st.slider("您认为 AI 生成的辅助内容在多大程度上影响了您提交的内容？ （请如实回答：您的真实回答将有助于我们的研究。您的回答不会影响您的报酬。）(1=无影响, 7=完全基于AI)", 1, 7)
        
        st.write("**1. 自我感知**")
        eff_1 = st.select_slider("对我来说，在构思阶段执行创意设计任务非常容易。(1=极其不同意, 7=极其同意)", options=range(1, 8))
        eff_2 = st.select_slider("我在构思阶段投入了大量精力。(1=极其不同意, 7=极其同意)", options=range(1, 8))
        
        st.write("**2. 创意自我评估：您如何评价自己提交内容的创造力水平**")
        self_creativity_1 = st.select_slider("这些想法非常独特。(1=极其不同意, 7=极其同意)", options=range(1, 8))
        self_creativity_2 = st.select_slider("这些想法在逻辑上行得通，符合任务要求。(1=极其不同意, 7=极其同意)", options=range(1, 8))
        self_creativity_3 = st.select_slider("细节描述丰富，非常精美(1=极其不同意, 7=极其同意)", options=range(1, 8))
        
        st.write("**3. 认知刺激**")
        stim_1 = st.select_slider("在这个过程中，我觉得自己受到了许多设计想法的启发。(1=极其不同意, 7=极其同意)", options=range(1, 8))
        stim_2 = st.select_slider("在这个过程中，我相信我的大脑中产生了很多不同的风格。(1=极其不同意, 7=极其同意)", options=range(1, 8))
        stim_3 = st.select_slider("在这个过程中，我认为我充分意识到了许多不同的风格。(1=极其不同意, 7=极其同意)", options=range(1, 8))
        

        if st.form_submit_button("提交并进入下一阶段"):
            # 统一验证：检查所有必填字段
            validation_passed = True
            error_messages = []
            
            if att_check_ai is None:
                validation_passed = False
                error_messages.append("• 请回答是否使用了 AI 工具激发灵感")
            
            # 显示验证结果
            if not validation_passed:
                st.error("❌ 表单填写不完整，请先完成以下内容：\n" + "\n".join(error_messages))
            else:
                save_data(st.session_state['user_id'], "ideation_stage", {
                    "concept_1": st.session_state.get('concept_1', ""),
                    "concept_2": st.session_state.get('concept_2', ""),
                    "concept_3": st.session_state.get('concept_3', ""),
                    "all_concepts": st.session_state.get('all_concepts', []),
                    #ai对话过程
                    "ai_conversations": st.session_state.get('ideation_ai_conversations', []),
                    "P3_Ideation_duration_sec": st.session_state['time_logs'].get("P3_Ideation", 0),
                    "q2_feedback": {
                        "att_check": att_check_ai, "influence": ai_influence,
                        "effort": [eff_1, eff_2], "creativity": [self_creativity_1, self_creativity_2, self_creativity_3],
                        "stimulation": [stim_1, stim_2, stim_3]
                    }
                })
                next_step()

# --- P4: 收敛/执行阶段 (Implementation) ---
elif st.session_state['step'] == 4:
    
    # 初始化子步骤状态
    if 'impl_sub_step' not in st.session_state:
        st.session_state['impl_sub_step'] = 0


    # ----- 子页面 1: 执行与完善 (创作区) -----
    if st.session_state['impl_sub_step'] == 0:
        
        st.header("阶段 4/5: 执行与完善 (Implementation)")
        st.markdown("""
         请以"勇气"为主题，请构思一个面向4-7岁儿童的原创睡前故事，使故事极具吸引力。  
        您可以从以下几个方面进行思考：故事世界观设定、简单情节发展、预期的教育/情感效果。
        尽可能发挥你的想象力，你可以写任何你想写的内容。

        现在进入阶段二，收敛阶段。
        任务： 请从你刚才的3个创意中挑选最棒的一个，完成一份故事情节概要。约200字左右。
      
        """)

        # 展示在 P3 填写的五个创意
        #st.subheader("您在上一步提交的 3 个创意概念")
        concepts = st.session_state.get('all_concepts', [])
        #for i, concept in enumerate(concepts, start=1):
            #st.markdown(f"**创意 {i}：** {concept}")

        # 让用户从五个创意中选择一个
        st.subheader("请选择您要展开的创意")
        selected_concept_index = st.radio("选择创意：", 
                                          options=range(len(concepts)), 
                                          format_func=lambda i: f"创意 {i+1}",
                                          horizontal=True)
        selected_concept = concepts[selected_concept_index]
        
        st.info(f"您选择的创意：**{selected_concept}**")
        st.session_state['selected_concept_index'] = selected_concept_index
        st.session_state['selected_concept'] = selected_concept

        
        group = st.session_state['group']
        draft = st.session_state.get('selected_concept', "")
        
        # 实验操纵：C3 和 C4 组在收敛阶段有 AI 介入
        if group in [3, 4]:
            render_ai_helper(
                stage_key='implementation',
                max_helps=3
            )

        # 最终编辑区
        final_script = st.text_area("请提交最终确定的故事：", 
                                   value=st.session_state.get('final_script_content', draft), 
                                   height=400)
        
        if st.button("完成创作，进入最后问卷"):
            if not final_script.strip():
                st.warning("内容不能为空。")
            else:
                record_duration("P4_Implementation")
                st.session_state['final_script_content'] = final_script
                st.session_state['impl_sub_step'] = 1
                st.rerun()

    # ----- 子页面 2: 最终阶段反馈问卷 -----
    elif st.session_state['impl_sub_step'] == 1:
        scroll_to_top()
        st.header("阶段 5/5: 最终阶段评价")
        st.write("请评价您在 **执行与完善脚本** 过程中的真实感受。")

        with st.form("final_feedback_form"):
            st.subheader("Q3: 最终阶段反馈")


            att_check_ai= st.radio("您在执行阶段（即您刚刚经历的阶段）是否使用了生成式人工智能工具？（请如实回答：您的真实回答将有助于我们的研究。您的回答不会影响您的报酬。）", ["是", "否"], index=None,horizontal=True)
            ai_influence = st.slider("您认为 AI 生成的辅助内容在多大程度上影响了您提交的内容？ （请如实回答：您的真实回答将有助于我们的研究。您的回答不会影响您的报酬。）(1=无影响, 7=完全基于AI)", 1, 7)
            
            st.write("**1. 自我感知**")
            eff_1 = st.select_slider("对我来说，在执行阶段执行创意设计任务非常容易。(1=极其不同意, 7=极其同意)", options=range(1, 8))
            eff_2 = st.select_slider("我在执行阶段投入了大量精力。(1=极其不同意, 7=极其同意)", options=range(1, 8))

            st.write("**2. 创意自我评估：您如何评价自己提交内容的创造力水平**")
            self_creativity_1 = st.select_slider("这些想法非常独特。(1=极其不同意, 7=极其同意)", options=range(1, 8))
            self_creativity_2 = st.select_slider("这些想法在逻辑上行得通，符合任务要求。(1=极其不同意, 7=极其同意)", options=range(1, 8))
            self_creativity_3 = st.select_slider("细节描述丰富，非常精美(1=极其不同意, 7=极其同意)", options=range(1, 8))
                
            st.write("**3. 认知刺激**")
            stim_1 = st.select_slider("在这个过程中，我觉得自己受到了许多设计想法的启发。(1=极其不同意, 7=极其同意)", options=range(1, 8))
            stim_2 = st.select_slider("在这个过程中，我相信我的大脑中产生了很多不同的风格。(1=极其不同意, 7=极其同意)", options=range(1, 8))
            stim_3 = st.select_slider("在这个过程中，我认为我充分意识到了许多不同的风格。(1=极其不同意, 7=极其同意)", options=range(1, 8))

            st.write("**4. 自信心**")
            confidence = st.select_slider("在执行任务时，我感到很有信心。(1=极其不同意, 7=极其同意)", options=range(1, 8))

            st.write("**5. 情绪**")
            emotion = st.select_slider("您会如何描述您在设计任务期间的情绪？(1=非常消极, 7=非常积极)", options=range(1, 8))

            st.write("**6. 参与感**")
            engagement = st.select_slider("您感觉自己对创意设计过程的参与度如何？(1=我完全没有参与, 7=我非常参与)", options=range(1, 8))


            if st.form_submit_button("提交最终作品并结束"):
                # 统一验证：检查所有必填字段
                validation_passed = True
                error_messages = []
                
                if att_check_ai is None:
                    validation_passed = False
                    error_messages.append("• 请回答是否使用了 AI 工具")
                
                # 显示验证结果
                if not validation_passed:
                    st.error("❌ 表单填写不完整，请先完成以下内容：\n" + "\n".join(error_messages))
                else:
                    record_duration("P5_Q3_FinalFeedback")
                    save_data(st.session_state['user_id'], "implementation_stage", {
                        #用户选择的创意概念
                        "selected_concept": st.session_state.get('selected_concept', ""),
                        #最后提交的故事概要
                        "final_content": st.session_state['final_script_content'],
                        #ai对话过程
                        "ai_conversations": st.session_state.get('implementation_ai_conversations', []),
                        "P4_Implementation_duration_sec": st.session_state['time_logs'].get("P4_Implementation", 0),
                        "q3_feedback": {
                            "att_check": att_check_ai, "influence": ai_influence,
                            "effort": [eff_1, eff_2],
                            "creativity": [self_creativity_1, self_creativity_2, self_creativity_3],
                            "stimulation": [stim_1, stim_2, stim_3],
                            "confidence": confidence,
                            "emotion": emotion,
                            "engagement": engagement,
                            "Q3_FinalFeedback_duration_sec": st.session_state['time_logs'].get("P5_Q3_FinalFeedback", 0)
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