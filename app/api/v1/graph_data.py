# app/api/v1/graph_data.py
"""
为GraphRAG Visualizer提供Neo4j数据的API端点
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.models.user_model import User
from app.data_access.graph_db import graph_db


class Neo4jNodeResponse(BaseModel):
    identity: str
    labels: List[str]
    properties: Dict[str, Any]


class Neo4jRelationshipResponse(BaseModel):
    identity: str
    start: str
    end: str
    type: str
    properties: Dict[str, Any]


class Neo4jGraphDataResponse(BaseModel):
    nodes: List[Neo4jNodeResponse]
    relationships: List[Neo4jRelationshipResponse]


router = APIRouter()


@router.get("/graph/neo4j-data", response_model=Neo4jGraphDataResponse)
async def get_neo4j_data_for_visualizer(
    limit: int = 5000,
    current_user: User = Depends(get_current_user)
):
    """
    获取Neo4j图数据用于GraphRAG Visualizer
    
    参数:
    - limit: 返回的最大记录数（默认 5000）
    """
    try:
        print(f"正在从 Neo4j 获取数据，限制: {limit}")
        
        # 第一步：获取所有节点
        nodes_query = """
        MATCH (n)
        RETURN n
        LIMIT $limit
        """
        
        nodes_records = await graph_db.execute_query(nodes_query, {"limit": limit})
        print(f"收到 {len(nodes_records)} 个节点")
        
        # 收集所有节点
        nodes_dict = {}
        for record in nodes_records:
            try:
                node = record["n"]
                if node is not None:
                    node_id = str(node.element_id) if hasattr(node, 'element_id') else str(id(node))
                    nodes_dict[node_id] = Neo4jNodeResponse(
                        identity=node_id,
                        labels=list(node.labels) if hasattr(node, 'labels') else [],
                        properties=dict(node) if hasattr(node, '__iter__') else {}
                    )
            except Exception as e:
                print(f"处理节点时出错: {e}")
        
        print(f"已收集 {len(nodes_dict)} 个节点")
        
        # 第二步：获取所有关系
        relationships_query = """
        MATCH (n)-[r]->(m)
        RETURN n, r, m
        LIMIT $limit
        """
        
        records = await graph_db.execute_query(relationships_query, {"limit": limit})
        print(f"收到 {len(records)} 条关系记录")
        
        # 收集关系
        relationships_list = []
        
        for record in records:
            try:
                relationship = record["r"]
                if relationship is not None:
                    rel_id = str(relationship.element_id) if hasattr(relationship, 'element_id') else str(id(relationship))
                    start_node_id = str(relationship.start_node.element_id) if hasattr(relationship.start_node, 'element_id') else str(id(relationship.start_node))
                    end_node_id = str(relationship.end_node.element_id) if hasattr(relationship.end_node, 'element_id') else str(id(relationship.end_node))
                    
                    relationships_list.append(Neo4jRelationshipResponse(
                        identity=rel_id,
                        start=start_node_id,
                        end=end_node_id,
                        type=relationship.type if hasattr(relationship, 'type') else "UNKNOWN",
                        properties=dict(relationship) if hasattr(relationship, '__iter__') else {}
                    ))
            except Exception as e:
                print(f"处理关系时出错: {e}")
        
        print(f"最终结果 - {len(nodes_dict)} 个节点, {len(relationships_list)} 个关系")
        
        return Neo4jGraphDataResponse(
            nodes=list(nodes_dict.values()),
            relationships=relationships_list
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Neo4j数据失败: {str(e)}")