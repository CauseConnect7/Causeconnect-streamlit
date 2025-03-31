from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict
from pymongo import MongoClient
from scipy.spatial.distance import cosine
import numpy as np
from bson.objectid import ObjectId
import openai
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 创建FastAPI应用
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据模型
class CompanyResponse(BaseModel):
    _id: str
    Name: Optional[str] = None
    Description: Optional[str] = None
    Industries: Optional[str] = None
    Specialities: Optional[str] = None
    Staff_Count: Optional[int] = None
    Assets: Optional[float] = None
    Mission: Optional[str] = None
    Narrative: Optional[str] = None
    Tags: Optional[str] = None
    Linkedin_followers: Optional[int] = None
    Popularity: Optional[str] = None
    Contribution: Optional[str] = None
    Partnership: Optional[str] = None
    Event: Optional[str] = None

# MongoDB连接
try:
    client = MongoClient(os.getenv("MONGODB_URI"))
    db = client[os.getenv("MONGODB_DB_NAME")]
    nonprofit_collection = db[os.getenv("MONGODB_COLLECTION_NONPROFIT")]
    forprofit_collection = db[os.getenv("MONGODB_COLLECTION_FORPROFIT")]
    
    # 创建tag_embedding索引
    nonprofit_collection.create_index([("tag_embedding", 1)])
    forprofit_collection.create_index([("tag_embedding", 1)])
except Exception as e:
    print(f"Database connection error: {e}")

@app.post("/test/complete-matching-process")
async def complete_matching_process(request: Dict):
    """整合的匹配流程API"""
    try:
        print("\n=== 开始匹配流程 ===")
        
        # 1. 验证输入
        print("\n1. 验证输入字段")
        required_fields = [
            "Name", 
            "Type", 
            "Description",
            "Mission",
            "Industries",
            "Specialities",
            "Organization looking 1",
            "Organization looking 2"
        ]
        if not all(field in request for field in required_fields):
            print("错误：缺少必要字段")
            raise HTTPException(status_code=400, detail="缺少必要字段")
        print("输入验证成功")

        # 2. 生成理想组织描述
        print("\n2. 生成理想组织描述")
        openai.api_key = os.getenv("OPENAI_API_KEY")
        print("正在调用OpenAI生成理想组织描述...")
        org_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": os.getenv("PROMPT_GEN_ORG_SYSTEM").format(
                    org_type_looking_for=request["Organization looking 1"])},
                {"role": "user", "content": os.getenv("PROMPT_GEN_ORG_USER").format(
                    org_type_looking_for=request["Organization looking 1"],
                    partnership_description=request["Organization looking 2"]
                )}
            ]
        )
        
        ideal_org_description = org_response.choices[0].message['content'].strip()
        print(f"生成的理想组织描述: {ideal_org_description[:100]}...")

        # 新增: 2.5 基于Mission过滤组织
        print("\n2.5 基于Mission过滤组织")
        filter_response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": os.getenv("PROMPT_FILTER_SYSTEM")},
                {"role": "user", "content": os.getenv("PROMPT_FILTER_USER").format(
                    organization_mission=request["Mission"],
                    generated_organizations=ideal_org_description
                )}
            ]
        )

        filtered_org_description = filter_response.choices[0].message['content'].strip()
        print(f"过滤后的组织描述: {filtered_org_description[:100]}...")

        # 3. 生成标签
        print("\n3. 生成标签")
        print("正在调用OpenAI生成标签...")
        tags_response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": os.getenv("PROMPT_TAGS_SYSTEM").format(
                    total_tags=30, steps=6, tags_per_step=5)},
                {"role": "user", "content": os.getenv("PROMPT_TAGS_USER").format(
                    total_tags=30, description=filtered_org_description)}
            ]
        )
        
        tags = tags_response.choices[0].message['content'].strip()
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()][:30]
        tags_string = ", ".join(tag_list)
        print(f"生成的标签: {tags_string}")

        # 5. 生成标签嵌入向量
        print("\n5. 生成标签嵌入向量")
        print("正在调用OpenAI生成嵌入向量...")
        embedding_response = openai.Embedding.create(
            model="text-embedding-ada-002",
            input=tags_string
        )
        
        tag_embedding = embedding_response["data"][0]["embedding"]
        print(f"嵌入向量维度: {len(tag_embedding)}")

        # 6. 查找匹配
        print("\n6. 查找匹配")
        matches = []
        collection = nonprofit_collection if request["Organization looking 1"].strip().lower() in ["non profit", "nonprofit"] else forprofit_collection
        print(f"使用集合: {collection.name}")
        
        print("正在查询数据库中的匹配项...")
        query_count = 0
        for org in collection.find({"tag_embedding": {"$exists": True}}):
            query_count += 1
            if org.get("tag_embedding"):
                try:
                    # 直接使用 np.frombuffer 处理二进制数据，不需要其他转换
                    org_embedding = np.frombuffer(org["tag_embedding"], dtype=np.float32)
                    # 直接计算余弦相似度，不需要预处理向量
                    similarity = float(1 - cosine(tag_embedding, org_embedding))
                    
                    match_result = {
                        "similarity_score": similarity,
                        "organization": {
                            "_id": str(org["_id"]),
                            "Name": org.get("Name", ""),
                            "Description": org.get("Description", ""),
                            "Industries": org.get("Industries", []),
                            "Specialities": org.get("Specialities", []),
                            "Staff_Count": org.get("Staff_Count", ""),
                            "Assets": org.get("Assets", ""),
                            "Mission": org.get("Mission", ""),
                            "Narrative": org.get("Narrative", ""),
                            "Tags": org.get("Tags", []),
                            "Linkedin_followers": org.get("Linkedin_followers", ""),
                            "Popularity": org.get("Popularity", ""),
                            "Partnership": org.get("Partnership", ""),
                            "Event": org.get("Event", "")
                        }
                    }
                    matches.append(match_result)
                except Exception as e:
                    print(f"处理组织 {org.get('_id')} 时出错: {str(e)}")
                    print(f"错误类型: {type(e)}")
                    print(f"组织tag_embedding类型: {type(org.get('tag_embedding'))}")
                    if isinstance(org.get("tag_embedding"), bytes):
                        print(f"组织tag_embedding长度: {len(org.get('tag_embedding'))}")
                    continue

        print(f"共处理 {query_count} 个组织，找到 {len(matches)} 个匹配项")

        # 7. 排序和评估匹配项
        print("\n7. 排序和评估匹配项")
        matches.sort(key=lambda x: x["similarity_score"], reverse=True)
        top_100_matches = matches[:100]
        first_thirty = top_100_matches[:30]  # 改为30个
        remaining_matches = top_100_matches[30:]  # 从第31个开始的剩余匹配
        print(f"前100个匹配项中，选择前30个进行评估")

        # 评估前30个匹配
        print("\n8. 评估匹配项")
        evaluated_matches = []  # 存储评估为 true 的匹配项
        rejected_matches = []   # 存储评估为 false 的匹配项
        for idx, match in enumerate(first_thirty):
            print(f"评估第 {idx+1}/30 个匹配项...")
            
            # 准备资源信息
            match_resources = ""
            if request["Organization looking 1"].lower() == "nonprofit":
                match_resources = f"Partnership History: {match['organization'].get('Partnership', '')}, Event Experience: {match['organization'].get('Event', '')}"
            else:
                match_resources = f"Assets: {match['organization'].get('Assets', '')}, Contribution Capacity: {match['organization'].get('Contribution', '')}"

            # 评估匹配
            evaluation_prompt = os.getenv("MATCH_EVALUATION_PROMPT").format(
                # 用户组织信息
                user_description=request["Description"],
                user_mission=request["Mission"],
                user_industries=request["Industries"],
                user_specialities=request["Specialities"],
                
                # 匹配组织信息
                match_description=match["organization"]["Description"],
                match_mission=match["organization"]["Mission"],
                match_industries=match["organization"]["Industries"],
                match_specialties=match["organization"]["Specialities"],
                
                # 资源信息
                match_resources=match_resources,
                match_partnership=match["organization"].get("Partnership", ""),
                match_event=match["organization"].get("Event", ""),
                match_contribution=match["organization"].get("Contribution", ""),
                match_assets=match["organization"].get("Assets", "")
            )

            eval_response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": os.getenv("MATCH_EVALUATION_SYSTEM_PROMPT")},
                    {"role": "user", "content": evaluation_prompt}
                ],
                temperature=0.3
            )

            is_match = eval_response.choices[0].message['content'].strip().lower() == 'true'
            if is_match:
                match["evaluation"] = {
                    "is_match": True, 
                    "status": "accepted"
                }
                evaluated_matches.append(match)
                print(f"匹配项 {idx+1} 评估为匹配")
            else:
                match["evaluation"] = {
                    "is_match": False, 
                    "status": "rejected"
                }
                rejected_matches.append(match)
                print(f"匹配项 {idx+1} 评估为不匹配")

        # 选择最终的20个匹配
        print("\n9. 选择最终匹配")
        final_matches = []
        supplementary_matches = []

        # 首先添加评估为true的匹配，但不超过20个
        if len(evaluated_matches) >= 20:
            final_matches = evaluated_matches[:20]  # 如果accepted超过20个，只取前20个
            print("从已接受的匹配中选择前20个")
        else:
            # 如果accepted不够20个，需要补充
            final_matches = evaluated_matches.copy()
            remaining_needed = 20 - len(final_matches)
            print(f"需要从剩余匹配项中补充 {remaining_needed} 个")
            for match in remaining_matches[:remaining_needed]:
                match["evaluation"] = {"is_match": None, "status": "supplementary"}
                supplementary_matches.append(match)
            final_matches.extend(supplementary_matches)

        print("\n10. 构建响应")
        def sanitize_float(value):
            """确保浮点数是JSON兼容的"""
            if isinstance(value, (int, float)):
                if np.isnan(value) or np.isinf(value):
                    return 0.0
                return float(value)
            return 0.0

        def sanitize_organization_data(org_data):
            """清理组织数据确保JSON兼容"""
            return {
                "id": str(org_data["_id"]),
                "name": str(org_data.get("Name", "")),
                "description": str(org_data.get("Description", "")),
                "mission": str(org_data.get("Mission", "")),
                "industries": org_data.get("Industries", []),
                "specialities": org_data.get("Specialities", []),
                "staff_count": int(org_data.get("Staff_Count", 0)),
                "assets": sanitize_float(org_data.get("Assets", 0.0)),
                "narrative": str(org_data.get("Narrative", "")),
                "tags": org_data.get("Tags", []),
                "linkedin_followers": int(org_data.get("Linkedin_followers", 0)),
                "popularity": str(org_data.get("Popularity", "")),
                "contribution": str(org_data.get("Contribution", "")),
                "partnership": str(org_data.get("Partnership", "")),
                "event": str(org_data.get("Event", ""))
            }

        # 在返回响应前修改
        sanitized_matches = []
        for match in final_matches:
            sanitized_match = {
                "similarity_score": sanitize_float(match["similarity_score"]),
                "evaluation_status": match["evaluation"]["status"],
                "organization": sanitize_organization_data(match["organization"])
            }
            sanitized_matches.append(sanitized_match)

        response = {
            "status": "success",
            "process_steps": {
                "step1_input_organization": {
                    "name": str(request["Name"]),
                    "type": str(request["Type"]),
                    "description": str(request["Description"]),
                    "mission": str(request["Mission"]),
                    "industries": request["Industries"],
                    "specialities": request["Specialities"],
                    "looking_for": str(request["Organization looking 1"]),
                    "partnership_description": str(request["Organization looking 2"])
                },
                "step2_ideal_organization": {
                    "description": str(ideal_org_description)
                },
                "step3_generated_tags": {
                    "tags": tag_list,
                    "tags_string": str(tags_string)
                },
                "step4_embedding": {
                    "dimension": int(len(tag_embedding))
                },
                "step5_matches": {
                    "total_matches_found": int(len(matches)),
                    "evaluation_summary": {
                        "total_evaluated": int(len(first_thirty)),
                        "accepted": int(len(evaluated_matches)),
                        "rejected": int(len(rejected_matches)),
                        "supplementary": int(len(supplementary_matches)),
                        "final_output": 20
                    }
                }
            },
            "matching_results": sanitized_matches
        }
        
        print("\n=== 匹配流程完成 ===")
        return response

    except Exception as e:
        print(f"\n错误: {str(e)}")
        print(f"错误类型: {type(e)}")
        import traceback
        print(f"错误追踪:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500, 
            detail={
                "error": str(e),
                "step": "complete_matching_process",
                "message": "匹配过程出错"
            }
        )

@app.post("/test/complete-matching-process-simple")
async def complete_matching_process_simple(request: Dict):
    """简化版匹配流程API - 保持与完整版相同的返回结构"""
    try:
        print("\n=== 开始简化匹配流程 ===")
        
        # 1. 验证输入
        print("\n1. 验证输入字段")
        required_fields = [
            "Name", 
            "Type", 
            "Description",
            "Mission",
            "Industries",
            "Specialities",
            "Organization looking 1",
            "Organization looking 2"
        ]
        if not all(field in request for field in required_fields):
            raise HTTPException(status_code=400, detail="缺少必要字段")
        print("输入验证成功")

        # 2. 直接为 looking for 2 生成嵌入向量
        print("\n2. 生成嵌入向量")
        openai.api_key = os.getenv("OPENAI_API_KEY")
        embedding_response = openai.Embedding.create(
            model="text-embedding-ada-002",
            input=request["Organization looking 2"]
        )
        
        description_embedding = embedding_response["data"][0]["embedding"]

        # 3. 查找匹配
        print("\n3. 查找匹配")
        matches = []
        collection = nonprofit_collection if request["Organization looking 1"].strip().lower() in ["non profit", "nonprofit"] else forprofit_collection
        print(f"使用集合: {collection.name}")
        
        print("正在查询数据库中的匹配项...")
        query_count = 0
        for org in collection.find({"description_embedding": {"$exists": True}}):
            query_count += 1
            if org.get("description_embedding"):
                try:
                    org_embedding = np.frombuffer(org["description_embedding"], dtype=np.float32)
                    similarity = float(1 - cosine(description_embedding, org_embedding))
                    
                    match_result = {
                        "similarity_score": similarity,
                        "organization": {
                            "_id": str(org["_id"]),
                            "Name": org.get("Name", ""),
                            "Description": org.get("Description", ""),
                            "Industries": org.get("Industries", []),
                            "Specialities": org.get("Specialities", []),
                            "Staff_Count": org.get("Staff_Count", ""),
                            "Assets": org.get("Assets", ""),
                            "Mission": org.get("Mission", ""),
                            "Narrative": org.get("Narrative", ""),
                            "Tags": org.get("Tags", []),
                            "Linkedin_followers": org.get("Linkedin_followers", ""),
                            "Popularity": org.get("Popularity", ""),
                            "Partnership": org.get("Partnership", ""),
                            "Event": org.get("Event", "")
                        }
                    }
                    matches.append(match_result)
                except Exception as e:
                    print(f"处理组织 {org.get('_id')} 时出错: {str(e)}")
                    continue

        print(f"共处理 {query_count} 个组织，找到 {len(matches)} 个匹配项")

        # 4. 按相似度排序并返回前20个
        print("\n4. 排序并选择前20个匹配项")
        matches.sort(key=lambda x: x["similarity_score"], reverse=True)
        top_twenty = matches[:20]

        # 5. 使用与完整流程相同的数据清理函数
        def sanitize_float(value):
            """确保浮点数是JSON兼容的"""
            if isinstance(value, (int, float)):
                if np.isnan(value) or np.isinf(value):
                    return 0.0
                return float(value)
            return 0.0

        def sanitize_organization_data(org_data):
            """清理组织数据确保JSON兼容"""
            return {
                "id": str(org_data["_id"]),
                "name": str(org_data.get("Name", "")),
                "description": str(org_data.get("Description", "")),
                "mission": str(org_data.get("Mission", "")),
                "industries": org_data.get("Industries", []),
                "specialities": org_data.get("Specialities", []),
                "staff_count": int(org_data.get("Staff_Count", 0)),
                "assets": sanitize_float(org_data.get("Assets", 0.0)),
                "narrative": str(org_data.get("Narrative", "")),
                "tags": org_data.get("Tags", []),
                "linkedin_followers": int(org_data.get("Linkedin_followers", 0)),
                "popularity": str(org_data.get("Popularity", "")),
                "contribution": str(org_data.get("Contribution", "")),
                "partnership": str(org_data.get("Partnership", "")),
                "event": str(org_data.get("Event", ""))
            }

        # 清理匹配结果
        sanitized_matches = []
        for match in top_twenty:
            sanitized_match = {
                "similarity_score": sanitize_float(match["similarity_score"]),
                "evaluation_status": "simple_match",
                "organization": sanitize_organization_data(match["organization"])
            }
            sanitized_matches.append(sanitized_match)

        # 构建新的响应结构，与完整版保持一致
        response = {
            "status": "success",
            "process_steps": {
                "step1_input_organization": {
                    "name": str(request["Name"]),
                    "type": str(request["Type"]),
                    "description": str(request["Description"]),
                    "mission": str(request["Mission"]),
                    "industries": request["Industries"],
                    "specialities": request["Specialities"],
                    "looking_for": str(request["Organization looking 1"]),
                    "partnership_description": str(request["Organization looking 2"])
                },
                "step2_ideal_organization": {
                    "description": None  # 简化版不生成理想组织
                },
                "step3_generated_tags": {
                    "tags": [],          # 简化版不生成标签
                    "tags_string": ""
                },
                "step4_embedding": {
                    "dimension": int(len(description_embedding))
                },
                "step5_matches": {       # 改为与完整版相同的键名
                    "total_matches_found": int(len(matches)),
                    "evaluation_summary": {
                        "total_evaluated": 20,  # 设为20因为我们直接返回前20个
                        "accepted": 20,         # 简化版将所有返回的匹配视为已接受
                        "rejected": 0,
                        "supplementary": 0,
                        "final_output": 20
                    }
                }
            },
            "matching_results": sanitized_matches
        }
        
        print("\n=== 简化匹配流程完成 ===")
        return response

    except Exception as e:
        print(f"\n错误: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "step": "complete_matching_process_simple",
                "message": "匹配过程出错"
            }
        )

# 检查必要的环境变量
required_env_vars = [
    "OPENAI_API_KEY",
    "MONGODB_URI",
    "MONGODB_DB_NAME",
    "MONGODB_COLLECTION_NONPROFIT",
    "MONGODB_COLLECTION_FORPROFIT",
    "PROMPT_GEN_ORG_SYSTEM",
    "PROMPT_GEN_ORG_USER",
    "PROMPT_TAGS_SYSTEM",
    "PROMPT_TAGS_USER",
    "MATCH_EVALUATION_SYSTEM_PROMPT",
    "MATCH_EVALUATION_PROMPT"
]

missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")
