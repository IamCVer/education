"""
数据集仓库管理API
支持列出、查看元数据、导入导出数据集文件
"""
import os
import asyncio
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
import pandas as pd

from app.api.deps import get_admin_user
from app.models.user_model import User
from app.scripts.import_graphrag_to_neo4j import GraphRAGImporter
from app.services.notification_service import notify_data_import

router = APIRouter()

# 数据源目录
DATASOURCE_DIR = Path(__file__).parent.parent.parent / "datasource"


class DatasetMetadata(BaseModel):
    """数据集元数据"""
    filename: str
    file_type: str  # csv 或 parquet
    file_size: int  # 字节
    row_count: int
    column_count: int
    columns: List[str]
    updated_at: str  # 文件修改时间
    is_online: bool  # 是否在线（是否在Neo4j中）


class ImportRequest(BaseModel):
    """导入请求"""
    filename: str
    clear_existing: bool = True


class ImportStatus(BaseModel):
    """导入状态"""
    status: str  # "success", "error", "running"
    message: str
    filename: Optional[str] = None


# 全局导入状态
import_status = {
    "running": False,
    "last_import": None,
    "error": None
}


def get_file_metadata(filepath: Path) -> Optional[DatasetMetadata]:
    """获取单个文件的元数据"""
    if not filepath.exists():
        return None
    
    # 获取基本文件信息
    stat = filepath.stat()
    file_type = "csv" if filepath.suffix == ".csv" else "parquet" if filepath.suffix == ".parquet" else None
    
    if not file_type:
        return None
    
    try:
        # 尝试读取文件内容
        if filepath.suffix == ".csv":
            # 尝试多种编码
            for encoding in ['utf-8', 'gbk', 'gb2312', 'latin1']:
                try:
                    df = pd.read_csv(filepath, nrows=0, encoding=encoding)
                    row_count = sum(1 for _ in open(filepath, encoding=encoding)) - 1
                    break
                except (UnicodeDecodeError, LookupError):
                    continue
            else:
                # 所有编码都失败，返回基本信息
                raise ValueError("无法识别文件编码")
        elif filepath.suffix == ".parquet":
            df = pd.read_parquet(filepath)
            row_count = len(df)
        
        return DatasetMetadata(
            filename=filepath.name,
            file_type=file_type,
            file_size=stat.st_size,
            row_count=row_count,
            column_count=len(df.columns),
            columns=df.columns.tolist(),
            updated_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
            is_online=False
        )
    except Exception as e:
        print(f"读取文件 {filepath} 详细信息失败: {e}")
        # 返回基本信息（不包含行数和列信息）
        return DatasetMetadata(
            filename=filepath.name,
            file_type=file_type,
            file_size=stat.st_size,
            row_count=0,
            column_count=0,
            columns=[],
            updated_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
            is_online=False
        )


@router.get("/datasets")
async def list_datasets(
    page: int = 1,
    page_size: int = 10,
    current_user: User = Depends(get_admin_user)
):
    """
    列出所有数据集文件及其元数据（支持分页）
    """
    datasets = []
    
    # 扫描数据源目录
    if not DATASOURCE_DIR.exists():
        raise HTTPException(status_code=404, detail="数据源目录不存在")
    
    # 支持的文件类型
    for file_pattern in ["*.csv", "*.parquet"]:
        for filepath in DATASOURCE_DIR.glob(file_pattern):
            metadata = get_file_metadata(filepath)
            if metadata:
                datasets.append(metadata)
    
    # 按文件名排序
    datasets.sort(key=lambda x: x.filename)
    
    # 计算分页
    total = len(datasets)
    total_pages = (total + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    
    return {
        "items": datasets[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }


@router.get("/datasets/import-status", response_model=ImportStatus)
async def get_import_status(
    current_user: User = Depends(get_admin_user)
):
    """
    获取当前导入任务的状态
    """
    global import_status
    
    if import_status["running"]:
        return ImportStatus(
            status="running",
            message="导入任务正在进行中..."
        )
    elif import_status["error"]:
        return ImportStatus(
            status="error",
            message=f"导入失败: {import_status['error']}"
        )
    elif import_status["last_import"]:
        return ImportStatus(
            status="success",
            message=f"导入成功，最后导入时间: {import_status['last_import']}"
        )
    else:
        return ImportStatus(
            status="idle",
            message="暂无导入任务"
        )


@router.get("/datasets/{filename}", response_model=DatasetMetadata)
async def get_dataset_metadata(
    filename: str,
    current_user: User = Depends(get_admin_user)
):
    """
    获取指定数据集的详细元数据
    """
    filepath = DATASOURCE_DIR / filename
    
    if not filepath.exists():
        raise HTTPException(status_code=404, detail=f"文件 {filename} 不存在")
    
    metadata = get_file_metadata(filepath)
    if not metadata:
        raise HTTPException(status_code=400, detail=f"无法读取文件 {filename}")
    
    return metadata


@router.get("/datasets/{filename}/preview")
async def preview_dataset(
    filename: str,
    rows: int = 10,
    current_user: User = Depends(get_admin_user)
):
    """
    预览数据集内容（前N行）
    """
    filepath = DATASOURCE_DIR / filename
    
    if not filepath.exists():
        raise HTTPException(status_code=404, detail=f"文件 {filename} 不存在")
    
    try:
        if filepath.suffix == ".csv":
            df = pd.read_csv(filepath, nrows=rows)
        elif filepath.suffix == ".parquet":
            df = pd.read_parquet(filepath)
            df = df.head(rows)
        else:
            raise HTTPException(status_code=400, detail="不支持的文件类型")
        
        # 转换为JSON（处理NaN值）
        data = df.fillna("").to_dict(orient="records")
        
        return {
            "filename": filename,
            "rows": len(data),
            "columns": df.columns.tolist(),
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取文件失败: {str(e)}")


@router.get("/datasets/{filename}/download")
async def download_dataset(
    filename: str,
    current_user: User = Depends(get_admin_user)
):
    """
    下载数据集文件
    """
    filepath = DATASOURCE_DIR / filename
    
    if not filepath.exists():
        raise HTTPException(status_code=404, detail=f"文件 {filename} 不存在")
    
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/octet-stream"
    )


@router.post("/datasets/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    current_user: User = Depends(get_admin_user)
):
    """
    上传新的数据集文件（csv或parquet）
    """
    # 检查文件类型
    if not (file.filename.endswith(".csv") or file.filename.endswith(".parquet")):
        raise HTTPException(
            status_code=400,
            detail="只支持 CSV 和 Parquet 文件"
        )
    
    # 保存文件
    filepath = DATASOURCE_DIR / file.filename
    
    try:
        content = await file.read()
        with open(filepath, "wb") as f:
            f.write(content)
        
        # 获取元数据
        metadata = get_file_metadata(filepath)
        
        return {
            "success": True,
            "message": f"文件 {file.filename} 上传成功",
            "metadata": metadata
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传文件失败: {str(e)}")


@router.delete("/datasets/{filename}")
async def delete_dataset(
    filename: str,
    current_user: User = Depends(get_admin_user)
):
    """
    删除数据集文件
    """
    filepath = DATASOURCE_DIR / filename
    
    if not filepath.exists():
        raise HTTPException(status_code=404, detail=f"文件 {filename} 不存在")
    
    try:
        filepath.unlink()
        return {
            "success": True,
            "message": f"文件 {filename} 已删除"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}")


async def run_import_task(clear_existing: bool = True, filename: str = None, user_id: int = None, username: str = None):
    """后台运行导入任务"""
    global import_status
    
    try:
        import_status["running"] = True
        import_status["error"] = None
        
        if filename:
            # 单文件导入
            await import_single_file(filename, clear_existing)
        else:
            # 导入所有文件
            importer = GraphRAGImporter()
            await importer.run(clear_existing=clear_existing)
        
        import_status["running"] = False
        import_status["last_import"] = datetime.now().isoformat()
        
        # 创建成功通知
        if user_id and username:
            await notify_data_import(
                username=username,
                user_id=user_id,
                filename=filename or "所有GraphRAG数据",
                success=True
            )
        
    except Exception as e:
        import_status["running"] = False
        import_status["error"] = str(e)
        print(f"导入失败: {e}")
        
        # 创建失败通知
        if user_id and username:
            await notify_data_import(
                username=username,
                user_id=user_id,
                filename=filename or "所有GraphRAG数据",
                success=False
            )


async def import_single_file(filename: str, clear_existing: bool = False):
    """导入单个文件到 Neo4j"""
    from neo4j import AsyncGraphDatabase
    from app.core.config import settings
    import os
    
    # 获取文件路径和类型
    filepath = DATASOURCE_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"文件 {filename} 不存在")
    
    # 判断文件类型
    file_type = None
    base_name = filepath.stem.lower()
    
    # 映射文件名到数据类型
    if base_name in ['entities', 'entity']:
        file_type = 'entities'
    elif base_name in ['relationships', 'relationship']:
        file_type = 'relationships'
    elif base_name in ['communities', 'community']:
        file_type = 'communities'
    elif base_name in ['community_reports', 'community_report']:
        file_type = 'community_reports'
    elif base_name in ['documents', 'document']:
        file_type = 'documents'
    elif base_name in ['text_units', 'text_unit', 'chunks', 'chunk']:
        file_type = 'text_units'
    elif base_name in ['covariates', 'covariate']:
        file_type = 'covariates'
    else:
        # 尝试作为自定义实体导入
        file_type = 'custom'
    
    print(f"开始导入文件: {filename} (类型: {file_type})")
    
    # 读取文件
    if filepath.suffix == '.csv':
        # 尝试多种编码
        for encoding in ['utf-8', 'gbk', 'gb2312', 'latin1']:
            try:
                df = pd.read_csv(filepath, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            # 所有编码都失败，使用错误处理
            df = pd.read_csv(filepath, encoding='latin1')
    elif filepath.suffix == '.parquet':
        df = pd.read_parquet(filepath)
    else:
        raise ValueError(f"不支持的文件格式: {filepath.suffix}")
    
    print(f"读取到 {len(df)} 条记录")
    
    # 连接 Neo4j
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://db_neo4j:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "wcy666666")
    
    driver = AsyncGraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    
    try:
        async with driver.session() as session:
            # 根据文件类型执行不同的导入逻辑
            if file_type == 'entities':
                await import_entities_data(session, df, clear_existing)
            elif file_type == 'relationships':
                await import_relationships_data(session, df, clear_existing)
            elif file_type == 'communities':
                await import_communities_data(session, df, clear_existing)
            elif file_type == 'community_reports':
                await import_community_reports_data(session, df, clear_existing)
            elif file_type == 'documents':
                await import_documents_data(session, df, clear_existing)
            elif file_type == 'text_units':
                await import_text_units_data(session, df, clear_existing)
            elif file_type == 'covariates':
                await import_covariates_data(session, df, clear_existing)
            else:
                # 自定义文件，作为通用实体导入
                await import_custom_entities(session, df, filename, clear_existing)
        
        print(f"✅ 文件 {filename} 导入成功")
    finally:
        await driver.close()


async def import_entities_data(session, df, clear_existing):
    """导入实体数据"""
    if clear_existing:
        await session.run("MATCH (n:Entity) DETACH DELETE n")
        print("已清空现有实体数据")
    
    batch_size = 500
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i + batch_size]
        entities_data = []
        
        for _, row in batch.iterrows():
            entity = {
                'id': str(row.get('id', '')),
                'title': str(row.get('title', '')),
                'type': str(row.get('type', '')),
                'description': str(row.get('description', ''))[:5000],
                'human_readable_id': int(row.get('human_readable_id', 0)),
                'degree': int(row.get('degree', 0)),
                'x': float(row.get('x', 0.0)),
                'y': float(row.get('y', 0.0))
            }
            entities_data.append(entity)
        
        await session.run("""
            UNWIND $entities AS entity
            MERGE (e:Entity {id: entity.id})
            SET e.title = entity.title,
                e.name = entity.title,
                e.type = entity.type,
                e.description = entity.description,
                e.human_readable_id = entity.human_readable_id,
                e.degree = entity.degree,
                e.x = entity.x,
                e.y = entity.y
        """, entities=entities_data)
        
        print(f"  已导入 {min(i + batch_size, len(df))}/{len(df)} 条实体")


async def import_relationships_data(session, df, clear_existing):
    """导入关系数据"""
    if clear_existing:
        await session.run("MATCH ()-[r:RELATED_TO]->() DELETE r")
        print("已清空现有关系数据")
    
    batch_size = 500
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i + batch_size]
        relationships_data = []
        
        for _, row in batch.iterrows():
            rel = {
                'source': str(row.get('source', '')),
                'target': str(row.get('target', '')),
                'description': str(row.get('description', ''))[:5000],
                'weight': float(row.get('weight', 1.0)),
                'id': str(row.get('id', ''))
            }
            relationships_data.append(rel)
        
        await session.run("""
            UNWIND $relationships AS rel
            MATCH (source:Entity {title: rel.source})
            MATCH (target:Entity {title: rel.target})
            MERGE (source)-[r:RELATED_TO]->(target)
            SET r.description = rel.description,
                r.weight = rel.weight,
                r.id = rel.id
        """, relationships=relationships_data)
        
        print(f"  已导入 {min(i + batch_size, len(df))}/{len(df)} 条关系")


async def import_communities_data(session, df, clear_existing):
    """导入社区数据"""
    if clear_existing:
        await session.run("MATCH (n:COMMUNITY) DETACH DELETE n")
        print("已清空现有社区数据")
    
    batch_size = 100
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i + batch_size]
        communities_data = []
        
        for _, row in batch.iterrows():
            comm = {
                'id': str(row.get('id', '')),
                'community': int(row.get('community', 0)),
                'level': int(row.get('level', 0)),
                'title': str(row.get('title', '')),
                'size': int(row.get('size', 0))
            }
            communities_data.append(comm)
        
        await session.run("""
            UNWIND $communities AS comm
            MERGE (c:COMMUNITY {id: comm.id})
            SET c.community = comm.community,
                c.level = comm.level,
                c.title = comm.title,
                c.name = comm.title,
                c.size = comm.size
        """, communities=communities_data)
        
        print(f"  已导入 {min(i + batch_size, len(df))}/{len(df)} 条社区")


async def import_community_reports_data(session, df, clear_existing):
    """导入社区报告数据"""
    batch_size = 100
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i + batch_size]
        
        for _, row in batch.iterrows():
            report_data = {
                'community_id': str(row.get('community', '')),
                'title': str(row.get('title', ''))[:500],
                'summary': str(row.get('summary', ''))[:5000],
                'full_content': str(row.get('full_content', ''))[:10000],
                'rank': float(row.get('rank', 0.0))
            }
            
            await session.run("""
                MATCH (c:COMMUNITY {community: toInteger($community_id)})
                SET c.report_title = $title,
                    c.summary = $summary,
                    c.full_content = $full_content,
                    c.rank = $rank
            """, **report_data)
        
        print(f"  已导入 {min(i + batch_size, len(df))}/{len(df)} 条报告")


async def import_documents_data(session, df, clear_existing):
    """导入文档数据"""
    if clear_existing:
        await session.run("MATCH (n:RAW_DOCUMENT) DETACH DELETE n")
        print("已清空现有文档数据")
    
    batch_size = 100
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i + batch_size]
        documents_data = []
        
        for _, row in batch.iterrows():
            doc = {
                'id': str(row.get('id', '')),
                'title': str(row.get('title', ''))[:500],
                'raw_content': str(row.get('raw_content', ''))[:5000],
                'text': str(row.get('raw_content', ''))[:5000]
            }
            documents_data.append(doc)
        
        await session.run("""
            UNWIND $documents AS doc
            MERGE (d:RAW_DOCUMENT {id: doc.id})
            SET d.title = doc.title,
                d.name = doc.title,
                d.raw_content = doc.raw_content,
                d.text = doc.text
        """, documents=documents_data)
        
        print(f"  已导入 {min(i + batch_size, len(df))}/{len(df)} 条文档")


async def import_text_units_data(session, df, clear_existing):
    """导入文本单元数据"""
    if clear_existing:
        await session.run("MATCH (n:CHUNK) DETACH DELETE n")
        print("已清空现有文本单元数据")
    
    batch_size = 100
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i + batch_size]
        text_units_data = []
        
        for _, row in batch.iterrows():
            text_unit = {
                'id': str(row.get('id', '')),
                'human_readable_id': int(row.get('human_readable_id', 0)),
                'text': str(row.get('text', ''))[:10000],
                'n_tokens': int(row.get('n_tokens', 0))
            }
            text_units_data.append(text_unit)
        
        await session.run("""
            UNWIND $text_units AS tu
            MERGE (t:CHUNK {id: tu.id})
            SET t.human_readable_id = tu.human_readable_id,
                t.text = tu.text,
                t.content = tu.text,
                t.n_tokens = tu.n_tokens
        """, text_units=text_units_data)
        
        print(f"  已导入 {min(i + batch_size, len(df))}/{len(df)} 条文本单元")


async def import_covariates_data(session, df, clear_existing):
    """导入协变量数据"""
    if clear_existing:
        await session.run("MATCH (n:COVARIATE) DETACH DELETE n")
        print("已清空现有协变量数据")
    
    batch_size = 100
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i + batch_size]
        covariates_data = []
        
        for _, row in batch.iterrows():
            covariate = {
                'id': str(row.get('id', '')),
                'human_readable_id': int(row.get('human_readable_id', 0)),
                'covariate_type': str(row.get('covariate_type', 'CLAIM')),
                'type': str(row.get('type', 'COVARIATE')),
                'description': str(row.get('description', ''))[:5000]
            }
            covariates_data.append(covariate)
        
        await session.run("""
            UNWIND $covariates AS cov
            MERGE (c:COVARIATE {id: cov.id})
            SET c.human_readable_id = cov.human_readable_id,
                c.covariate_type = cov.covariate_type,
                c.type = cov.type,
                c.description = cov.description
        """, covariates=covariates_data)
        
        print(f"  已导入 {min(i + batch_size, len(df))}/{len(df)} 条协变量")


async def import_custom_entities(session, df, filename, clear_existing):
    """导入自定义文件作为通用实体"""
    # 使用 Entity 标签，而不是文件名
    label = "Entity"
    
    if clear_existing:
        await session.run(f"MATCH (n:{label}) WHERE n.id STARTS WITH '{filename.split('.')[0]}_' DETACH DELETE n")
        print(f"已清空现有来自 {filename} 的数据")
    
    batch_size = 500
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i + batch_size]
        entities_data = []
        
        for _, row in batch.iterrows():
            entity = {col: str(row.get(col, '')) for col in df.columns}
            entities_data.append(entity)
        
        # 动态构建属性设置
        properties = ', '.join([f"e.{col} = entity.{col}" for col in df.columns if col != 'id'])
        
        query = f"""
            UNWIND $entities AS entity
            MERGE (e:{label} {{id: entity.id}})
            SET {properties}
        """
        
        await session.run(query, entities=entities_data)
        
        print(f"  已导入 {min(i + batch_size, len(df))}/{len(df)} 条 {label}")


@router.post("/datasets/import-to-neo4j", response_model=ImportStatus)
async def import_to_neo4j(
    request: ImportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_admin_user)
):
    """
    将数据集导入到Neo4j知识图谱
    支持增量导入或全量替换
    """
    global import_status
    
    # 检查是否有正在运行的导入任务
    if import_status["running"]:
        raise HTTPException(
            status_code=409,
            detail="已有导入任务正在运行，请稍后再试"
        )
    
    # 检查文件是否存在
    filepath = DATASOURCE_DIR / request.filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail=f"文件 {request.filename} 不存在")
    
    # 在后台运行导入任务（传递文件名和用户信息）
    background_tasks.add_task(
        run_import_task, 
        request.clear_existing, 
        request.filename,
        current_user.id,
        current_user.email
    )
    
    return ImportStatus(
        status="running",
        message=f"正在导入 {request.filename} 到 Neo4j，这可能需要几分钟时间...",
        filename=request.filename
    )


@router.post("/datasets/import-all-to-neo4j")
async def import_all_to_neo4j(
    background_tasks: BackgroundTasks,
    clear_existing: bool = True,
    current_user: User = Depends(get_admin_user)
):
    """
    一键导入所有数据集到Neo4j
    """
    global import_status
    
    # 检查是否有正在运行的导入任务
    if import_status["running"]:
        raise HTTPException(
            status_code=409,
            detail="已有导入任务正在运行，请稍后再试"
        )
    
    # 在后台运行导入任务
    background_tasks.add_task(
        run_import_task, 
        clear_existing, 
        None, 
        current_user.id, 
        current_user.email
    )
    
    return ImportStatus(
        status="running",
        message="正在导入所有数据集到 Neo4j，这可能需要几分钟时间..."
    )

