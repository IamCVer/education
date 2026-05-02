import React from "react";
import {
  Typography,
  Box,
  Drawer,
  List,
  ListItemButton,
  ListItemText,
} from "@mui/material";
import DataTable from "./DataTable";
import { Entity, entityColumns } from "../models/entity";
import { Relationship, relationshipColumns } from "../models/relationship";
import { Document, documentColumns } from "../models/document";
import { TextUnit, textUnitColumns } from "../models/text-unit";
import { Community, communityColumns } from "../models/community";
import {
  CommunityReport,
  communityReportColumns,
} from "../models/community-report";
import { Covariate, covariateColumns } from "../models/covariate";

interface DataTableContainerProps {
  selectedTable: string;
  setSelectedTable: (
    value: React.SetStateAction<
      | "entities"
      | "relationships"
      | "documents"
      | "textunits"
      | "communities"
      | "communityReports"
      | "covariates"
    >
  ) => void;
  entities: Entity[];
  relationships: Relationship[];
  documents: Document[];
  textunits: TextUnit[];
  communities: Community[];
  communityReports: CommunityReport[];
  covariates: Covariate[];
}

const DataTableContainer: React.FC<DataTableContainerProps> = ({
  selectedTable,
  setSelectedTable,
  entities,
  relationships,
  documents,
  textunits,
  communities,
  communityReports,
  covariates,
}) => {
  return (
    <>
      <Drawer
        variant="permanent"
        anchor="left"
        sx={{
          width: 240,
          flexShrink: 0,
          [`& .MuiDrawer-paper`]: { 
            width: 240, 
            boxSizing: "border-box",
            top: 64, // 为顶部导航栏留出空间
            height: 'calc(100% - 64px)',
          },
        }}
      >
        <List>
          <ListItemButton
            selected={selectedTable === "entities"}
            onClick={() => setSelectedTable("entities")}
          >
            <ListItemText primary="实体" />
          </ListItemButton>
          <ListItemButton
            selected={selectedTable === "relationships"}
            onClick={() => setSelectedTable("relationships")}
          >
            <ListItemText primary="关系" />
          </ListItemButton>
          <ListItemButton
            selected={selectedTable === "documents"}
            onClick={() => setSelectedTable("documents")}
          >
            <ListItemText primary="文档" />
          </ListItemButton>
          <ListItemButton
            selected={selectedTable === "textunits"}
            onClick={() => setSelectedTable("textunits")}
          >
            <ListItemText primary="文本单元" />
          </ListItemButton>
          <ListItemButton
            selected={selectedTable === "communities"}
            onClick={() => setSelectedTable("communities")}
          >
            <ListItemText primary="社区" />
          </ListItemButton>

          <ListItemButton
            selected={selectedTable === "communityReports"}
            onClick={() => setSelectedTable("communityReports")}
          >
            <ListItemText primary="社区报告" />
          </ListItemButton>

          <ListItemButton
            selected={selectedTable === "covariates"}
            onClick={() => setSelectedTable("covariates")}
          >
            <ListItemText primary="协变量" />
          </ListItemButton>
        </List>
      </Drawer>
      <Box 
        p={3} 
        sx={{ 
          flexGrow: 1, 
          overflow: "auto",
          marginLeft: '240px', // 为左侧Drawer留出空间
          width: 'calc(100% - 240px)',
        }}
      >
        {selectedTable === "entities" && (
          <>
            <Typography variant="h4" gutterBottom>
              实体 (entities.parquet)
            </Typography>
            <DataTable columns={entityColumns} data={entities} />
          </>
        )}
        {selectedTable === "relationships" && (
          <>
            <Typography variant="h4" gutterBottom>
              关系 (relationships.parquet)
            </Typography>
            <DataTable columns={relationshipColumns} data={relationships} />
          </>
        )}
        {selectedTable === "documents" && (
          <>
            <Typography variant="h4" gutterBottom>
              文档 (documents.parquet)
            </Typography>
            <DataTable columns={documentColumns} data={documents} />
          </>
        )}
        {selectedTable === "textunits" && (
          <>
            <Typography variant="h4" gutterBottom>
              文本单元 (text_units.parquet)
            </Typography>
            <DataTable columns={textUnitColumns} data={textunits} />
          </>
        )}
        {selectedTable === "communities" && (
          <>
            <Typography variant="h4" gutterBottom>
              社区 (communities.parquet)
            </Typography>
            <DataTable columns={communityColumns} data={communities} />
          </>
        )}
        {selectedTable === "communityReports" && (
          <>
            <Typography variant="h4" gutterBottom>
              社区报告 (community_reports.parquet)
            </Typography>
            <DataTable
              columns={communityReportColumns}
              data={communityReports}
            />
          </>
        )}
        {selectedTable === "covariates" && (
          <>
            <Typography variant="h4" gutterBottom>
              协变量 (covariates.parquet)
            </Typography>
            <DataTable columns={covariateColumns} data={covariates} />
          </>
        )}
      </Box>
    </>
  );
};

export default DataTableContainer;
