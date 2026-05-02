import React, { useEffect, useState } from "react";
import {
  Box,
  Button,
  CircularProgress,
  Drawer,
  TextField,
  Typography,
  Card,
  CardContent,
  CardHeader,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Collapse,
  Link,
  Alert,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import { SearchResult } from "../models/search-result";

interface APISearchDrawerProps {
  apiDrawerOpen: boolean;
  toggleDrawer: (open: boolean) => () => void;
  handleApiSearch: (
    query: string,
    searchType: "local" | "global"
  ) => Promise<void>;
  apiSearchResults: SearchResult | null;
  localSearchEnabled: boolean;
  globalSearchEnabled: boolean;
  hasCovariates: boolean;
  serverUp: boolean;
}

const APISearchDrawer: React.FC<APISearchDrawerProps> = ({
  apiDrawerOpen,
  toggleDrawer,
  handleApiSearch,
  apiSearchResults,
  localSearchEnabled,
  globalSearchEnabled,
  hasCovariates,
  serverUp,
}) => {
  const [query, setQuery] = useState<string>("");
  const [loadingLocal, setLoadingLocal] = useState<boolean>(false);
  const [loadingGlobal, setLoadingGlobal] = useState<boolean>(false);
  const [expandedTables, setExpandedTables] = useState<{
    [key: string]: boolean;
  }>({});

  useEffect(() => {
    // Initialize the expandedTables state to false for all keys in context_data
    if (apiSearchResults && apiSearchResults.context_data) {
      const initialExpandedState: { [key: string]: boolean } = {};
      Object.keys(apiSearchResults.context_data).forEach((key) => {
        initialExpandedState[key] = true;
      });
      setExpandedTables(initialExpandedState);
    }
  }, [apiSearchResults]);

  const handleSearch = async (searchType: "local" | "global") => {
    if (searchType === "local") {
      setLoadingLocal(true);
    } else {
      setLoadingGlobal(true);
    }

    try {
      await handleApiSearch(query, searchType);
    } finally {
      if (searchType === "local") {
        setLoadingLocal(false);
      } else {
        setLoadingGlobal(false);
      }
    }
  };

  const toggleTable = (key: string) => {
    setExpandedTables((prevState) => ({
      ...prevState,
      [key]: !prevState[key],
    }));
  };

  return (
    <Drawer
      anchor="left"
      open={apiDrawerOpen}
      onClose={toggleDrawer(false)}
      sx={{ zIndex: 1500 }}
    >
      <Box
        sx={{ width: "60vw", padding: 2, paddingTop: 6, position: "relative" }}
      >
        {/* Close Button at the top-right corner */}
        <IconButton
          onClick={toggleDrawer(false)}
          sx={{ position: "absolute", top: 8, right: 8 }}
        >
          <CloseIcon />
        </IconButton>

        {/* First Row: TextField */}
        <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <TextField
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            // onKeyDown={async (e) => {
            //   if (e.key === "Enter" && !loadingLocal) {
            //     await handleSearch("local"); // Default to global search on enter
            //   }
            // }}
            placeholder="输入 API 搜索查询"
            fullWidth
            margin="normal"
          />

          {/* Second Row: Buttons */}
          <Box sx={{ display: "flex", gap: 2 }}>
            <Button
              variant="contained"
              sx={{ flex: 1, whiteSpace: "normal", textAlign: "center" }}
              onClick={() => handleSearch("local")}
              disabled={
                !serverUp ||
                !localSearchEnabled ||
                loadingLocal ||
                loadingGlobal
              }
            >
              {loadingLocal ? <CircularProgress size={24} /> : "本地搜索"}
            </Button>
            <Button
              variant="contained"
              color="success"
              sx={{ flex: 1, whiteSpace: "normal", textAlign: "center" }}
              onClick={() => handleSearch("global")}
              disabled={
                !serverUp ||
                !globalSearchEnabled ||
                loadingLocal ||
                loadingGlobal
              }
            >
              {loadingGlobal ? <CircularProgress size={24} /> : "全局搜索"}
            </Button>
          </Box>

          {!serverUp && (
            <Alert severity="error" sx={{ mt: 1 }}>
              服务器未运行。请启动服务器以使用 API。请按照{" "}
              <Link
                href="https://github.com/noworneverev/graphrag-api"
                target="_blank"
                rel="noopener noreferrer"
              >
                graphrag-api
              </Link>{" "}
              的说明操作。
            </Alert>
          )}
          {!localSearchEnabled && (
            <Alert severity="warning" sx={{ mt: 1 }}>
              请启用"包含文本单元"和"包含社区"
              {hasCovariates && '，以及"包含协变量"'}以使用本地搜索。
            </Alert>
          )}
          {!globalSearchEnabled && (
            <Alert severity="warning" sx={{ mt: 1 }}>
              请启用"包含社区"以使用全局搜索。
            </Alert>
          )}
        </Box>

        {apiSearchResults && (
          <>
            {/* Search Results Card */}
            <Card sx={{ marginTop: 2 }}>
              <CardHeader title="搜索结果" />
              <CardContent>
                <Typography variant="body1" sx={{ whiteSpace: "pre-wrap" }}>
                  {apiSearchResults.response}
                </Typography>
              </CardContent>
            </Card>

            {/* Metadata Card */}
            <Card sx={{ marginTop: 2 }}>
              <CardHeader title="元数据" />
              <CardContent>
                <Typography variant="body2">
                  <strong>完成时间:</strong>{" "}
                  {apiSearchResults.completion_time} ms
                </Typography>
                <Typography variant="body2">
                  <strong>LLM 调用次数:</strong> {apiSearchResults.llm_calls}
                </Typography>
                <Typography variant="body2">
                  <strong>提示词令牌数:</strong>{" "}
                  {apiSearchResults.prompt_tokens}
                </Typography>
              </CardContent>
            </Card>

            {/* Context Data Tables */}
            {apiSearchResults &&
              apiSearchResults.context_data &&
              Object.entries(apiSearchResults.context_data).map(
                ([key, data], index) => (
                  <Card sx={{ marginTop: 2 }} key={index}>
                    <CardHeader
                      title={key.charAt(0).toUpperCase() + key.slice(1)}
                      action={
                        <IconButton onClick={() => toggleTable(key)}>
                          {expandedTables[key] ? (
                            <ExpandLessIcon />
                          ) : (
                            <ExpandMoreIcon />
                          )}
                        </IconButton>
                      }
                    />
                    <Collapse
                      in={expandedTables[key]}
                      timeout="auto"
                      unmountOnExit
                    >
                      <CardContent>
                        {Array.isArray(data) && data.length > 0 ? (
                          <TableContainer component={Paper}>
                            <Table size="small">
                              <TableHead>
                                <TableRow>
                                  {Object.keys(data[0]).map(
                                    (columnName, idx) => (
                                      <TableCell key={idx}>
                                        {columnName.charAt(0).toUpperCase() +
                                          columnName.slice(1)}
                                      </TableCell>
                                    )
                                  )}
                                </TableRow>
                              </TableHead>
                              <TableBody>
                                {data.map((row, rowIndex) => (
                                  <TableRow key={rowIndex}>
                                    {Object.values(row).map(
                                      (value, cellIndex) => (
                                        <TableCell key={cellIndex}>
                                          {typeof value === "string"
                                            ? value
                                            : JSON.stringify(value, null, 2)}
                                        </TableCell>
                                      )
                                    )}
                                  </TableRow>
                                ))}
                              </TableBody>
                            </Table>
                          </TableContainer>
                        ) : (
                          <Typography variant="body2" color="textSecondary">
                            暂无数据
                          </Typography>
                        )}
                      </CardContent>
                    </Collapse>
                  </Card>
                )
              )}
          </>
        )}
      </Box>
    </Drawer>
  );
};

export default APISearchDrawer;
