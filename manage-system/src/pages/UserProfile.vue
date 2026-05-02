<template>
  <div class="content">
    <!-- 作者介绍区域 -->
    <div class="md-layout">
      <div class="md-layout-item md-size-100">
        <h2 style="text-align: center; color: #9c27b0; margin-bottom: 30px;">👨‍💻 项目开发团队</h2>
      </div>
      
      <!-- 成员1：杨文军 -->
      <div class="md-layout-item md-medium-size-100 md-size-33">
        <md-card class="md-card-profile md-theme-default">
          <div class="md-card-avatar">
            <img class="img" :src="teamImage" />
          </div>
          <md-card-content>
            <h6 class="category text-gray">项目参与者</h6>
            <h4 class="card-title">杨文军</h4>
            <p class="card-description">
              资深全栈开发工程师，专注于人工智能与知识图谱技术的研究与应用。擅长系统架构设计，
              在大语言模型、向量检索、分布式系统等领域有丰富的实战经验。本项目主要负责整体架构设计、
              后端开发以及 AI 技术集成，致力于打造高性能、智能化的教育问答系统。
            </p>
            <md-button class="md-round md-success">查看贡献</md-button>
          </md-card-content>
        </md-card>
      </div>

      <!-- 成员2：韦草原 -->
      <div class="md-layout-item md-medium-size-100 md-size-33">
        <md-card class="md-card-profile md-theme-default">
          <div class="md-card-avatar">
            <img class="img" :src="teamImage" />
          </div>
          <md-card-content>
            <h6 class="category text-gray">项目参与者</h6>
            <h4 class="card-title">韦草原</h4>
            <p class="card-description">
              专注于自然语言处理与知识图谱构建的算法工程师，对深度学习、GraphRAG 技术有深入研究。
              在本项目中主要负责知识图谱的设计与优化、检索算法的实现、以及前端交互体验的提升。
              善于将前沿的 AI 技术落地到实际应用场景，追求极致的用户体验与系统性能。
            </p>
            <md-button class="md-round md-info">查看贡献</md-button>
          </md-card-content>
        </md-card>
      </div>

      <!-- 成员3：洪基恒 -->
      <div class="md-layout-item md-medium-size-100 md-size-33">
        <md-card class="md-card-profile md-theme-default">
          <div class="md-card-avatar">
            <img class="img" :src="teamImage" />
          </div>
          <md-card-content>
            <h6 class="category text-gray">项目参与者</h6>
            <h4 class="card-title">洪基恒</h4>
            <p class="card-description">
              经验丰富的软件工程师，专注于前端开发与用户体验设计。在本项目中主要负责前端界面开发、
              用户交互优化以及系统测试工作。精通 Vue.js、React 等现代前端框架，
              注重代码质量与项目文档的完善，为项目的顺利推进提供了重要支持。
            </p>
            <md-button class="md-round md-warning">查看贡献</md-button>
          </md-card-content>
        </md-card>
      </div>
    </div>

    <!-- 项目介绍区域 -->
    <div class="md-layout" style="margin-top: 30px;">
      <div class="md-layout-item md-size-100">
        <md-card>
          <md-card-header data-background-color="purple">
            <h4 class="title">智能教育问答系统</h4>
            <p class="category">基于知识图谱与大语言模型的创新型教育平台</p>
          </md-card-header>
          <md-card-content>
            <div class="project-intro">
              <h3 style="color: #9c27b0; margin-top: 0;">🎓 项目亮点</h3>
              <p style="font-size: 16px; line-height: 1.8; color: #555;">
                本系统是一款融合了<strong>知识图谱、大语言模型（LLM）、向量检索</strong>等前沿技术的智能教育问答平台。
                通过深度整合 <strong>Neo4j 知识图谱</strong>、<strong>Qdrant 向量数据库</strong>、<strong>通义千问大模型</strong>以及 <strong>GraphRAG 技术</strong>，
                实现了精准、智能、个性化的知识检索与问答服务。
              </p>
              
              <h3 style="color: #9c27b0; margin-top: 25px;">✨ 核心功能</h3>
              <div class="md-layout" style="margin-top: 15px;">
                <div class="md-layout-item md-size-50 md-small-size-100">
                  <ul style="font-size: 15px; line-height: 2; color: #666;">
                    <li>📚 <strong>智能知识问答</strong>：基于知识图谱的语义理解与推理</li>
                    <li>🔍 <strong>混合检索引擎</strong>：结合向量检索与图谱查询</li>
                    <li>🎯 <strong>个性化推荐</strong>：根据用户历史提供精准答案</li>
                    <li>💬 <strong>多轮对话支持</strong>：上下文理解与连续问答</li>
                  </ul>
                </div>
                <div class="md-layout-item md-size-50 md-small-size-100">
                  <ul style="font-size: 15px; line-height: 2; color: #666;">
                    <li>🎤 <strong>语音交互</strong>：集成 ChatTTS 语音合成技术</li>
                    <li>📊 <strong>可视化分析</strong>：知识图谱可视化展示</li>
                    <li>🔐 <strong>权限管理</strong>：完善的用户权限与通知系统</li>
                    <li>⚡ <strong>高性能缓存</strong>：Redis 缓存加速响应速度</li>
                  </ul>
                </div>
              </div>

              <h3 style="color: #9c27b0; margin-top: 25px;">🚀 项目优势</h3>
              <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 8px; color: white; margin-top: 15px;">
                <p style="margin: 0; font-size: 15px; line-height: 1.8;">
                  ✓ <strong>技术前沿性</strong>：融合知识图谱、大模型、向量检索等多项前沿 AI 技术<br>
                  ✓ <strong>架构完善性</strong>：采用微服务架构，支持高并发、高可用、易扩展<br>
                  ✓ <strong>智能化程度高</strong>：深度语义理解与推理能力，提供精准的知识问答<br>
                  ✓ <strong>用户体验优</strong>：多模态交互（文本+语音），界面美观，操作流畅<br>
                  ✓ <strong>可视化丰富</strong>：知识图谱可视化展示，直观呈现知识关联关系
                </p>
              </div>

              <h3 style="color: #9c27b0; margin-top: 25px;">🛠️ 技术栈</h3>
              <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-top: 15px;">
                <span class="tech-badge">FastAPI</span>
                <span class="tech-badge">Vue.js</span>
                <span class="tech-badge">Neo4j</span>
                <span class="tech-badge">Qdrant</span>
                <span class="tech-badge">Redis</span>
                <span class="tech-badge">MySQL</span>
                <span class="tech-badge">通义千问</span>
                <span class="tech-badge">ChatTTS</span>
                <span class="tech-badge">Docker</span>
                <span class="tech-badge">WebSocket</span>
              </div>
            </div>
          </md-card-content>
        </md-card>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      teamImage: require("@/assets/img/faces/marc.jpg"),
    };
  },
};
</script>

<style scoped>
.project-intro {
  padding: 10px 20px;
}

.project-intro h3 {
  font-weight: 600;
  margin-bottom: 15px;
}

.project-intro ul {
  list-style: none;
  padding-left: 0;
}

.project-intro li {
  padding: 5px 0;
}

.tech-badge {
  display: inline-block;
  background: linear-gradient(60deg, #66bb6a, #43a047);
  color: white;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  box-shadow: 0 2px 5px rgba(0,0,0,0.15);
  transition: transform 0.2s;
}

.tech-badge:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}

.card-description {
  text-align: justify;
  line-height: 1.8;
  color: #666;
  font-size: 14px;
}

.md-card-profile {
  margin-bottom: 30px;
  min-height: 450px;
}

.md-card-profile .md-card-content {
  padding: 15px 30px;
}

.md-card-profile .card-title {
  margin: 10px 0;
  color: #3c4858;
  font-weight: 600;
}
</style>
