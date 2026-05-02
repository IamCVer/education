// 清空数据库（可选）
MATCH (n) DETACH DELETE n;

// 创建约束
CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT community_id IF NOT EXISTS FOR (c:Community) REQUIRE c.id IS UNIQUE;

// 导入实体
LOAD CSV WITH HEADERS FROM 'file:///entities.csv' AS row
CREATE (e:Entity {
    id: row.id,
    human_readable_id: toInteger(row.human_readable_id),
    title: row.title,
    type: row.type,
    description: row.description,
    degree: toInteger(row.degree),
    x: toFloat(row.x),
    y: toFloat(row.y)
});

// 创建实体索引
CREATE INDEX entity_title IF NOT EXISTS FOR (e:Entity) ON (e.title);

// 导入关系
LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
MATCH (source:Entity {title: row.source})
MATCH (target:Entity {title: row.target})
CREATE (source)-[r:RELATED_TO {
    id: row.id,
    description: row.description,
    weight: toFloat(row.weight)
}]->(target);

// 导入社区
LOAD CSV WITH HEADERS FROM 'file:///communities.csv' AS row
CREATE (c:Community {
    id: row.id,
    human_readable_id: toInteger(row.human_readable_id),
    community: toInteger(row.community),
    level: toInteger(row.level),
    title: row.title,
    size: toInteger(row.size)
});

// 显示统计信息
MATCH (e:Entity) RETURN 'Entities' as type, count(e) as count
UNION
MATCH ()-[r:RELATED_TO]->() RETURN 'Relationships' as type, count(r) as count
UNION  
MATCH (c:Community) RETURN 'Communities' as type, count(c) as count;

