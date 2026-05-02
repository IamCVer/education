// Neo4j数据适配器 - 将Neo4j数据转换为GraphRAG格式

export interface Neo4jNode {
  identity: string;
  labels: string[];
  properties: { [key: string]: any };
}

export interface Neo4jRelationship {
  identity: string;
  start: string;
  end: string;
  type: string;
  properties: { [key: string]: any };
}

export interface Neo4jGraphData {
  nodes: Neo4jNode[];
  relationships: Neo4jRelationship[];
}

// 转换Neo4j数据为GraphRAG Entity格式
export const convertNeo4jToEntities = (nodes: Neo4jNode[]) => {
  return nodes
    .filter(node => node.labels.includes('Entity'))
    .map((node, index) => ({
      id: node.properties.id || node.identity,
      human_readable_id: node.properties.human_readable_id || index,
      title: node.properties.title || node.properties.name || node.identity,
      name: node.properties.name || node.properties.title || node.identity, // 添加name字段用于标签显示
      type: node.properties.type || node.labels[0] || 'UNKNOWN',
      description: node.properties.description || '',
      text_unit_ids: node.properties.text_unit_ids || [],
      graph_embedding: node.properties.graph_embedding,
      text_embedding: node.properties.text_embedding,
      community_ids: node.properties.community_ids || [],
      x: node.properties.x || 0,
      y: node.properties.y || 0,
      degree: node.properties.degree || 0
    }));
};

// 转换Neo4j关系为GraphRAG Relationship格式
export const convertNeo4jToRelationships = (relationships: Neo4jRelationship[], nodes: Neo4jNode[]) => {
  const nodeMap = new Map(nodes.map(node => [node.identity, node]));
  
  return relationships.map((rel, index) => {
    const sourceNode = nodeMap.get(rel.start);
    const targetNode = nodeMap.get(rel.end);
    
    return {
      id: rel.identity,
      human_readable_id: index,
      source: sourceNode?.properties.name || sourceNode?.properties.title || rel.start,
      target: targetNode?.properties.name || targetNode?.properties.title || rel.end,
      description: rel.properties.description || '',
      weight: rel.properties.weight || 1,
      combined_degree: rel.properties.combined_degree || 0,
      text_unit_ids: rel.properties.text_unit_ids || [],
      type: rel.type
    };
  });
};

// 转换Neo4j数据为GraphRAG Documents格式
export const convertNeo4jToDocuments = (nodes: Neo4jNode[]) => {
  return nodes
    .filter(node => node.labels.includes('RAW_DOCUMENT'))
    .map((node, index) => ({
      id: node.identity,
      human_readable_id: index,
      title: node.properties.title || node.properties.name || `Document ${node.identity}`,
      text: node.properties.text || node.properties.content || '',
      text_unit_ids: node.properties.text_unit_ids || []
    }));
};

// 转换Neo4j数据为GraphRAG TextUnits格式
export const convertNeo4jToTextUnits = (nodes: Neo4jNode[]) => {
  return nodes
    .filter(node => node.labels.includes('CHUNK'))
    .map((node, index) => ({
      id: node.identity,
      human_readable_id: index,
      text: node.properties.text || node.properties.content || '',
      n_tokens: node.properties.n_tokens || 0,
      document_ids: node.properties.document_ids || [],
      entity_ids: node.properties.entity_ids || [],
      relationship_ids: node.properties.relationship_ids || []
    }));
};

// 转换Neo4j数据为GraphRAG Communities格式
export const convertNeo4jToCommunities = (nodes: Neo4jNode[]) => {
  return nodes
    .filter(node => node.labels.includes('COMMUNITY'))
    .map((node, index) => ({
      id: parseInt(node.identity) || index,
      human_readable_id: index,
      community: parseInt(node.properties.community || index.toString()),
      parent: node.properties.parent ? parseInt(node.properties.parent) : undefined,
      level: node.properties.level || 0,
      title: node.properties.title || node.properties.name || `Community ${node.identity}`,
      entity_ids: node.properties.entity_ids || [],
      relationship_ids: node.properties.relationship_ids || [],
      text_unit_ids: node.properties.text_unit_ids || [],
      period: node.properties.period || '',
      size: node.properties.size || 0
    }));
};

// 转换Neo4j数据为GraphRAG CommunityReports格式
export const convertNeo4jToCommunityReports = (nodes: Neo4jNode[]) => {
  return nodes
    .filter(node => node.labels.includes('COMMUNITY'))
    .map((node, index) => ({
      id: node.identity,
      human_readable_id: index,
      community: parseInt(node.properties.community || index.toString()),
      parent: node.properties.parent ? parseInt(node.properties.parent) : undefined,
      level: node.properties.level || 0,
      title: node.properties.title || node.properties.name || `Community ${node.identity}`,
      summary: node.properties.summary || '',
      full_content: node.properties.full_content || '',
      rank: node.properties.rank || 1,
      rank_explanation: node.properties.rank_explanation || '',
      findings: node.properties.findings || [],
      full_content_json: node.properties.full_content_json || '',
      period: node.properties.period || '',
      size: node.properties.size || 0
    }));
};

// 转换Neo4j数据为GraphRAG Covariates格式
export const convertNeo4jToCovariates = (nodes: Neo4jNode[]) => {
  return nodes
    .filter(node => node.labels.includes('COVARIATE'))
    .map((node, index) => ({
      id: node.identity,
      human_readable_id: index,
      covariate_type: node.properties.covariate_type || 'CLAIM',
      type: node.properties.type || 'COVARIATE',
      description: node.properties.description || '',
      subject_id: node.properties.subject_id || '',
      object_id: node.properties.object_id || '',
      status: node.properties.status || '',
      start_date: node.properties.start_date || '',
      end_date: node.properties.end_date || '',
      source_text: node.properties.source_text || '',
      text_unit_id: node.properties.text_unit_id || ''
    }));
};

// 主要的转换函数
export const convertNeo4jToGraphRAGFormat = (neo4jData: Neo4jGraphData) => {
  const entities = convertNeo4jToEntities(neo4jData.nodes);
  const relationships = convertNeo4jToRelationships(neo4jData.relationships, neo4jData.nodes);
  const documents = convertNeo4jToDocuments(neo4jData.nodes);
  const textUnits = convertNeo4jToTextUnits(neo4jData.nodes);
  const communities = convertNeo4jToCommunities(neo4jData.nodes);
  const communityReports = convertNeo4jToCommunityReports(neo4jData.nodes);
  const covariates = convertNeo4jToCovariates(neo4jData.nodes);

  return {
    entities,
    relationships,
    documents,
    textUnits,
    communities,
    communityReports,
    covariates
  };
};

// API调用函数 - 从后端获取Neo4j数据
export const fetchNeo4jData = async (baseUrl: string, token: string): Promise<Neo4jGraphData> => {
  try {
    const response = await fetch(`${baseUrl}/api/v1/graph/neo4j-data`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    return {
      nodes: data.nodes || [],
      relationships: data.relationships || []
    };
  } catch (error) {
    console.error('获取Neo4j数据失败:', error);
    throw error;
  }
};

// 获取认证token的辅助函数
export const getAuthToken = (): string | null => {
  // 首先尝试从URL参数获取token
  const urlParams = new URLSearchParams(window.location.search);
  const urlToken = urlParams.get('token');
  
  console.log('URL参数:', window.location.search);
  console.log('从URL获取的token:', urlToken);
  
  if (urlToken) {
    console.log('保存token到localStorage');
    // 如果URL中有token，保存到localStorage并使用
    localStorage.setItem('userToken', urlToken);
    // 清除URL中的token参数以避免安全问题
    const url = new URL(window.location.href);
    url.searchParams.delete('token');
    window.history.replaceState({}, document.title, url.toString());
    return urlToken;
  }
  
  // 否则从localStorage获取
  const storedToken = localStorage.getItem('userToken');
  console.log('从localStorage获取的token:', storedToken ? '存在' : '不存在');
  return storedToken;
};

// 检查用户是否已登录
export const isAuthenticated = (): boolean => {
  const token = getAuthToken();
  if (!token) return false;
  
  try {
    const tokenParts = token.split('.');
    if (tokenParts.length !== 3) return false;
    
    const payload = JSON.parse(atob(tokenParts[1]));
    const currentTime = Date.now() / 1000;
    
    return payload.exp > currentTime;
  } catch (error) {
    return false;
  }
};

// 重定向到登录页面
export const redirectToLogin = (baseUrl: string) => {
  window.location.href = `${baseUrl}/pages/auth/login.html`;
};
