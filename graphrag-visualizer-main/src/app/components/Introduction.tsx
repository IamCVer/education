import React from "react";
import {
  Typography,
  Box,
  Link,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
} from "@mui/material";

const Introduction: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        欢迎使用 GraphRAG 可视化工具
      </Typography>

      <Typography variant="body1" gutterBottom sx={{ color: "error.main" }}>
        如果您使用的是 <strong>GraphRAG 0.3.x 或更早版本</strong>，请访问旧版网站：{" "}
        <Link
          href="https://noworneverev.github.io/graphrag-visualizer-legacy"
          target="_blank"
          rel="noopener"
        >
          GraphRAG Visualizer 旧版
        </Link>
      </Typography>

      <Typography variant="h6" gutterBottom>
        概述
      </Typography>
      <Typography variant="body1" gutterBottom>
        本应用用于可视化微软{" "}
        <Link
          href="https://microsoft.github.io/graphrag/"
          target="_blank"
          rel="noopener"
        >
          GraphRAG
        </Link>{" "}
        生成的数据。只需上传 parquet 文件即可可视化数据，无需使用 Gephi、Neo4j 或 Jupyter Notebook 等额外软件。
      </Typography>

      <Box
        component="img"
        src={process.env.PUBLIC_URL + "/demo.png"}
        alt="Demo"
        sx={{ mt: 2, mb: 2, width: "100%" }}
      />

      <Typography variant="h6" gutterBottom>
        功能特性
      </Typography>
      <ul>
        <li>
          <Typography variant="body1">
            <strong>图谱可视化：</strong>在"图谱可视化"标签页中以 2D 或 3D 方式查看图谱。
          </Typography>
        </li>
        <li>
          <Typography variant="body1">
            <strong>数据表格：</strong>在"数据表格"标签页中展示 parquet 文件中的数据。
          </Typography>
        </li>
        <li>
          <Typography variant="body1">
            <strong>搜索功能：</strong>完全支持搜索功能，允许用户聚焦于特定的节点或关系。
          </Typography>
        </li>
        <li>
          <Typography variant="body1">
            <strong>本地处理：</strong>您的数据在本地机器上处理，不会上传到任何地方，确保数据安全和隐私。
          </Typography>
        </li>
      </ul>

      <Typography variant="h6" gutterBottom>
        使用搜索功能
      </Typography>
      <Typography variant="body1" gutterBottom>
        一旦{" "}
        <Link
          href="https://github.com/noworneverev/graphrag-api"
          target="_blank"
          rel="noopener"
        >
          graphrag-api
        </Link>{" "}
        服务器启动并运行，您可以直接通过 GraphRAG 可视化工具执行搜索。这使您能够轻松搜索和探索托管在本地服务器上的数据。
      </Typography>

      <Box
        component="img"
        src={process.env.PUBLIC_URL + "/search.png"}
        alt="Search"
        sx={{ mt: 2, mb: 2, width: "100%" }}
      />

      <Typography variant="h6" gutterBottom>
        图数据模型
      </Typography>
      <Typography variant="body1" gutterBottom>
        创建文本单元、文档、社区和协变量关系的逻辑来自{" "}
        <Link
          href="https://github.com/microsoft/graphrag/blob/main/examples_notebooks/community_contrib/neo4j/graphrag_import_neo4j_cypher.ipynb"
          target="_blank"
          rel="noopener"
        >
          GraphRAG 导入 Neo4j Cypher 笔记本
        </Link>
        。
      </Typography>

      <Typography variant="h6" gutterBottom>
        节点类型
      </Typography>
      <TableContainer component={Paper} sx={{ mb: 2 }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>
                <strong>节点</strong>
              </TableCell>
              <TableCell>
                <strong>类型</strong>
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            <TableRow>
              <TableCell>文档</TableCell>
              <TableCell>
                <Chip label="RAW_DOCUMENT" size="small" />
              </TableCell>
            </TableRow>
            <TableRow>
              <TableCell>文本单元</TableCell>
              <TableCell>
                <Chip label="CHUNK" size="small" />
              </TableCell>
            </TableRow>
            <TableRow>
              <TableCell>社区</TableCell>
              <TableCell>
                <Chip label="COMMUNITY" size="small" />
              </TableCell>
            </TableRow>
            <TableRow>
              <TableCell>发现</TableCell>
              <TableCell>
                <Chip label="FINDING" size="small" />
              </TableCell>
            </TableRow>
            <TableRow>
              <TableCell>协变量</TableCell>
              <TableCell>
                <Chip label="COVARIATE" size="small" />
              </TableCell>
            </TableRow>
            <TableRow>
              <TableCell>实体</TableCell>
              <TableCell>
                <i>多种类型</i>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>

      <Typography variant="h6" gutterBottom>
        关系类型
      </Typography>
      <TableContainer component={Paper} sx={{ mb: 2 }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>
                <strong>源节点</strong>
              </TableCell>
              <TableCell>
                <strong>关系</strong>
              </TableCell>
              <TableCell>
                <strong>目标节点</strong>
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            <TableRow>
              <TableCell>实体</TableCell>
              <TableCell>
                <Chip label="RELATED" size="small" />
              </TableCell>
              <TableCell>实体</TableCell>
            </TableRow>
            <TableRow>
              <TableCell>文本单元</TableCell>
              <TableCell>
                <Chip label="PART_OF" size="small" />
              </TableCell>
              <TableCell>文档</TableCell>
            </TableRow>
            <TableRow>
              <TableCell>文本单元</TableCell>
              <TableCell>
                <Chip label="HAS_ENTITY" size="small" />
              </TableCell>
              <TableCell>实体</TableCell>
            </TableRow>
            <TableRow>
              <TableCell>文本单元</TableCell>
              <TableCell>
                <Chip label="HAS_COVARIATE" size="small" />
              </TableCell>
              <TableCell>协变量</TableCell>
            </TableRow>
            <TableRow>
              <TableCell>社区</TableCell>
              <TableCell>
                <Chip label="HAS_FINDING" size="small" />
              </TableCell>
              <TableCell>发现</TableCell>
            </TableRow>
            <TableRow>
              <TableCell>实体</TableCell>
              <TableCell>
                <Chip label="IN_COMMUNITY" size="small" />
              </TableCell>
              <TableCell>社区</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default Introduction;
