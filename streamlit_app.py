import streamlit as st
import requests
import random
import json
from datetime import datetime
import pandas as pd
from streamlit.runtime.scriptrunner import get_script_run_ctx
from pymongo import MongoClient
from dotenv import load_dotenv
import os

def get_api_url():
    if os.environ.get('RENDER_INTERNAL_HOSTNAME'):
        # Render环境中优先使用内部地址
        return os.getenv('API_INTERNAL_URL', 'http://causeconnect-streamlit:10000')
    elif os.environ.get('API_URL'):
        # 使用环境变量中配置的地址
        return os.environ.get('API_URL')
    else:
        # 本地开发环境
        return "https://causeconnect-streamlit.onrender.com" 

API_URL = get_api_url()

# API调用函数
def call_api(endpoint, data=None):
    try:
        url = f"{API_URL}/{endpoint}"
        if data:
            response = requests.post(url, json=data)
        else:
            response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API调用失败: {str(e)}")
        return None

# 使用示例
def some_function():
    try:
        result = call_api("your_endpoint", {"some": "data"})
        if result:
            # 处理返回数据
            st.write(result)
    except Exception as e:
        st.error(f"处理失败: {str(e)}")

# 设置页面配置和主题
st.set_page_config(
    page_title="Organization Matching Platform",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main {
        background-color: #f5f7f9;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f4d7a;
        color: white;
    }
    .match-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    .score-high {
        color: #28a745;
        font-weight: bold;
    }
    .score-low {
        color: #dc3545;
        font-weight: bold;
    }
    .org-name {
        font-size: 20px;
        font-weight: bold;
        color: #1f4d7a;
    }
    .org-industry {
        color: #666;
        font-style: italic;
    }
    .section-title {
        background-color: #1f4d7a;
        color: white;
        padding: 10px;
        border-radius: 5px;
        margin: 20px 0;
    }
    .evaluation-status {
        font-size: 14px;
        padding: 4px 8px;
        border-radius: 4px;
        margin-top: 5px;
    }
    .status-accepted {
        background-color: #28a745;
        color: white;
    }
    .status-rejected {
        background-color: #dc3545;
        color: white;
    }
    .status-supplementary {
        background-color: #ffc107;
        color: black;
    }
    .stMarkdown {margin-bottom: 0px;}
    .stExpander {margin-top: 0px; margin-bottom: 0px;}
    .stContainer {margin-top: 0px; margin-bottom: 0px; padding-top: 0px; padding-bottom: 0px;}
    .stTextInput, .stTextArea, .stSelectbox {
        background-color: transparent !important;
    }
    .input-container {
        background-color: white;
        padding: 30px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .section-container {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .section-title {
        color: #1f4d7a;
        margin-bottom: 20px;
        font-size: 1.5em;
        font-weight: bold;
    }
    .section-description {
        color: #666;
        margin-bottom: 30px;
        font-size: 1em;
    }
</style>
""", unsafe_allow_html=True)

def call_matching_api(input_data, algorithm_type):
    """调用匹配API"""
    api_url = f"{get_api_url()}/test/complete-matching-process"
    if algorithm_type == "simple":
        api_url += "-simple"
    
    response = requests.post(api_url, json=input_data)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"API调用失败: {response.status_code}")

def display_match_card(match, index, scores_key):
    """Display a single match as a card"""
    org = match["organization"]
    similarity_score = match["similarity_score"]
    evaluation_status = match.get("evaluation_status", "Not evaluated")
    
    # 初始化session state中的分数
    if scores_key not in st.session_state:
        st.session_state[scores_key] = {}
    if index not in st.session_state[scores_key]:
        st.session_state[scores_key][index] = 5

    with st.container():
        st.markdown(f"""
        <div class="match-card">
            <div class="org-name">{org["name"]}</div>
            <div class="org-industry">{org["industries"]}</div>
            <div class="evaluation-status">Status: {evaluation_status}</div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("**Description:**")
            st.write(org["description"][:300] + "..." if len(org["description"]) > 300 else org["description"])
            
            st.write("**Mission:**")
            st.write(org["mission"])
            
            st.write("**Key Information:**")
            st.write(f"- Staff Count: {org['staff_count']}")
            st.write(f"- LinkedIn Followers: {org['linkedin_followers']}")
            
            # 根据组织类型显示不同信息
            if org.get("partnership"):
                st.write("**Partnership History:**")
                st.write(org["partnership"])
            if org.get("event"):
                st.write("**Event Experience:**")
                st.write(org["event"])
            if org.get("contribution"):
                st.write("**Contribution Capacity:**")
                st.write(org["contribution"])
            if org.get("assets"):
                st.write("**Assets:**")
                st.write(org["assets"])
        
        with col2:
            # 使用number_input而不是slider来避免拖动刷新
            score = st.number_input(
                "Rate this match (1-10)",
                min_value=1,
                max_value=10,
                value=st.session_state[scores_key][index],
                key=f"input_{scores_key}_{index}"
            )
            # 更新session state中的分数
            st.session_state[scores_key][index] = score
            
            if score >= 5:
                st.markdown(f'<p class="score-high">Good Match (Score: {score})</p>', unsafe_allow_html=True)
            else:
                st.markdown(f'<p class="score-low">Poor Match (Score: {score})</p>', unsafe_allow_html=True)

def display_matches(results, set_label):
    """显示匹配结果"""
    if f"scores_set_{set_label}" not in st.session_state:
        st.session_state[f"scores_set_{set_label}"] = {}

    for idx, match in enumerate(results["matching_results"]):
        # 如果是新页面的第一个项目，添加锚点
        if idx == 0:
            st.markdown(f'<div id="set_{set_label}_top"></div>', unsafe_allow_html=True)
        
        org = match["organization"]
        match_id = f"{set_label}_{idx}"
        
        # 确保每个match_id的数据结构存在
        if match_id not in st.session_state[f"scores_set_{set_label}"]:
            st.session_state[f"scores_set_{set_label}"][match_id] = {
                "score": None,
                "status": "Not Rated",
                "rated": False,
                "org_name": org['name'],
                "org_id": org.get('id', ''),
                "org_data": org  # 存储完整的组织数据
            }

        with st.container():
            st.markdown("""
                <div style='background-color: #f8f9fa; padding: 20px; border: 1px solid #e9ecef; border-radius: 8px; margin: 15px 0;'>
                """, unsafe_allow_html=True)
            
            # 组织名称和热门标签
            popularity_badge = "🔥 Popular!" if org.get('popularity', 'No') == 'Yes' else ""
            st.markdown(f"### {org['name']} {popularity_badge}")
            
            # 基本信息显示
            if org.get('mission'):
                st.markdown(f"**Mission:** *{org['mission']}*")
            st.markdown(f"**Industry:** {org.get('industries', '')}")
            st.markdown(f"**Specialities:** {org.get('specialities', '')}")
            
            # LinkedIn信息 - 修正字段名
            linkedin_info = f"LinkedIn Followers: {org.get('Linkedin_followers', 'N/A')}"
            st.markdown(f"**{linkedin_info}**")
            
            # 描述
            st.markdown("**Description:**")
            st.write(org.get('description', ''))
            
            # 评分部分
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown("""
                    <div style='font-size: 0.9em; margin-bottom: 10px;'>
                        <span style='color: #d32f2f; font-weight: bold;'>* Please rate this organization:</span>
                        <br>
                        <span style='color: #666;'>
                            Not Rated | 0-4: Unmatch | 5: Neutral | 6-10: Match
                        </span>
                    </div>
                """, unsafe_allow_html=True)
                
                # 评分选项
                score_selection = st.radio(
                    label=f"Rating for {org['name']}",
                    options=["Not Rated"] + list(range(0, 11)),
                    horizontal=True,
                    key=f"radio_{match_id}",
                    index=0,
                    label_visibility="collapsed"
                )
                
                # 更新评分状态
                current_data = st.session_state[f"scores_set_{set_label}"][match_id]
                if score_selection != "Not Rated":
                    score = int(score_selection)
                    status = "Match" if score > 5 else "Unmatch" if score < 5 else "Neutral"
                    current_data.update({
                        "score": score,
                        "status": status,
                        "rated": True,
                        "rated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                else:
                    current_data.update({
                        "score": None,
                        "status": "Not Rated",
                        "rated": False,
                        "rated_at": None
                    })

            # 状态显示
            with col2:
                status = current_data["status"]
                score = current_data["score"]
                
                status_color = {
                    "Match": "#28a745",
                    "Unmatch": "#dc3545",
                    "Neutral": "#ffc107",
                    "Not Rated": "#6c757d"
                }.get(status, "#6c757d")
                
                score_display = f"({score}/10)" if score is not None else ""
                
                st.markdown(f"""
                    <div style='padding: 8px 15px; 
                    background-color: {status_color}; 
                    color: white; 
                    border-radius: 5px; 
                    text-align: center; 
                    margin-top: 10px;'>
                        {status} {score_display}
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)

    # 在评分部分添加锁定状态提示
    if st.session_state.matching_locked:
        st.markdown("""
            <div style='background-color: #e8f4f8; padding: 10px; border-radius: 5px; margin: 10px 0;'>
                <p style='color: #2c5282; margin: 0;'>
                    🔒 Please complete the evaluation process. To start a new search, use the unlock button at the top.
                </p>
            </div>
        """, unsafe_allow_html=True)

def display_rating_summary():
    """显示评分总结和问卷链接"""
    st.markdown("### Ratings Summary")
    
    # 创建两列布局
    col1, col2 = st.columns(2)
    
    # 检查是否所有组织都已评分
    all_rated_a = all(data.get("rated", False) 
                     for data in st.session_state.get("scores_set_A", {}).values())
    all_rated_b = all(data.get("rated", False) 
                     for data in st.session_state.get("scores_set_B", {}).values())

    # Set A 在左列
    with col1:
        st.markdown("#### Set A")
        if "scores_set_A" in st.session_state and st.session_state["scores_set_A"]:
            ratings_data = [
                {
                    "Organization": data["org_name"],
                    "Score": data["score"],
                    "Status": data["status"],
                    "Rated At": data["rated_at"]
                }
                for data in st.session_state["scores_set_A"].values()
                if data.get("rated", False)  # 只显示已评分的
            ]
            if ratings_data:
                df = pd.DataFrame(ratings_data)
                st.dataframe(df, hide_index=True)
            
            if not all_rated_a:
                st.warning("⚠️ Please rate all organizations in Set A")

    # Set B 在右列
    with col2:
        st.markdown("#### Set B")
        if "scores_set_B" in st.session_state and st.session_state["scores_set_B"]:
            ratings_data = [
                {
                    "Organization": data["org_name"],
                    "Score": data["score"],
                    "Status": data["status"],
                    "Rated At": data["rated_at"]
                }
                for data in st.session_state["scores_set_B"].values()
                if data.get("rated", False)  # 只显示已评分的
            ]
            if ratings_data:
                df = pd.DataFrame(ratings_data)
                st.dataframe(df, hide_index=True)
            
            if not all_rated_b:
                st.warning("⚠️ Please rate all organizations in Set B")

    # 只有当两个set都完全评分后才显示问卷链接
    if all_rated_a and all_rated_b:
        st.markdown("""
        <div style='
            background-color: #f0f9ff;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #90cdf4;
            margin: 20px 0;
            text-align: center;
        '>
            <h4 style='color: #2b6cb0; margin: 0 0 10px 0;'>🎁 Complete Our Survey!</h4>
            <p style='margin: 0 0 15px 0;'>
                Thank you for rating all organizations! Please help us improve by completing a short survey.
                <br>
                <strong>As a token of our appreciation, you'll receive an Amazon Gift Card!</strong>
            </p>
            <a href='https://docs.google.com/forms/d/e/1FAIpQLSf1aKpa6qpxqi6Bxa9ex6fCOnMScDKJQJ4J1q426TgYHectqg/viewform?usp=dialog' 
               target='_blank' 
               style='
                    background-color: #4299e1;
                    color: white;
                    padding: 10px 20px;
                    text-decoration: none;
                    border-radius: 5px;
                    display: inline-block;
               '>
                Take Survey 📝
            </a>
        </div>
        """, unsafe_allow_html=True)

def initialize_algorithm_assignment():
    """初始化A/B测试的算法分配"""
    if "algorithm_assignment" not in st.session_state:
        # 随机分配算法
        algorithms = ["algorithm_1", "algorithm_2"]
        random.shuffle(algorithms)
        st.session_state.algorithm_assignment = {
            "A": algorithms[0],
            "B": algorithms[1]
        }

def save_to_mongodb(scores_a, scores_b, user_info):
    """保存评分数据到MongoDB"""
    try:
        # 确保算法映射存在
        if "algorithm_mapping" not in st.session_state:
            st.session_state.algorithm_mapping = {
                "algorithm_1": "complex",
                "algorithm_2": "simple"
            }
        
        # 获取真实算法名称
        algorithm_data = {
            "set_A": st.session_state.algorithm_mapping.get(
                st.session_state.algorithm_assignment.get("A", "algorithm_1"), 
                "complex"
            ),
            "set_B": st.session_state.algorithm_mapping.get(
                st.session_state.algorithm_assignment.get("B", "algorithm_2"), 
                "simple"
            )
        }
        
        load_dotenv()
        MONGODB_URI = os.getenv('MONGODB_URI')
        client = MongoClient(MONGODB_URI)
        db = client['Organization5']
        user_collection = db['User']
        
        # 准备要保存的数据
        rating_data = {
            "timestamp": datetime.now(),
            "user_info": user_info,
            "algorithm_assignment": algorithm_data,
            "ratings": {
                "set_A": {
                    org_id: {
                        "organization_name": data["org_name"],
                        "score": data["score"],
                        "status": data["status"],
                        "rated_at": data["rated_at"],
                        "algorithm_used": algorithm_data["set_A"],
                        "organization_details": data.get("org_data", {})
                    }
                    for org_id, data in scores_a.items()
                    if data.get("rated", False)
                },
                "set_B": {
                    org_id: {
                        "organization_name": data["org_name"],
                        "score": data["score"],
                        "status": data["status"],
                        "rated_at": data["rated_at"],
                        "algorithm_used": algorithm_data["set_B"],
                        "organization_details": data.get("org_data", {})
                    }
                    for org_id, data in scores_b.items()
                    if data.get("rated", False)
                }
            }
        }
        
        with st.spinner('Saving results...'):
            result = user_collection.insert_one(rating_data)
            return True, result.inserted_id
            
    except Exception as e:
        print(f"MongoDB save error: {str(e)}")
        return False, str(e)
    finally:
        if 'client' in locals():
            client.close()

def save_feedback_to_mongodb(feedback_data, original_data_id):
    """保存用户反馈到MongoDB"""
    try:
        load_dotenv()
        MONGODB_URI = os.getenv('MONGODB_URI')
        client = MongoClient(MONGODB_URI)
        db = client['Organization5']
        user_collection = db['User']
        
        # 更新原有文档，添加用户反馈
        result = user_collection.update_one(
            {"_id": original_data_id},
            {
                "$set": {
                    "user_feedback": feedback_data,
                    "feedback_timestamp": datetime.now()
                }
            }
        )
        
        return True, result.modified_count
    except Exception as e:
        print(f"Error saving feedback: {str(e)}")  # 添加错误日志
        return False, str(e)

def is_profile_complete(profile_data):
    """检查profile是否完整且不包含placeholder文本"""
    required_fields = ["Name", "Type", "Description", "Mission", "Industries", "Specialities"]
    
    # 检查所有必填字段是否存在且不为空
    if not all(profile_data.get(field) and profile_data[field].strip() for field in required_fields):
        return False
        
    # 检查是否仍然是placeholder文本
    if "E.g.," in profile_data["Industries"] or "E.g.," in profile_data["Specialities"]:
        return False
        
    return True

def initialize_session_state():
    """初始化所有session state变量"""
    # 首先确保基础状态变量存在
    if "initialized" not in st.session_state:
        st.session_state.initialized = True
        
    # 直接初始化算法映射，不依赖于其他条件
    if "algorithm_mapping" not in st.session_state:
        st.session_state.algorithm_mapping = {
            "algorithm_1": "complex",
            "algorithm_2": "simple"
        }
    
    # 初始化其他状态变量
    default_states = {
        "matching_locked": False,
        "profile_data": {},
        "search_data": {},
        "results": {},
        "current_set": None,
        "search_performed": False,
        "scores_set_A": {},
        "scores_set_B": {},
        "feedback_submitted": False,
        "show_thank_you": False,
        "algorithm_assignment": {}
    }
    
    for key, value in default_states.items():
        if key not in st.session_state:
            st.session_state[key] = value


def show_introduction():
    # Title
    st.markdown("""
        <div style='text-align: center; padding: 20px;'>
            <h1 style='color: #1f4d7a;'>Welcome to CauseConnect</h1>
            <h3 style='color: #666;'>Organization Partnership Matching Platform</h3>
        </div>
    """, unsafe_allow_html=True)
    
    # Problem Statement
    st.markdown("<h4 style='color: #1f4d7a;'>Problem Statement</h4>", unsafe_allow_html=True)
    st.write("""
        Organizations often struggle to find suitable partners despite the abundance of potential collaborators. 
        Traditional partnership matching methods are time-consuming, heavily reliant on personal networks, 
        and limited by geographical constraints. This creates significant barriers for organizations 
        seeking to expand their impact through strategic partnerships.
    """)
    
    # Our Solution
    st.markdown("<h4 style='color: #1f4d7a;'>Our Solution</h4>", unsafe_allow_html=True)
    st.write("""
        CauseConnect is an innovative project from the University of Washington Information School, 
        designed to revolutionize how organizations find their ideal partnership matches. We have 
        developed a sophisticated matching algorithm that analyzes organizational characteristics, 
        partnership goals, and collaboration potential to recommend the most suitable partners.
    """)
    
    # Research-Backed Design
    st.markdown("<h4 style='color: #1f4d7a;'>Research-Backed Design</h4>", unsafe_allow_html=True)
    st.write("""
        Our matching recommendations are powered by a comprehensive database of over 1,000 organizations, 
        including both non-profits and for-profits primarily from King County, sourced from LinkedIn. 
        Our platform design is informed by:
    """)
    st.markdown("""
        - Interviews with organization leaders about their partnership needs
        - Analysis of successful partnership patterns
        - Study of partnership formation challenges
    """)
    
    # User-Centered Matching Process
    st.markdown("<h4 style='color: #1f4d7a;'>Matching Process</h4>", unsafe_allow_html=True)
    st.write("""
        Our algorithm evaluates organizational compatibility through:
    """)
    st.markdown("""
        - **Mission & Values Alignment:** Matching organizations with similar goals and values
        - **Resource Complementarity:** Identifying mutually beneficial resource sharing opportunities
        - **Partnership Potential:** Calculating match scores based on multiple organizational factors
    """)
    
    # Current Testing Phase
    st.markdown("""
        <div style='background-color: #e8f4f8; padding: 20px; border-radius: 5px; margin-top: 20px;'>
            <h4 style='color: #1f4d7a;'>Current Testing Phase</h4>
            <p>We are currently conducting A/B testing to evaluate and refine our matching algorithms. 
            Your participation will help us validate our approach and improve the accuracy of partnership 
            recommendations. This testing phase is crucial for developing a tool that truly serves 
            the needs of organizations seeking meaningful collaborations.</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Time Commitment
    st.markdown("""
        <div style='background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;'>
            <h4 style='color: #856404; margin: 0;'>⏱️ Time Commitment</h4>
            <p style='margin: 10px 0 0 0;'>This evaluation process takes approximately 20-30 minutes to complete. 
            Please ensure you have sufficient time to provide thoughtful ratings and feedback.</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Testing Process
    st.markdown("<h3 style='color: #1f4d7a;'>Testing Process</h3>", unsafe_allow_html=True)
    st.markdown("""
        - You will receive two sets (Set A and Set B) of potential partner recommendations, each containing 20 organizations
        - Please rate each organization based on how well they match with your organization (1-10)
        - Rating Guide:
            - 1-4: Not a Match
            - 5: Neutral
            - 6-10: Good Match
        - After completing the ratings, please fill out a brief questionnaire to help us improve the algorithm
    """)
    
    # Important Information
    st.markdown("<h3 style='color: #1f4d7a;'>Important Information</h3>", unsafe_allow_html=True)
    st.markdown("""
        - This is an A/B test research project evaluating different matching algorithms
        - Your feedback is crucial for improving our matching system
        - An Amazon gift card will be provided based on the quality and completeness of your feedback
        - For any questions or concerns, please contact: causeconnect7@gmail.com
    """)
    
    # Privacy Statement
    st.markdown("""
        <div style='background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-top: 20px;'>
            <h4 style='color: #1f4d7a;'>Privacy Statement</h4>
            <p>We are committed to protecting your privacy. All information provided will be used solely 
            for research purposes and will not be used for any other commercial purposes.</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Research Project Information
    st.markdown("""
        <div style='background-color: #e8f4f8; padding: 20px; border-radius: 5px; margin-top: 20px;'>
            <h4 style='color: #1f4d7a;'>Research Project Information</h4>
            <p><strong>Important Requirements for Participation:</strong></p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        - You must have prior experience in organizational partnerships or collaborations
        - You must represent a real organization with verifiable information
        - You must be familiar with your organization's partnership goals and needs
        
        Your expertise and real-world experience are essential for the validity of our A/B testing 
        of matching algorithms. Only participants meeting these requirements will be eligible for 
        the Amazon gift card compensation.
    """)
    
    # Confirmation Button
    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if "introduction_confirmed" not in st.session_state:
            st.session_state.introduction_confirmed = False
        if st.button("I understand and want to start the test", type="primary", use_container_width=True):
            st.session_state.introduction_confirmed = True
            st.rerun()

def main():
    # 确保在主函数开始时就初始化所有状态
    initialize_session_state()
    
    # 当切换到Results视图时，确保算法映射存在
    if st.session_state.current_set == "Results":
        if "algorithm_mapping" not in st.session_state:
            st.session_state.algorithm_mapping = {
                "algorithm_1": "complex",
                "algorithm_2": "simple"
            }
    
    # Check if introduction is confirmed
    if not st.session_state.get("introduction_confirmed", False):
        show_introduction()
        return
        
    # 添加提交后的感谢页面状态
    if "show_thank_you" not in st.session_state:
        st.session_state.show_thank_you = False

    # 如果是感谢页面，显示感谢信息并清空数据
    if st.session_state.show_thank_you:
        st.markdown("""
            <div style='text-align: center; padding: 50px; background-color: #f8f9fa; border-radius: 10px;'>
                <h1 style='color: #1f4d7a;'>🎉 Thank You!</h1>
                <p style='font-size: 1.2em; color: #666; margin: 20px 0;'>
                    Thank you for participating in our matching platform evaluation.
                    <br>We will send the Amazon gift card to your email soon!
                </p>
                <p style='color: #666;'>
                    Your feedback helps us improve our platform.
                </p>
            </div>
        """, unsafe_allow_html=True)

        # 添加开始新搜索的按钮
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Start New Search", type="primary", use_container_width=True):
                # 完全清空session state
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        
        # 提前返回，不显示其他内容
        return

    # 显示解锁按钮（如果已锁定）
    if st.session_state.matching_locked:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔓 Unlock to Start New Search", type="secondary", use_container_width=True):
                # 重新初始化session state
                st.session_state.matching_locked = False
                st.session_state.search_performed = False
                st.session_state.current_set = None
                st.session_state.results = {}
                st.session_state.scores_set_A = {}
                st.session_state.scores_set_B = {}
                st.rerun()

    # Profile和Search表单
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
            <div style='background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
                <h2 style='color: #1f4d7a; margin-bottom: 20px; font-size: 24px; font-weight: bold;'>
                    🏢 Organization Profile
                </h2>
                <p style='color: #666; margin-bottom: 30px; font-size: 16px;'>
                    Please tell us about your organization. This information helps us find the best matches for you.
                </p>
            """, unsafe_allow_html=True)
        
        # Profile 表单内容
        org_name = st.text_input(
            "Organization Name",
            value=st.session_state.profile_data.get("Name", ""),
            help="Enter the official name of your organization"
        )
        
        org_type = st.selectbox(
            "Organization Type",
            ["For-Profit", "Non Profit"],
            index=0 if st.session_state.profile_data.get("Type", "") == "For-Profit" else 1,
            help="Select the type that best describes your organization"
        )
        
        org_description = st.text_area(
            "Organization Description",
            value=st.session_state.profile_data.get("Description", ""),
            height=100,
            help="Describe your organization's main activities, values, and goals",
            placeholder="E.g., We are a technology company focused on developing sustainable solutions..."
        )
        
        org_mission = st.text_area(
            "Organization Mission",
            value=st.session_state.profile_data.get("Mission", ""),
            height=75,
            help="What is your organization's core mission and purpose?",
            placeholder="E.g., Our mission is to accelerate the world's transition to sustainable energy..."
        )
        
        org_industries = st.text_input(
            "Industries",
            value=st.session_state.profile_data.get("Industries", ""),
            help="List the main industries your organization operates in (separate with commas)",
            placeholder="E.g., Environmental Services, Education, Waste Management"
        )
        
        org_specialities = st.text_input(
            "Specialities",
            value=st.session_state.profile_data.get("Specialities", ""),
            help="List your organization's key specialties or expertise (separate with commas)",
            placeholder="E.g., Recycling Programs, Environmental Education, Community Engagement"
        )

        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div style='background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
                <h2 style='color: #1f4d7a; margin-bottom: 20px; font-size: 24px; font-weight: bold;'>
                    🔍 Partnership Search
                </h2>
                <p style='color: #666; margin-bottom: 30px; font-size: 16px;'>
                    Tell us about the kind of partnership you're looking for. The more specific you are, 
                    the better we can match you with potential partners.
                </p>
            """, unsafe_allow_html=True)
        
        looking_for = st.selectbox(
            "I'm looking for:",
            ["For-Profit", "Non Profit"],
            index=0 if st.session_state.search_data.get("looking_for", "") == "For-Profit" else 1,
            help="Select the type of organization you want to partner with"
        )
        
        partnership_description = st.text_area(
            "Describe your ideal partnership",
            value=st.session_state.search_data.get("partnership_description", ""),
            height=150,
            help="What are your partnership goals? What kind of resources or capabilities are you looking for?",
            placeholder="E.g., Looking for technology-focused companies that can provide innovative solutions for waste tracking and recycling process optimization..."
        )

        st.markdown('</div>', unsafe_allow_html=True)

    # 搜索按钮（只在未锁定时显示）
    if not st.session_state.matching_locked:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            # 先收集所有输入数据
            profile_data = {
                "Name": org_name.strip(),
                "Type": org_type,
                "Description": org_description.strip(),
                "Mission": org_mission.strip(),
                "Industries": org_industries.strip(),
                "Specialities": org_specialities.strip()
            }
            
            search_data = {
                "looking_for": looking_for,
                "partnership_description": partnership_description.strip()
            }

            if st.button("🔍 Search Matches", key="search_button", use_container_width=True, type="primary"):
                if not is_profile_complete(profile_data):
                    st.error("Please complete all fields in your organization profile with your own information!")
                elif "E.g.," in partnership_description:
                    st.error("Please provide your own partnership description!")
                elif not partnership_description.strip():
                    st.error("Please describe your ideal partnership!")
                else:
                    # 开始新搜索时锁定
                    st.session_state.matching_locked = True
                    
                    # 保存到session state
                    st.session_state.profile_data = profile_data
                    st.session_state.search_data = search_data
                    
                    # 清除之前的搜索结果和评分
                    st.session_state.results = {}
                    st.session_state.scores_set_A = {}
                    st.session_state.scores_set_B = {}
                    st.session_state.current_set = "A"
                    st.session_state.search_performed = True
                    
                    try:
                        # 准备API输入数据
                        input_data = {
                            "Name": profile_data["Name"],
                            "Type": profile_data["Type"],
                            "Description": profile_data["Description"],
                            "Mission": profile_data["Mission"],
                            "Industries": profile_data["Industries"],
                            "Specialities": profile_data["Specialities"],
                            "Organization looking 1": search_data["looking_for"],
                            "Organization looking 2": search_data["partnership_description"]
                        }
                        
                        with st.spinner('Finding matches...'):
                            # 调用API
                            complex_results = call_matching_api(input_data, "complex")
                            simple_results = call_matching_api(input_data, "simple")
                            
                            # 保存结果到session state
                            st.session_state.results = {
                                'A': complex_results,
                                'B': simple_results
                            }
                            st.session_state.current_set = "A"
                            st.session_state.search_performed = True
                            
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error during search: {str(e)}")
                        st.session_state.matching_locked = False

    # 显示匹配结果（无论是否锁定都显示）
    if st.session_state.search_performed and st.session_state.results:
        st.markdown("---")
        
        if st.session_state.current_set == "A":
            st.markdown("""
                <h3 style='color: #1f77b4;'>Set A Matches</h3>
                <div style='margin-bottom: 20px;'>Please rate all organizations in Set A</div>
            """, unsafe_allow_html=True)
            
            display_matches(st.session_state.results['A'], "A")
            
            # 检查Set A是否全部评分完成
            all_rated_a = all(data.get("rated", False) 
                            for data in st.session_state.scores_set_A.values())
            
            st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
            
            if all_rated_a:
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button("Proceed to Set B →", type="primary", use_container_width=True):
                        st.session_state.current_set = "B"
                        st.rerun()
            else:
                st.warning("⚠️ Please rate all organizations in Set A to proceed")

        elif st.session_state.current_set == "B":
            st.markdown("""
                <h3 style='color: #1f77b4;'>Set B Matches</h3>
                <div style='margin-bottom: 20px;'>Please rate all organizations in Set B</div>
            """, unsafe_allow_html=True)
            
            display_matches(st.session_state.results['B'], "B")
            
            # 检查Set B是否全部评分完成
            all_rated_b = all(data.get("rated", False) 
                            for data in st.session_state.scores_set_B.values())
            
            st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
            
            if all_rated_b:
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button("View Final Results →", type="primary", use_container_width=True):
                        st.session_state.current_set = "Results"
                        st.rerun()
            else:
                st.warning("⚠️ Please rate all organizations in Set B to proceed")

        elif st.session_state.current_set == "Results":
            # 第一次进入Results页面时保存评分数据到MongoDB
            if "mongodb_save_id" not in st.session_state:
                user_info = {
                    "organization_name": st.session_state.profile_data["Name"],
                    "organization_type": st.session_state.profile_data["Type"],
                    "mission": st.session_state.profile_data["Mission"],
                    "description": st.session_state.profile_data["Description"],
                    "industries": st.session_state.profile_data["Industries"],
                    "specialities": st.session_state.profile_data["Specialities"],
                    "looking_for": st.session_state.search_data["looking_for"],
                    "partnership_description": st.session_state.search_data["partnership_description"]
                }
                
                success, result = save_to_mongodb(
                    st.session_state.scores_set_A,
                    st.session_state.scores_set_B,
                    user_info
                )
                
                if success:
                    st.session_state.mongodb_save_id = result
                    st.success("✅ Results saved successfully!")
                else:
                    st.error(f"❌ Failed to save results: {result}")

            # 显示用户反馈表单
            st.markdown("""
                <h2 style='color: #1f4d7a; margin-bottom: 30px;'>
                    Functional Test User Experience
                </h2>
            """, unsafe_allow_html=True)
            
            with st.form("feedback_form"):
                # 邮箱输入
                st.markdown("""
                    <h3 style='color: #1f4d7a; margin-bottom: 15px;'>
                        📧 Leave your email for following up gift card!
                    </h3>
                """, unsafe_allow_html=True)
                email = st.text_input("", key="email_input", help="We'll send you an Amazon gift card as a thank you!")
                
                # 问题直观性评分
                st.markdown("### Was the question intuitive and easy to answer?")
                intuitive_score = st.slider(
                    "Rate from 1 (Not as well) to 10 (Very)",
                    1, 10, 5
                )
                
                # Set比较
                st.markdown("### Which set provided more accurate matches?")
                better_set = st.radio(
                    "Choose the set that gave you better matching results:",
                    options=["Set A", "Set B"],
                    help="Select the set that you felt provided more relevant and accurate matches"
                )
                
                # 潜在匹配评分
                st.markdown("### Potential Matches Found")
                potential_matches = st.slider(
                    "Rate from 1 (None) to 10 (Many)",
                    1, 10, 5
                )
                
                # 工作流程改进评分
                st.markdown("### Process Enhancement")
                workflow_enhancement = st.slider(
                    "Does our prototype enhance the matching process compared to your previous workflow?",
                    1, 10, 5,
                    help="1 = Not that Much, 10 = Very"
                )
                
                # 未来使用意向
                st.markdown("### Future Usage")
                will_use = st.radio(
                    "Do you feel our prototype useful and will continue to use it in cause market?",
                    options=["Yes", "No"]
                )
                
                # 提交按钮
                if st.form_submit_button("Submit Feedback"):
                    if not email:
                        st.error("Please enter your email to receive the gift card!")
                    else:
                        feedback_data = {
                            "email": email,
                            "intuitive_score": intuitive_score,
                            "preferred_set": better_set,
                            "potential_matches_score": potential_matches,
                            "workflow_enhancement_score": workflow_enhancement,
                            "will_use_in_future": will_use,
                            "feedback_submitted_at": datetime.now()
                        }
                        
                        if "mongodb_save_id" in st.session_state:
                            success, _ = save_feedback_to_mongodb(feedback_data, st.session_state.mongodb_save_id)
                            if success:
                                # 设置显示感谢页面的标志
                                st.session_state.show_thank_you = True
                                st.rerun()
                            else:
                                st.error("❌ Failed to save feedback. Please try again.")

    # 如果刚刚提交了反馈，显示成功消息并准备新的搜索
    if st.session_state.feedback_submitted:
        st.success("✅ Thank you for completing the evaluation! You can now start a new search.")
        st.session_state.feedback_submitted = False  # 重置标志

    # 显示锁定状态提示
    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
    if st.session_state.matching_locked:
        st.info("🔒 Matching is locked. Please complete the current evaluation process or unlock to start a new search.")

if __name__ == "__main__":
    main() 
