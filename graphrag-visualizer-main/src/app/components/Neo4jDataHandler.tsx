import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  Box,
  Container,
  Tab,
  Tabs,
  Typography,
  Alert,
  CircularProgress,
  Button,
  Snackbar,
} from "@mui/material";
import { 
  fetchNeo4jData, 
  convertNeo4jToGraphRAGFormat,
  redirectToLogin,
  getAuthToken
} from "../api/neo4j-adapter";
import { Entity } from "../models/entity";
import { Relationship } from "../models/relationship";
import { Document } from "../models/document";
import { TextUnit } from "../models/text-unit";
import { Community } from "../models/community";
import { CommunityReport } from "../models/community-report";
import { Covariate } from "../models/covariate";
import useGraphData from "../hooks/useGraphData";
import GraphViewer from "./GraphViewer";
import DataTableContainer from "./DataTableContainer";

// 配置 - 可以通过环境变量或配置文件设置
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

const Neo4jDataHandler: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();

  // 标签页和UI状态
  const [tabIndex, setTabIndex] = useState(0);
  const [graphType, setGraphType] = useState<"2d" | "3d">("2d");
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [selectedTable, setSelectedTable] = useState<
    | "entities"
    | "relationships"
    | "documents"
    | "textunits"
    | "communities"
    | "communityReports"
    | "covariates"
  >("entities");
  const [includeDocuments, setIncludeDocuments] = useState(false);
  const [includeTextUnits, setIncludeTextUnits] = useState(false);
  const [includeCommunities, setIncludeCommunities] = useState(false);
  const [includeCovariates, setIncludeCovariates] = useState(false);
  // 数据状态
  const [entities, setEntities] = useState<Entity[]>([]);
  const [relationships, setRelationships] = useState<Relationship[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [textUnits, setTextUnits] = useState<TextUnit[]>([]);
  const [communities, setCommunities] = useState<Community[]>([]);
  const [communityReports, setCommunityReports] = useState<CommunityReport[]>([]);
  const [covariates, setCovariates] = useState<Covariate[]>([]);

  // 加载状态
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [snackbarOpen, setSnackbarOpen] = useState(false);

  // 使用GraphRAG的useGraphData hook
  const graphData = useGraphData(
    entities,
    relationships,
    documents,
    textUnits,
    communities,
    communityReports,
    covariates,
    includeDocuments,
    includeTextUnits,
    includeCommunities,
    includeCovariates
  );

  // 加载Neo4j数据
  const loadNeo4jData = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = getAuthToken();
      console.log('获取到的token:', token ? '存在' : '不存在');
      
      if (!token) {
        console.log('未找到认证令牌，重定向到登录页面');
        console.log('当前URL:', window.location.href);
        redirectToLogin(API_BASE_URL);
        return;
      }

      // 从后端获取Neo4j数据
      const neo4jData = await fetchNeo4jData(API_BASE_URL, token);
      console.log('🔍 从API获取的原始数据:', {
        节点数: neo4jData.nodes.length,
        关系数: neo4jData.relationships.length
      });
      
      // 转换为GraphRAG格式
      const graphragData = convertNeo4jToGraphRAGFormat(neo4jData);
      console.log('✅ 转换后的GraphRAG数据:', {
        实体数: graphragData.entities.length,
        关系数: graphragData.relationships.length,
        文档数: graphragData.documents.length,
        文本单元数: graphragData.textUnits.length,
        社区数: graphragData.communities.length,
        社区报告数: graphragData.communityReports.length,
        协变量数: graphragData.covariates.length
      });
      
      if (graphragData.entities.length > 0) {
        console.log('📝 第一个实体示例:', graphragData.entities[0]);
      }

      // 更新状态
      setEntities(graphragData.entities);
      setRelationships(graphragData.relationships);
      setDocuments(graphragData.documents);
      setTextUnits(graphragData.textUnits);
      setCommunities(graphragData.communities);
      setCommunityReports(graphragData.communityReports);
      setCovariates(graphragData.covariates);

      console.log('🎉 状态已更新');
      setSnackbarOpen(true);
    } catch (err) {
      console.error('加载Neo4j数据失败:', err);
      setError(err instanceof Error ? err.message : '加载数据时发生未知错误');
    } finally {
      setLoading(false);
    }
  };

  // 组件挂载时延迟加载数据，给认证一些时间
  useEffect(() => {
    const timer = setTimeout(() => {
      loadNeo4jData();
    }, 1000); // 延迟1秒

    return () => clearTimeout(timer);
  }, []);

  // 重新加载数据
  const handleReload = () => {
    loadNeo4jData();
  };

  // 关闭成功提示
  const handleSnackbarClose = () => {
    setSnackbarOpen(false);
  };

  // 事件处理函数
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabIndex(newValue);
    const path = newValue === 0 ? "/neo4j" : "/data";
    navigate(path);
  };

  const handleToggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  const handleToggleGraphType = (event: React.ChangeEvent<HTMLInputElement>) => {
    setGraphType(event.target.checked ? "3d" : "2d");
  };

  // 这些函数直接作为setState函数传递给GraphViewer
  const handleIncludeDocumentsChange = setIncludeDocuments;
  const handleIncludeTextUnitsChange = setIncludeTextUnits;
  const handleIncludeCommunitiesChange = setIncludeCommunities;
  const handleIncludeCovariatesChange = setIncludeCovariates;

  // 根据路径设置标签页
  useEffect(() => {
    if (location.pathname === "/data") {
      setTabIndex(1);
    } else {
      setTabIndex(0);
    }
  }, [location.pathname]);

  // 渲染加载状态
  if (loading) {
    return (
      <Box
        display="flex"
        flexDirection="column"
        alignItems="center"
        justifyContent="center"
        minHeight="60vh"
        gap={2}
      >
        <CircularProgress size={60} />
        <Typography variant="h6" color="textSecondary">
          正在从Neo4j数据库加载图谱数据...
        </Typography>
        <Typography variant="body2" color="textSecondary">
          请稍候，这可能需要几秒钟时间
        </Typography>
      </Box>
    );
  }

  // 渲染错误状态
  if (error) {
    return (
      <Box p={3}>
        <Alert 
          severity="error" 
          action={
            <Button color="inherit" size="small" onClick={handleReload}>
              重试
            </Button>
          }
        >
          <Typography variant="h6">加载数据失败</Typography>
          <Typography variant="body2" sx={{ mt: 1 }}>
            {error}
          </Typography>
        </Alert>
        
        <Box mt={2}>
          <Typography variant="body2" color="textSecondary">
            可能的原因：
          </Typography>
          <ul>
            <li>网络连接问题</li>
            <li>认证令牌已过期，请重新登录</li>
            <li>Neo4j数据库连接问题</li>
            <li>后端服务未运行</li>
          </ul>
        </Box>
      </Box>
    );
  }

  // 渲染数据统计
  const renderDataStats = () => (
    <Box mb={2} p={2} bgcolor="background.paper" borderRadius={1}>
      <Typography variant="h6" gutterBottom>
        数据统计
      </Typography>
      <Box display="flex" gap={3} flexWrap="wrap">
        <Typography variant="body2">
          实体: {entities.length}
        </Typography>
        <Typography variant="body2">
          关系: {relationships.length}
        </Typography>
        <Typography variant="body2">
          文档: {documents.length}
        </Typography>
        <Typography variant="body2">
          文本单元: {textUnits.length}
        </Typography>
        <Typography variant="body2">
          社区: {communities.length}
        </Typography>
        <Typography variant="body2">
          协变量: {covariates.length}
        </Typography>
      </Box>
    </Box>
  );

  return (
    <Container maxWidth={false} disableGutters={tabIndex === 1}>
      <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
        <Tabs value={tabIndex} onChange={handleTabChange}>
          <Tab label="图谱可视化" />
          <Tab label="数据表格" />
        </Tabs>
      </Box>

      {/* 数据统计 - 在数据表格视图中添加左边距 */}
      <Box sx={{ marginLeft: tabIndex === 1 ? '240px' : 0 }}>
        {renderDataStats()}
      </Box>

      {/* 图谱可视化标签页 */}
      {tabIndex === 0 && (
        <GraphViewer
          data={graphData}
          graphType={graphType}
          isFullscreen={isFullscreen}
          onToggleFullscreen={handleToggleFullscreen}
          onToggleGraphType={handleToggleGraphType}
          includeDocuments={includeDocuments}
          includeTextUnits={includeTextUnits}
          includeCommunities={includeCommunities}
          includeCovariates={includeCovariates}
          onIncludeDocumentsChange={handleIncludeDocumentsChange}
          onIncludeTextUnitsChange={handleIncludeTextUnitsChange}
          onIncludeCommunitiesChange={handleIncludeCommunitiesChange}
          onIncludeCovariatesChange={handleIncludeCovariatesChange}
          hasDocuments={documents.length > 0}
          hasTextUnits={textUnits.length > 0}
          hasCommunities={communities.length > 0}
          hasCovariates={covariates.length > 0}
        />
      )}

      {/* 数据表格标签页 */}
      {tabIndex === 1 && (
        <DataTableContainer
          entities={entities}
          relationships={relationships}
          documents={documents}
          textunits={textUnits}
          communities={communities}
          communityReports={communityReports}
          covariates={covariates}
          selectedTable={selectedTable}
          setSelectedTable={setSelectedTable}
        />
      )}

      {/* 成功提示 */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={3000}
        onClose={handleSnackbarClose}
      >
        <Alert onClose={handleSnackbarClose} severity="success">
          Neo4j数据加载成功！共加载 {entities.length} 个实体和 {relationships.length} 个关系。
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default Neo4jDataHandler;
