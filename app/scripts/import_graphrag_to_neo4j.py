"""
将 GraphRAG 数据导入到 Neo4j 数据库的脚本
"""
import os
import sys
import asyncio
import pandas as pd
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from neo4j import AsyncGraphDatabase
from app.core.config import settings


class GraphRAGImporter:
    """GraphRAG 数据导入器"""

    def __init__(self):
        # 获取环境变量，如果没有则使用默认值
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://db_neo4j:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "wcy666666")
        
        print(f"Neo4j 连接配置:")
        print(f"  URI: {neo4j_uri}")
        print(f"  User: {neo4j_user}")
        print(f"  Password: {'*' * len(neo4j_password)}")
        
        self.driver = AsyncGraphDatabase.driver(
            neo4j_uri,
            auth=(neo4j_user, neo4j_password)
        )
        self.data_dir = Path(__file__).parent.parent / "datasource"
        print(f"  数据目录: {self.data_dir}")

    async def close(self):
        """关闭数据库连接"""
        await self.driver.close()

    async def clear_database(self):
        """清空数据库"""
        print("\n正在清空数据库...")
        try:
            async with self.driver.session() as session:
                result = await session.run("MATCH (n) RETURN count(n) as count")
                record = await result.single()
                old_count = record['count']
                print(f"  当前节点数: {old_count}")
                
                if old_count > 0:
                    await session.run("MATCH (n) DETACH DELETE n")
                    print(f"  已删除 {old_count} 个节点")
                else:
                    print("  数据库已经是空的")
            print("✓ 数据库已清空")
        except Exception as e:
            print(f"✗ 清空数据库时出错: {e}")
            raise

    async def create_constraints(self):
        """创建约束和索引"""
        print("正在创建约束和索引...")
        async with self.driver.session() as session:
            # 为实体创建唯一性约束
            try:
                await session.run(
                    "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE"
                )
            except Exception as e:
                print(f"创建实体约束时出错（可能已存在）: {e}")

            # 为社区创建唯一性约束
            try:
                await session.run(
                    "CREATE CONSTRAINT community_id IF NOT EXISTS FOR (c:COMMUNITY) REQUIRE c.id IS UNIQUE"
                )
            except Exception as e:
                print(f"创建社区约束时出错（可能已存在）: {e}")

            # 为文档创建唯一性约束
            try:
                await session.run(
                    "CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:RAW_DOCUMENT) REQUIRE d.id IS UNIQUE"
                )
            except Exception as e:
                print(f"创建文档约束时出错（可能已存在）: {e}")

        print("✓ 约束和索引创建完成")

    async def import_entities(self):
        """导入实体数据"""
        print("正在导入实体...")
        
        # 读取 parquet 文件（更高效）
        entities_file = self.data_dir / "entities.parquet"
        if entities_file.exists():
            df = pd.read_parquet(entities_file)
        else:
            # 如果 parquet 不存在，读取 CSV
            df = pd.read_csv(self.data_dir / "entities.csv")

        print(f"找到 {len(df)} 个实体")

        # 批量导入
        batch_size = 500
        total_batches = (len(df) + batch_size - 1) // batch_size

        async with self.driver.session() as session:
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i + batch_size]
                entities_data = []

                for _, row in batch.iterrows():
                    entity = {
                        'id': str(row['id']),
                        'title': str(row['title']),
                        'type': str(row.get('type', '')),
                        'description': str(row.get('description', '')),
                        'human_readable_id': int(row.get('human_readable_id', 0)),
                        'degree': int(row.get('degree', 0)),
                        'x': float(row.get('x', 0.0)),
                        'y': float(row.get('y', 0.0))
                    }
                    entities_data.append(entity)

                # 批量创建节点（使用实体的type作为标签，如果没有则使用Entity）
                await session.run("""
                    UNWIND $entities AS entity
                    CREATE (e:Entity)
                    SET e.id = entity.id,
                        e.title = entity.title,
                        e.name = entity.title,
                        e.type = entity.type,
                        e.description = entity.description,
                        e.human_readable_id = entity.human_readable_id,
                        e.degree = entity.degree,
                        e.x = entity.x,
                        e.y = entity.y
                """, entities=entities_data)

                current_batch = i // batch_size + 1
                print(f"  进度: {current_batch}/{total_batches} 批次")

        print(f"✓ 成功导入 {len(df)} 个实体")

    async def import_relationships(self):
        """导入关系数据"""
        print("正在导入关系...")

        # 读取 parquet 文件
        relationships_file = self.data_dir / "relationships.parquet"
        if relationships_file.exists():
            df = pd.read_parquet(relationships_file)
        else:
            df = pd.read_csv(self.data_dir / "relationships.csv")

        print(f"找到 {len(df)} 个关系")

        batch_size = 500
        total_batches = (len(df) + batch_size - 1) // batch_size

        async with self.driver.session() as session:
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i + batch_size]
                relationships_data = []

                for _, row in batch.iterrows():
                    rel = {
                        'source': str(row['source']),
                        'target': str(row['target']),
                        'description': str(row.get('description', '')),
                        'weight': float(row.get('weight', 1.0)),
                        'id': str(row.get('id', ''))
                    }
                    relationships_data.append(rel)

                # 批量创建关系
                await session.run("""
                    UNWIND $relationships AS rel
                    MATCH (source:Entity {title: rel.source})
                    MATCH (target:Entity {title: rel.target})
                    CREATE (source)-[r:RELATED_TO]->(target)
                    SET r.description = rel.description,
                        r.weight = rel.weight,
                        r.id = rel.id
                """, relationships=relationships_data)

                current_batch = i // batch_size + 1
                print(f"  进度: {current_batch}/{total_batches} 批次")

        print(f"✓ 成功导入 {len(df)} 个关系")

    async def import_communities(self):
        """导入社区数据"""
        print("正在导入社区...")

        communities_file = self.data_dir / "communities.parquet"
        if communities_file.exists():
            df = pd.read_parquet(communities_file)
        else:
            df = pd.read_csv(self.data_dir / "communities.csv")

        print(f"找到 {len(df)} 个社区")

        batch_size = 100
        total_batches = (len(df) + batch_size - 1) // batch_size

        async with self.driver.session() as session:
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i + batch_size]
                communities_data = []

                for _, row in batch.iterrows():
                    comm = {
                        'id': str(row['id']),
                        'community': int(row.get('community', 0)),
                        'level': int(row.get('level', 0)),
                        'title': str(row.get('title', '')),
                        'size': int(row.get('size', 0))
                    }
                    communities_data.append(comm)

                # 批量创建社区节点（使用COMMUNITY标签以匹配GraphRAG Visualizer）
                await session.run("""
                    UNWIND $communities AS comm
                    CREATE (c:COMMUNITY)
                    SET c.id = comm.id,
                        c.community = comm.community,
                        c.level = comm.level,
                        c.title = comm.title,
                        c.name = comm.title,
                        c.size = comm.size
                """, communities=communities_data)

                current_batch = i // batch_size + 1
                print(f"  进度: {current_batch}/{total_batches} 批次")

        print(f"✓ 成功导入 {len(df)} 个社区")

    async def import_community_reports(self):
        """导入社区报告数据"""
        print("正在导入社区报告...")

        reports_file = self.data_dir / "community_reports.parquet"
        if reports_file.exists():
            df = pd.read_parquet(reports_file)
        else:
            reports_file = self.data_dir / "community_reports.csv"
            if not reports_file.exists():
                print("未找到社区报告文件，跳过")
                return
            df = pd.read_csv(reports_file)

        print(f"找到 {len(df)} 个社区报告")

        batch_size = 100
        total_batches = (len(df) + batch_size - 1) // batch_size

        async with self.driver.session() as session:
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i + batch_size]

                for _, row in batch.iterrows():
                    # 将报告内容添加到对应的社区节点
                    report_data = {
                        'community_id': str(row['community']),
                        'title': str(row.get('title', '')),
                        'summary': str(row.get('summary', ''))[:5000],  # 限制长度
                        'full_content': str(row.get('full_content', ''))[:10000],  # 限制长度
                        'rank': float(row.get('rank', 0.0))
                    }

                    await session.run("""
                        MATCH (c:COMMUNITY {community: toInteger($community_id)})
                        SET c.report_title = $title,
                            c.summary = $summary,
                            c.full_content = $full_content,
                            c.rank = $rank
                    """, **report_data)

                current_batch = i // batch_size + 1
                print(f"  进度: {current_batch}/{total_batches} 批次")

        print(f"✓ 成功导入 {len(df)} 个社区报告")

    async def import_documents(self):
        """导入文档数据"""
        print("正在导入文档...")

        documents_file = self.data_dir / "documents.parquet"
        if documents_file.exists():
            df = pd.read_parquet(documents_file)
        else:
            documents_file = self.data_dir / "documents.csv"
            if not documents_file.exists():
                print("未找到文档文件，跳过")
                return
            df = pd.read_csv(documents_file)

        print(f"找到 {len(df)} 个文档")

        batch_size = 100
        total_batches = (len(df) + batch_size - 1) // batch_size

        async with self.driver.session() as session:
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i + batch_size]
                documents_data = []

                for _, row in batch.iterrows():
                    doc = {
                        'id': str(row.get('id', '')),
                        'title': str(row.get('title', ''))[:500],
                        'raw_content': str(row.get('raw_content', ''))[:5000],  # 限制长度
                        'text': str(row.get('raw_content', ''))[:5000]  # GraphRAG使用text字段
                    }
                    documents_data.append(doc)

                # 使用RAW_DOCUMENT标签以匹配GraphRAG Visualizer
                await session.run("""
                    UNWIND $documents AS doc
                    CREATE (d:RAW_DOCUMENT)
                    SET d.id = doc.id,
                        d.title = doc.title,
                        d.name = doc.title,
                        d.raw_content = doc.raw_content,
                        d.text = doc.text
                """, documents=documents_data)

                current_batch = i // batch_size + 1
                print(f"  进度: {current_batch}/{total_batches} 批次")

        print(f"✓ 成功导入 {len(df)} 个文档")

    async def import_text_units(self):
        """导入文本单元数据"""
        print("正在导入文本单元...")

        text_units_file = self.data_dir / "text_units.parquet"
        if text_units_file.exists():
            df = pd.read_parquet(text_units_file)
        else:
            text_units_file = self.data_dir / "text_units.csv"
            if not text_units_file.exists():
                print("未找到文本单元文件，跳过")
                return
            df = pd.read_csv(text_units_file)

        print(f"找到 {len(df)} 个文本单元")

        batch_size = 100
        total_batches = (len(df) + batch_size - 1) // batch_size

        async with self.driver.session() as session:
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i + batch_size]
                text_units_data = []

                for _, row in batch.iterrows():
                    # 处理列表类型的字段
                    document_ids = row.get('document_ids', [])
                    if isinstance(document_ids, str):
                        import ast
                        try:
                            document_ids = ast.literal_eval(document_ids) if document_ids else []
                        except:
                            document_ids = []
                    
                    entity_ids = row.get('entity_ids', [])
                    if isinstance(entity_ids, str):
                        import ast
                        try:
                            entity_ids = ast.literal_eval(entity_ids) if entity_ids else []
                        except:
                            entity_ids = []
                    
                    relationship_ids = row.get('relationship_ids', [])
                    if isinstance(relationship_ids, str):
                        import ast
                        try:
                            relationship_ids = ast.literal_eval(relationship_ids) if relationship_ids else []
                        except:
                            relationship_ids = []

                    text_unit = {
                        'id': str(row.get('id', '')),
                        'human_readable_id': int(row.get('human_readable_id', 0)),
                        'text': str(row.get('text', ''))[:10000],  # 限制长度
                        'n_tokens': int(row.get('n_tokens', 0)),
                        'document_ids': document_ids,
                        'entity_ids': entity_ids,
                        'relationship_ids': relationship_ids
                    }
                    text_units_data.append(text_unit)

                # 使用CHUNK标签以匹配GraphRAG Visualizer
                await session.run("""
                    UNWIND $text_units AS tu
                    CREATE (t:CHUNK)
                    SET t.id = tu.id,
                        t.human_readable_id = tu.human_readable_id,
                        t.text = tu.text,
                        t.content = tu.text,
                        t.n_tokens = tu.n_tokens,
                        t.document_ids = tu.document_ids,
                        t.entity_ids = tu.entity_ids,
                        t.relationship_ids = tu.relationship_ids
                """, text_units=text_units_data)

                current_batch = i // batch_size + 1
                print(f"  进度: {current_batch}/{total_batches} 批次")

        print(f"✓ 成功导入 {len(df)} 个文本单元")

    async def import_covariates(self):
        """导入协变量数据"""
        print("正在导入协变量...")

        covariates_file = self.data_dir / "covariates.parquet"
        if covariates_file.exists():
            df = pd.read_parquet(covariates_file)
        else:
            covariates_file = self.data_dir / "covariates.csv"
            if not covariates_file.exists():
                print("未找到协变量文件，跳过")
                return
            df = pd.read_csv(covariates_file)

        print(f"找到 {len(df)} 个协变量")

        batch_size = 100
        total_batches = (len(df) + batch_size - 1) // batch_size

        async with self.driver.session() as session:
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i + batch_size]
                covariates_data = []

                for _, row in batch.iterrows():
                    covariate = {
                        'id': str(row.get('id', '')),
                        'human_readable_id': int(row.get('human_readable_id', 0)),
                        'covariate_type': str(row.get('covariate_type', 'CLAIM')),
                        'type': str(row.get('type', 'COVARIATE')),
                        'description': str(row.get('description', ''))[:5000],
                        'subject_id': str(row.get('subject_id', '')),
                        'object_id': str(row.get('object_id', '')),
                        'status': str(row.get('status', '')),
                        'start_date': str(row.get('start_date', '')),
                        'end_date': str(row.get('end_date', '')),
                        'source_text': str(row.get('source_text', ''))[:5000],
                        'text_unit_id': str(row.get('text_unit_id', ''))
                    }
                    covariates_data.append(covariate)

                # 使用COVARIATE标签
                await session.run("""
                    UNWIND $covariates AS cov
                    CREATE (c:COVARIATE)
                    SET c.id = cov.id,
                        c.human_readable_id = cov.human_readable_id,
                        c.covariate_type = cov.covariate_type,
                        c.type = cov.type,
                        c.description = cov.description,
                        c.subject_id = cov.subject_id,
                        c.object_id = cov.object_id,
                        c.status = cov.status,
                        c.start_date = cov.start_date,
                        c.end_date = cov.end_date,
                        c.source_text = cov.source_text,
                        c.text_unit_id = cov.text_unit_id
                """, covariates=covariates_data)

                current_batch = i // batch_size + 1
                print(f"  进度: {current_batch}/{total_batches} 批次")

        print(f"✓ 成功导入 {len(df)} 个协变量")

    async def print_stats(self):
        """打印数据库统计信息"""
        print("\n" + "="*60)
        print("数据库统计信息")
        print("="*60)

        async with self.driver.session() as session:
            # 实体数量
            result = await session.run("MATCH (e:Entity) RETURN count(e) as count")
            record = await result.single()
            print(f"实体 (Entity) 节点数: {record['count']}")

            # 关系数量
            result = await session.run("MATCH ()-[r:RELATED_TO]->() RETURN count(r) as count")
            record = await result.single()
            print(f"关系 (RELATED_TO) 数: {record['count']}")

            # 社区数量
            result = await session.run("MATCH (c:COMMUNITY) RETURN count(c) as count")
            record = await result.single()
            print(f"社区 (COMMUNITY) 节点数: {record['count']}")

            # 文档数量
            result = await session.run("MATCH (d:RAW_DOCUMENT) RETURN count(d) as count")
            record = await result.single()
            print(f"文档 (RAW_DOCUMENT) 节点数: {record['count']}")

            # 文本单元数量
            result = await session.run("MATCH (t:CHUNK) RETURN count(t) as count")
            record = await result.single()
            print(f"文本单元 (CHUNK) 节点数: {record['count']}")

            # 协变量数量
            result = await session.run("MATCH (c:COVARIATE) RETURN count(c) as count")
            record = await result.single()
            print(f"协变量 (COVARIATE) 节点数: {record['count']}")

            # 实体类型分布
            result = await session.run("""
                MATCH (e:Entity)
                RETURN e.type as type, count(*) as count
                ORDER BY count DESC
                LIMIT 10
            """)
            print("\n实体类型 TOP 10:")
            async for record in result:
                print(f"  - {record['type']}: {record['count']}")

        print("="*60 + "\n")

    async def run(self, clear_existing=True):
        """运行完整的导入流程"""
        try:
            print("\n" + "="*60)
            print("开始导入 GraphRAG 数据到 Neo4j")
            print("="*60 + "\n")

            if clear_existing:
                await self.clear_database()

            await self.create_constraints()
            await self.import_entities()
            await self.import_relationships()
            await self.import_communities()
            await self.import_community_reports()
            await self.import_documents()
            await self.import_text_units()
            await self.import_covariates()
            await self.print_stats()

            print("✅ 所有数据导入完成！")
            print(f"\n可以通过以下方式访问 Neo4j:")
            print(f"  Web 界面: http://localhost:7474")
            print(f"  用户名: {settings.NEO4J_USER}")
            print(f"  密码: {settings.NEO4J_PASSWORD}\n")

        except Exception as e:
            print(f"\n❌ 导入过程中出错: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.close()


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='将 GraphRAG 数据导入到 Neo4j')
    parser.add_argument('--keep-existing', action='store_true', 
                       help='保留现有数据（默认会清空数据库）')
    args = parser.parse_args()

    importer = GraphRAGImporter()
    await importer.run(clear_existing=not args.keep_existing)


if __name__ == "__main__":
    asyncio.run(main())

