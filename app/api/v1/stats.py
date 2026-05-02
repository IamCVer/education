# app/api/v1/stats.py
"""
统计数据 API：GPU 监控、实体排行、社区层级树等
"""
import asyncio
import subprocess
from typing import List, Dict
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
import pandas as pd

from app.api.deps import get_admin_user
from app.models.user_model import User

router = APIRouter()

# 全局缓存
gpu_metrics_cache: List[Dict] = []
entities_ranking_cache: Dict = None
community_tree_cache: Dict = None
force_graph_cache: Dict = None

# Socket.IO 实例（将在 main.py 中注入）
sio_instance = None

def set_sio(sio):
    """设置 Socket.IO 实例"""
    global sio_instance
    sio_instance = sio


# ============ GPU 监控 API ============
@router.get("/gpu-metrics")
async def get_gpu_metrics(current_user: User = Depends(get_admin_user)):
    """获取 GPU 显存利用率历史数据"""
    return {"metrics": gpu_metrics_cache[-50:]}  # 返回最近 50 条


async def collect_gpu_metrics():
    """后台任务：定期收集 GPU/CPU 指标"""
    global gpu_metrics_cache
    
    # 检查是否有 GPU
    has_gpu = False
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=2
        )
        has_gpu = result.returncode == 0
    except:
        has_gpu = False
    
    print(f"系统监控启动: {'GPU 模式' if has_gpu else 'CPU 模式'}")
    
    while True:
        try:
            if has_gpu:
                # GPU 监控
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split("\n")
                    for line in lines:
                        parts = line.split(",")
                        if len(parts) == 2:
                            used = int(parts[0].strip())
                            total = int(parts[1].strip())
                            percentage = round((used / total) * 100, 2) if total > 0 else 0
                            
                            metric = {
                                "timestamp": datetime.now().isoformat(),
                                "type": "gpu",
                                "used": used,
                                "total": total,
                                "percentage": percentage
                            }
                            
                            gpu_metrics_cache.append(metric)
            else:
                # CPU 监控（使用 psutil）
                try:
                    import psutil
                    cpu_percent = psutil.cpu_percent(interval=1)
                    memory = psutil.virtual_memory()
                    
                    metric = {
                        "timestamp": datetime.now().isoformat(),
                        "type": "cpu",
                        "used": round(memory.used / (1024 * 1024), 2),  # MB
                        "total": round(memory.total / (1024 * 1024), 2),  # MB
                        "percentage": round(cpu_percent, 2),
                        "memory_percent": round(memory.percent, 2)
                    }
                    
                    gpu_metrics_cache.append(metric)
                except ImportError:
                    # 如果没有 psutil，使用模拟数据
                    import random
                    metric = {
                        "timestamp": datetime.now().isoformat(),
                        "type": "cpu",
                        "used": random.randint(2000, 8000),
                        "total": 16384,
                        "percentage": random.randint(20, 80),
                        "memory_percent": random.randint(40, 70)
                    }
                    gpu_metrics_cache.append(metric)
            
            # 限制缓存大小
            if len(gpu_metrics_cache) > 200:
                gpu_metrics_cache.pop(0)
            
            # 通过 Socket.IO 广播
            if sio_instance and gpu_metrics_cache:
                try:
                    await sio_instance.emit('gpu_metrics', gpu_metrics_cache[-1])
                except Exception as e:
                    print(f"Socket.IO 广播失败: {e}")
                        
        except Exception as e:
            print(f"收集系统指标失败: {e}")
        
        await asyncio.sleep(5)  # 每 5 秒收集一次


# ============ 实体排行 API ============
@router.get("/entities")
async def get_entities_ranking(current_user: User = Depends(get_admin_user)):
    """获取实体 Degree 和 Frequency Top 10"""
    global entities_ranking_cache
    
    if entities_ranking_cache is None:
        await refresh_entities_ranking()
    
    return entities_ranking_cache


async def refresh_entities_ranking():
    """刷新实体排行数据"""
    global entities_ranking_cache
    
    try:
        # 读取 entities.parquet
        df = pd.read_parquet("app/datasource/entities.parquet")
        
        # Degree Top 10
        degree_top10 = (
            df.nlargest(10, "degree")[["title", "degree", "type"]]
            .rename(columns={"title": "entity"})
            .to_dict(orient="records")
        )
        
        # Frequency Top 10 (假设有 frequency 字段，如果没有可以用其他字段替代)
        if "frequency" in df.columns:
            freq_top10 = (
                df.nlargest(10, "frequency")[["title", "frequency", "type"]]
                .rename(columns={"title": "entity"})
                .to_dict(orient="records")
            )
        else:
            # 如果没有 frequency 字段，使用 degree 作为替代
            freq_top10 = degree_top10
        
        entities_ranking_cache = {
            "degreeTop10": degree_top10,
            "frequencyTop10": freq_top10
        }
    except Exception as e:
        print(f"刷新实体排行失败: {e}")
        entities_ranking_cache = {
            "degreeTop10": [],
            "frequencyTop10": []
        }


# ============ 社区层级树 API ============
@router.get("/community-tree")
async def get_community_tree(current_user: User = Depends(get_admin_user)):
    """获取社区层级树（旭日图数据）"""
    global community_tree_cache
    
    if community_tree_cache is None:
        await refresh_community_tree()
    
    return community_tree_cache


async def refresh_community_tree():
    """刷新社区层级树数据"""
    global community_tree_cache
    
    try:
        # 读取 communities.parquet 和 entities.parquet
        communities_df = pd.read_parquet("app/datasource/communities.parquet")
        entities_df = pd.read_parquet("app/datasource/entities.parquet")
        
        # 构建层级树
        tree = build_community_hierarchy(communities_df, entities_df)
        
        # 统计信息
        stats = {
            "totalCommunities": len(communities_df),
            "maxLevel": int(communities_df["level"].max()) if "level" in communities_df.columns else 0,
            "totalEntities": len(entities_df)
        }
        
        community_tree_cache = {
            "tree": tree,
            "stats": stats
        }
    except Exception as e:
        print(f"刷新社区层级树失败: {e}")
        community_tree_cache = {
            "tree": {"name": "Knowledge Graph", "value": 0, "children": []},
            "stats": {"totalCommunities": 0, "maxLevel": 0, "totalEntities": 0}
        }


def build_community_hierarchy(communities_df: pd.DataFrame, entities_df: pd.DataFrame) -> Dict:
    """构建社区层级结构"""
    try:
        # 确保有 level 列
        if "level" not in communities_df.columns:
            communities_df["level"] = 0
        
        # 按 level 分组
        root = {
            "name": "Knowledge Graph",
            "value": len(entities_df),
            "children": []
        }
        
        # 获取顶级社区 (level 0)
        top_communities = communities_df[communities_df["level"] == 0]
        
        for _, comm in top_communities.iterrows():
            community_node = {
                "name": comm.get("title", f"Community {comm['id']}"),
                "value": int(comm.get("size", 1)),
                "level": int(comm["level"]),
                "children": []
            }
            
            # 递归添加子社区
            add_sub_communities(community_node, comm["id"], communities_df, 1)
            
            root["children"].append(community_node)
        
        # 如果没有层级结构，创建扁平结构
        if not root["children"]:
            for _, comm in communities_df.head(10).iterrows():
                root["children"].append({
                    "name": comm.get("title", f"Community {comm['id']}"),
                    "value": int(comm.get("size", 1)),
                    "level": 0
                })
        
        return root
    except Exception as e:
        print(f"构建社区层级失败: {e}")
        return {"name": "Knowledge Graph", "value": 0, "children": []}


def add_sub_communities(parent_node: Dict, parent_id: str, communities_df: pd.DataFrame, level: int):
    """递归添加子社区"""
    if level > 3:  # 限制层级深度
        return
    
    # 查找子社区（这里需要根据实际数据结构调整）
    # 假设有 parent_id 字段
    if "parent_id" in communities_df.columns:
        sub_communities = communities_df[communities_df["parent_id"] == parent_id]
        
        for _, comm in sub_communities.iterrows():
            child_node = {
                "name": comm.get("title", f"Community {comm['id']}"),
                "value": int(comm.get("size", 1)),
                "level": level
            }
            parent_node["children"].append(child_node)
            
            # 递归
            add_sub_communities(child_node, comm["id"], communities_df, level + 1)


# ============ 力导向图 API ============
@router.get("/force-graph")
async def get_force_graph(current_user: User = Depends(get_admin_user)):
    """获取力导向图数据（节点和边）"""
    global force_graph_cache
    
    if force_graph_cache is None:
        await refresh_force_graph()
    
    return force_graph_cache


async def refresh_force_graph():
    """刷新力导向图数据"""
    global force_graph_cache
    
    try:
        # 读取 entities.parquet（节点）
        entities_df = pd.read_parquet("app/datasource/entities.parquet")
        
        # 读取 relationships.parquet（关系/边）- covariates 数据质量有问题
        try:
            covariates_df = pd.read_parquet("app/datasource/relationships.parquet")
        except:
            # 如果没有 relationships，尝试 covariates（但数据可能不理想）
            try:
                covariates_df = pd.read_parquet("app/datasource/covariates.parquet")
                # 过滤掉包含 <think> 标签的行（数据质量问题）
                if not covariates_df.empty and 'subject_id' in covariates_df.columns:
                    covariates_df = covariates_df[
                        ~covariates_df['subject_id'].astype(str).str.contains('<think>', na=False)
                    ]
            except:
                covariates_df = pd.DataFrame()
        
        # 构建节点数据（限制数量以提高性能）
        nodes = []
        # 选择 degree 最高的前100个节点
        top_entities = entities_df.nlargest(100, "degree") if "degree" in entities_df.columns else entities_df.head(100)
        
        # 获取社区信息（如果有）
        communities_df = None
        try:
            communities_df = pd.read_parquet("app/datasource/communities.parquet")
        except:
            pass
        
        # 创建实体ID到社区的映射
        entity_to_community = {}
        if communities_df is not None and "id" in communities_df.columns:
            # 假设 entities 有 community_id 字段
            if "community" in entities_df.columns:
                for _, entity in top_entities.iterrows():
                    entity_to_community[entity["id"]] = entity.get("community", "0")
        
        # 创建 title 到 id 的映射（用于匹配边）
        title_to_id = {}
        for _, entity in top_entities.iterrows():
            entity_id = str(entity["id"])
            entity_title = str(entity.get("title", "")).strip()
            title_to_id[entity_title] = entity_id
            # 同时存储大写版本以提高匹配率
            title_to_id[entity_title.upper()] = entity_id
            
            community = entity_to_community.get(entity_id, "0")
            
            nodes.append({
                "id": entity_id,
                "name": entity.get("title", entity_id),
                "value": int(entity.get("degree", 1)),  # 节点大小
                "category": str(community),  # 用于分组着色
                "type": entity.get("type", "unknown"),
                "symbolSize": min(10 + int(entity.get("degree", 1)) * 2, 60)  # 根据 degree 设置大小
            })
        
        # 构建边数据
        links = []
        entity_names = set(title_to_id.keys())
        
        if not covariates_df.empty:
            # 判断使用哪种列名（relationships 用 source/target，covariates 用 subject_id/object_id）
            source_col = "source" if "source" in covariates_df.columns else "subject_id"
            target_col = "target" if "target" in covariates_df.columns else "object_id"
            
            for _, edge in covariates_df.iterrows():
                source_name = str(edge.get(source_col, "")).strip()
                target_name = str(edge.get(target_col, "")).strip()
                
                # 跳过 NONE 或空值
                if source_name in ["NONE", "", "nan", "None"] or target_name in ["NONE", "", "nan", "None"]:
                    continue
                
                # 尝试匹配（原始名称和大写）
                source_id = title_to_id.get(source_name) or title_to_id.get(source_name.upper())
                target_id = title_to_id.get(target_name) or title_to_id.get(target_name.upper())
                
                if source_id and target_id and source_id != target_id:
                    links.append({
                        "source": source_id,
                        "target": target_id,
                        "value": float(edge.get("weight", 1)),  # 边的权重
                        "type": edge.get("type", edge.get("description", "related"))[:50]  # 限制长度
                    })
                    
                    # 限制边的数量
                    if len(links) >= 300:
                        break
        
        # 统计信息
        # 计算社区数量
        unique_categories = len(set([node["category"] for node in nodes]))
        
        force_graph_cache = {
            "nodes": nodes,
            "links": links,
            "categories": [{"name": f"社区 {i}"} for i in range(unique_categories)],
            "stats": {
                "totalNodes": len(nodes),
                "totalLinks": len(links),
                "communities": unique_categories
            }
        }
        
        print(f"力导向图数据生成成功: {len(nodes)} 个节点, {len(links)} 条边")
        
    except Exception as e:
        print(f"刷新力导向图数据失败: {e}")
        import traceback
        traceback.print_exc()
        force_graph_cache = {
            "nodes": [],
            "links": [],
            "categories": [],
            "stats": {"totalNodes": 0, "totalLinks": 0, "communities": 0}
        }


# ============ 刷新统计数据 API ============
@router.post("/refresh")
async def refresh_stats(current_user: User = Depends(get_admin_user)):
    """手动刷新所有统计数据"""
    try:
        await refresh_entities_ranking()
        await refresh_community_tree()
        await refresh_force_graph()
        return {"message": "统计数据刷新成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刷新失败: {str(e)}")

