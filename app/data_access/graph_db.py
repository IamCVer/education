# app/data_access/graph_db.py (最终修正版)
"""
封装所有与Neo4j图数据库的交互逻辑。
"""
from typing import List, Dict, Any
from neo4j import AsyncGraphDatabase, Record
from neo4j.graph import Node, Relationship
from app.core.config import settings


class GraphDB:
    """
    用于与Neo4j数据库交互的单例类。
    """

    def __init__(self):
        self.driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )

    async def close(self):
        """关闭数据库驱动连接"""
        await self.driver.close()

    async def execute_query(self, query: str, params: Dict[str, Any] = None) -> List[Record]:
        """
        执行一个只读的Cypher查询并返回原始的Record列表。
        """
        params = params or {}
        try:
            async with self.driver.session() as session:
                result = await session.run(query, params)
                records = []
                async for record in result:
                    records.append(record)
                return records
        except Exception as e:
            print(f"Error executing Cypher query: {e}")
            return []

    async def get_neighborhood(self, node_ids: List[str], hops: int = 1) -> str:
        """
        获取指定入口点节点周围的局部图谱信息，并序列化为文本。
        """
        query = """
        MATCH (startNode)
        WHERE startNode.id IN $node_ids
        CALL apoc.path.subgraphAll(startNode, {maxLevel: $hops})
        YIELD nodes, relationships
        RETURN nodes, relationships
        """
        params = {"node_ids": node_ids, "hops": hops}
        results = await self.execute_query(query, params)

        if not results or not results[0]["nodes"]:
            return "在知识图谱中未找到相关信息。"

        context_str = "知识图谱上下文:\n"
        nodes_context = []
        seen_nodes = set()

        # vvvvvvvvvvvv 核心修正：健壮地处理节点和关系 vvvvvvvvvvvv
        for record in results:
            for node in record.get("nodes", []):
                if node.element_id not in seen_nodes:
                    # 使用dict()可以安全地将Node对象的所有属性转换为字典
                    node_props = dict(node)
                    nodes_context.append(f" - 节点: {node_props}")
                    seen_nodes.add(node.element_id)

        relationships_context = []
        seen_rels = set()
        for record in results:
            for rel in record.get("relationships", []):
                if rel.element_id not in seen_rels:
                    start_node_props = dict(rel.start_node)
                    end_node_props = dict(rel.end_node)
                    relationships_context.append(
                        f" - 关系: ({start_node_props.get('name')})-[{rel.type}]->({end_node_props.get('name')})"
                    )
                    seen_rels.add(rel.element_id)
        # ^^^^^^^^^^^^ 核心修正结束 ^^^^^^^^^^^^

        context_str += "节点信息:\n" + "\n".join(nodes_context) + "\n"
        context_str += "关系信息:\n" + "\n".join(relationships_context)

        return context_str


graph_db = GraphDB()