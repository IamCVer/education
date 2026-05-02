<template>
  <div class="group-chat-container" :class="{ 'dark-theme': isDarkTheme }">
    <!-- 左侧群聊列表 -->
    <div class="group-list-sidebar">
      <div class="sidebar-header">
        <h2>群聊</h2>
        <el-button 
          v-if="isTeacher" 
          type="primary" 
          size="small" 
          icon="el-icon-plus"
          @click="showCreateGroupDialog = true"
        >
          创建群聊
        </el-button>
      </div>

      <div class="group-list">
        <!-- 加载状态 -->
        <div v-if="groupsLoading" class="empty-state">
          <i class="el-icon-loading" style="font-size: 40px; color: #8b7fd6;"></i>
          <p>加载中...</p>
        </div>

        <template v-else>
          <div 
            v-for="group in groups" 
            :key="group.id"
            class="group-item"
            :class="{ 'active': selectedGroup && selectedGroup.id === group.id }"
            @click="selectGroup(group)"
          >
            <div class="group-icon">
              <i class="el-icon-chat-dot-round"></i>
            </div>
            <div class="group-info">
              <div class="group-name">{{ group.name }}</div>
              <div class="group-meta">{{ group.member_count }} 人</div>
            </div>
          </div>

          <div v-if="groups.length === 0" class="empty-state">
            <i class="el-icon-chat-line-round"></i>
            <p>暂无群聊</p>
            <p v-if="isTeacher" class="hint">点击上方按钮创建群聊</p>
          </div>
        </template>
      </div>
    </div>

    <!-- 右侧聊天区域 -->
    <div class="chat-area">
      <div v-if="!selectedGroup" class="no-selection">
        <i class="el-icon-chat-dot-round"></i>
        <p>请选择一个群聊开始对话</p>
      </div>

      <div v-else class="chat-content">
        <!-- 聊天头部 -->
        <div class="chat-header">
          <div class="header-left">
            <h3>{{ selectedGroup.name }}</h3>
            <span class="member-count">
              <i class="el-icon-user"></i>
              {{ selectedGroup.member_count }} 人
            </span>
          </div>
          <div class="header-right">
            <el-button 
              size="small" 
              icon="el-icon-user"
              @click="showMembersDialog = true"
            >
              查看成员
            </el-button>
            <el-button 
              size="small" 
              icon="el-icon-folder-opened"
              @click="openFilesDialog"
            >
              查看文件
            </el-button>
            <el-button 
              size="small" 
              icon="el-icon-bell"
              @click="openAnnouncementViewDialog"
            >
              查看公告
            </el-button>
            <el-button 
              v-if="isTeacher" 
              size="small" 
              icon="el-icon-plus"
              @click="showTeacherInviteDialog = true"
            >
              邀请成员
            </el-button>
            <el-button 
              v-if="isTeacher"
              size="small" 
              icon="el-icon-document-checked"
              @click="showPendingInvitationsDialog = true"
            >
              审核邀请
            </el-button>
            <el-button 
              v-if="!isTeacher"
              size="small" 
              icon="el-icon-user-add"
              @click="showStudentInviteDialog = true"
            >
              邀请成员
            </el-button>
          </div>
        </div>

        <!-- 消息列表 -->
        <div class="messages-container" ref="messagesContainer">
          <div 
            v-for="(message, index) in messages" 
            :key="index"
            class="message"
            :class="getMessageClass(message)"
          >
            <div class="message-avatar">
              <div v-if="message.message_type === 'ai_response'" class="ai-avatar">
                🤖
              </div>
              <div v-else-if="message.sender_role === 'teacher'" class="teacher-avatar">
                <i class="el-icon-user-solid"></i>
              </div>
              <div v-else class="student-avatar">
                <i class="el-icon-user"></i>
              </div>
            </div>
            <div class="message-content">
              <div class="message-header">
                <span class="sender-name">
                  {{ message.sender_name }}
                  <span v-if="message.message_type === 'ai_response'" class="role-badge ai-badge">AI管家</span>
                  <span v-else-if="message.sender_role === 'teacher'" class="role-badge teacher-badge">老师</span>
                  <span v-else-if="message.sender_role === 'student'" class="role-badge student-badge">学生</span>
                </span>
                <span class="message-time">{{ formatTime(message.created_at) }}</span>
              </div>
              <div class="message-text" v-html="renderMessage(message.message)"></div>
            </div>
          </div>

          <div v-if="isLoading" class="loading-message">
            <i class="el-icon-loading"></i>
            <span>加载中...</span>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="input-container">
          <!-- 功能按钮栏 -->
          <div class="input-actions">
            <!-- 文件上传 -->
            <el-upload
              :action="`/api/v1/groups/${selectedGroup.id}/upload-file`"
              :show-file-list="false"
              :on-success="handleUploadSuccess"
              :on-error="handleUploadError"
              :before-upload="beforeUpload"
              :headers="uploadHeaders"
              style="display: inline-block; margin-right: 8px;"
            >
              <el-button 
                size="small" 
                icon="el-icon-paperclip"
                :loading="uploadingFile"
              >
                上传文件
              </el-button>
            </el-upload>

            <!-- 搜索消息 -->
            <el-button 
              size="small" 
              icon="el-icon-search"
              @click="openSearchDialog"
            >
              搜索
            </el-button>

            <!-- 查看置顶消息 -->
            <el-button 
              size="small" 
              icon="el-icon-star-on"
              @click="showPinnedPanel = true"
              v-if="pinnedMessages.length > 0"
            >
              置顶 ({{ pinnedMessages.length }})
            </el-button>

            <!-- 群公告（仅老师） -->
            <el-button 
              v-if="isTeacher"
              size="small" 
              icon="el-icon-bell"
              @click="showAnnouncementDialog = true"
            >
              设置公告
            </el-button>

            <!-- AI助手（仅老师） -->
            <el-button 
              v-if="isTeacher"
              size="small" 
              type="primary"
              icon="el-icon-magic-stick"
              @click="showAIDialog = true"
            >
              问AI助手
            </el-button>
          </div>

          <!-- 回复提示 -->
          <div v-if="replyingTo" class="reply-hint">
            <span>回复 @{{ replyingTo.sender_name }}</span>
            <i class="el-icon-close" @click="cancelReply"></i>
          </div>

          <!-- 输入框 -->
          <div class="input-box">
            <el-input
              v-model="messageInput"
              type="textarea"
              :rows="3"
              placeholder="输入消息... (Ctrl+Enter发送)"
              @keydown.enter.ctrl="sendMessage"
            ></el-input>
            <el-button 
              type="primary" 
              icon="el-icon-s-promotion"
              @click="sendMessage"
              :disabled="!messageInput.trim()"
            >
              发送
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建群聊对话框 -->
    <el-dialog
      title="创建群聊"
      :visible.sync="showCreateGroupDialog"
      width="500px"
    >
      <el-form :model="createGroupForm" label-width="80px">
        <el-form-item label="群聊名称">
          <el-input v-model="createGroupForm.groupName" placeholder="请输入群聊名称"></el-input>
        </el-form-item>
        <el-form-item label="选择学生">
          <el-select
            v-model="createGroupForm.studentIds"
            multiple
            filterable
            placeholder="请选择学生"
            style="width: 100%"
          >
            <el-option
              v-for="student in students"
              :key="student.id"
              :label="student.username"
              :value="student.id"
            >
            </el-option>
          </el-select>
        </el-form-item>
      </el-form>
      <span slot="footer">
        <el-button @click="showCreateGroupDialog = false">取消</el-button>
        <el-button type="primary" @click="createGroup" :loading="creating">创建</el-button>
      </span>
    </el-dialog>

    <!-- 老师邀请对话框 -->
    <el-dialog
      title="邀请成员"
      :visible.sync="showTeacherInviteDialog"
      width="500px"
    >
      <el-select
        v-model="teacherInviteUserIds"
        multiple
        filterable
        placeholder="请选择要邀请的成员"
        style="width: 100%"
      >
        <el-option
          v-for="user in allUsers"
          :key="user.id"
          :label="user.email"
          :value="user.id"
        >
        </el-option>
      </el-select>
      <span slot="footer">
        <el-button @click="showTeacherInviteDialog = false">取消</el-button>
        <el-button type="primary" @click="teacherInviteUsers" :loading="inviting">邀请</el-button>
      </span>
    </el-dialog>

    <!-- 学生邀请对话框 -->
    <el-dialog
      title="邀请成员"
      :visible.sync="showStudentInviteDialog"
      width="500px"
    >
      <el-form :model="studentInviteForm" label-width="80px">
        <el-form-item label="邀请对象">
          <el-select
            v-model="studentInviteForm.invitedUserId"
            filterable
            placeholder="请选择要邀请的成员"
            style="width: 100%"
          >
            <el-option
              v-for="user in allUsers"
              :key="user.id"
              :label="user.email"
              :value="user.id"
            >
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="邀请理由">
          <el-input
            v-model="studentInviteForm.reason"
            type="textarea"
            :rows="3"
            placeholder="请输入邀请理由（老师会根据理由决定是否批准）"
          ></el-input>
        </el-form-item>
      </el-form>
      <span slot="footer">
        <el-button @click="showStudentInviteDialog = false">取消</el-button>
        <el-button type="primary" @click="studentInviteUser" :loading="inviting">发送邀请</el-button>
      </span>
    </el-dialog>

    <!-- 待审核邀请对话框 -->
    <el-dialog
      title="审核邀请"
      :visible.sync="showPendingInvitationsDialog"
      width="700px"
    >
      <div v-if="loadingInvitations" style="text-align: center; padding: 40px;">
        <i class="el-icon-loading" style="font-size: 32px; color: #8b7fd6;"></i>
        <p style="margin-top: 10px; color: #999;">加载中...</p>
      </div>
      <div v-else-if="pendingInvitations.length > 0" style="max-height: 500px; overflow-y: auto;">
        <div 
          v-for="invitation in pendingInvitations" 
          :key="invitation.id"
          style="padding: 15px; border: 1px solid #e0e0e0; border-radius: 4px; margin-bottom: 10px;"
        >
          <div style="display: flex; justify-content: space-between; align-items: start;">
            <div style="flex: 1;">
              <div style="font-weight: bold; margin-bottom: 8px;">
                <span style="color: #8b7fd6;">{{ invitation.inviter_name }}</span>
                <span style="color: #999; font-size: 12px; margin-left: 8px;">{{ invitation.inviter_role === 'teacher' ? '老师' : '学生' }}</span>
                邀请
                <span style="color: #8b7fd6;">{{ invitation.invited_user_name }}</span>
              </div>
              <div v-if="invitation.reason" style="margin-bottom: 8px; padding: 8px; background: #f5f5f5; border-radius: 4px;">
                <div style="font-size: 12px; color: #999; margin-bottom: 4px;">邀请理由：</div>
                <div style="color: #333;">{{ invitation.reason }}</div>
              </div>
              <div style="font-size: 12px; color: #999;">
                {{ formatTime(invitation.created_at) }}
              </div>
            </div>
            <div style="margin-left: 15px;">
              <el-button 
                size="small" 
                type="success"
                @click="approveInvitation(invitation.id)"
                :loading="reviewingInvitationId === invitation.id"
              >
                批准
              </el-button>
              <el-button 
                size="small" 
                @click="showRejectDialog(invitation.id)"
              >
                拒绝
              </el-button>
            </div>
          </div>
        </div>
      </div>
      <div v-else style="text-align: center; padding: 60px; color: #999;">
        <i class="el-icon-document-checked" style="font-size: 48px; color: #ddd;"></i>
        <p style="margin-top: 15px;">暂无待审核邀请</p>
      </div>
    </el-dialog>

    <!-- 拒绝邀请对话框 -->
    <el-dialog
      title="拒绝邀请"
      :visible.sync="showRejectDialog"
      width="400px"
    >
      <el-input
        v-model="rejectReason"
        type="textarea"
        :rows="3"
        placeholder="请输入拒绝理由（可选）"
      ></el-input>
      <span slot="footer">
        <el-button @click="showRejectDialog = false">取消</el-button>
        <el-button type="primary" @click="rejectInvitation" :loading="rejectingInvitation">拒绝</el-button>
      </span>
    </el-dialog>

    <!-- AI提问对话框 -->
    <el-dialog
      title="向AI助手提问"
      :visible.sync="showAIDialog"
      width="500px"
    >
      <el-input
        v-model="aiQuestion"
        type="textarea"
        :rows="4"
        placeholder="请输入您的问题..."
      ></el-input>
      <span slot="footer">
        <el-button @click="showAIDialog = false">取消</el-button>
        <el-button type="primary" @click="askAI" :loading="asking">提问</el-button>
      </span>
    </el-dialog>

    <!-- 搜索对话框 -->
    <el-dialog
      title="搜索消息"
      :visible.sync="showSearchDialog"
      width="600px"
    >
      <el-input
        v-model="searchQuery"
        placeholder="输入关键词搜索..."
        @keyup.enter.native="searchMessages"
      >
        <el-button slot="append" icon="el-icon-search" @click="searchMessages" :loading="searching">搜索</el-button>
      </el-input>
      <div v-if="searchResults.length > 0" class="search-results" style="margin-top: 20px; max-height: 400px; overflow-y: auto;">
        <div v-for="(result, index) in searchResults" :key="index" class="search-result-item" style="padding: 10px; border-bottom: 1px solid #eee;">
          <div style="font-weight: bold; color: #6c5dd3;">{{ result.sender_name }}</div>
          <div style="margin: 5px 0;">{{ result.message }}</div>
          <div style="font-size: 12px; color: #999;">{{ formatTime(result.created_at) }}</div>
        </div>
      </div>
      <div v-else-if="searching" style="text-align: center; padding: 20px; color: #999;">
        搜索中...
      </div>
      <div v-else style="text-align: center; padding: 20px; color: #999;">
        {{ searchQuery ? '未找到相关消息' : '请输入关键词进行搜索' }}
      </div>
    </el-dialog>

    <!-- 置顶消息面板 -->
    <el-dialog
      title="置顶消息"
      :visible.sync="showPinnedPanel"
      width="600px"
    >
      <div v-if="pinnedMessages.length > 0" style="max-height: 400px; overflow-y: auto;">
        <div v-for="(msg, index) in pinnedMessages" :key="index" class="pinned-message-item" style="padding: 15px; border-bottom: 1px solid #eee; position: relative;">
          <div style="font-weight: bold; color: #6c5dd3; margin-bottom: 5px;">{{ msg.sender_name }}</div>
          <div style="margin: 5px 0;">{{ msg.message }}</div>
          <div style="font-size: 12px; color: #999;">{{ formatTime(msg.created_at) }}</div>
          <el-button 
            v-if="isTeacher" 
            type="text" 
            size="mini" 
            icon="el-icon-close"
            style="position: absolute; top: 10px; right: 10px;"
            @click="unpinMessage(msg.id)"
          >
            取消置顶
          </el-button>
        </div>
      </div>
      <div v-else style="text-align: center; padding: 40px; color: #999;">
        暂无置顶消息
      </div>
    </el-dialog>

    <!-- 设置公告对话框 -->
    <el-dialog
      title="设置群公告"
      :visible.sync="showAnnouncementDialog"
      width="500px"
    >
      <el-input
        v-model="announcementText"
        type="textarea"
        :rows="4"
        placeholder="请输入群公告内容..."
      ></el-input>
      <div v-if="announcement" style="margin-top: 15px; padding: 10px; background: #f5f5f5; border-radius: 4px;">
        <div style="font-size: 12px; color: #999; margin-bottom: 5px;">当前公告：</div>
        <div>{{ announcement }}</div>
      </div>
      <span slot="footer">
        <el-button @click="showAnnouncementDialog = false">取消</el-button>
        <el-button type="primary" @click="setAnnouncement">设置</el-button>
      </span>
    </el-dialog>

    <!-- 查看文件列表对话框 -->
    <el-dialog
      title="群文件"
      :visible.sync="showFilesDialog"
      width="700px"
    >
      <div v-if="loadingFiles" style="text-align: center; padding: 40px;">
        <i class="el-icon-loading" style="font-size: 32px; color: #8b7fd6;"></i>
        <p style="margin-top: 15px; color: #999;">加载中...</p>
      </div>
      <div v-else-if="groupFiles.length > 0" style="max-height: 500px; overflow-y: auto;">
        <div 
          v-for="(file, index) in groupFiles" 
          :key="index" 
          class="file-item"
        >
          <div class="file-info">
            <i class="el-icon-document" style="font-size: 24px; color: #8b7fd6; margin-right: 12px;"></i>
            <div class="file-details">
              <div class="file-name">{{ file.name }}</div>
              <div class="file-meta">
                <span>{{ formatFileSize(file.size) }}</span>
                <span style="margin: 0 8px;">·</span>
                <span>{{ file.uploader }}</span>
                <span style="margin: 0 8px;">·</span>
                <span>{{ formatTime(file.created_at) }}</span>
              </div>
            </div>
          </div>
          <div class="file-actions">
            <el-button 
              size="mini" 
              type="primary" 
              icon="el-icon-download"
              @click="downloadFile(file)"
            >
              下载
            </el-button>
          </div>
        </div>
      </div>
      <div v-else style="text-align: center; padding: 60px; color: #999;">
        <i class="el-icon-folder-opened" style="font-size: 48px; color: #ddd;"></i>
        <p style="margin-top: 15px;">暂无文件</p>
      </div>
    </el-dialog>

    <!-- 查看公告对话框 -->
    <el-dialog
      title="群公告"
      :visible.sync="showAnnouncementViewDialog"
      width="600px"
    >
      <div v-if="announcement" style="padding: 20px; background: #f8f7fd; border-radius: 8px; border-left: 4px solid #8b7fd6;">
        <div style="white-space: pre-wrap; line-height: 1.8; color: #333;">{{ announcement }}</div>
      </div>
      <div v-else style="text-align: center; padding: 60px; color: #999;">
        <i class="el-icon-bell" style="font-size: 48px; color: #ddd;"></i>
        <p style="margin-top: 15px;">暂无公告</p>
      </div>
      <span slot="footer" v-if="isTeacher">
        <el-button type="primary" @click="showAnnouncementDialog = true; showAnnouncementViewDialog = false">
          <i class="el-icon-edit"></i> 编辑公告
        </el-button>
      </span>
    </el-dialog>

    <!-- 查看成员对话框 -->
    <el-dialog
      title="群成员"
      :visible.sync="showMembersDialog"
      width="500px"
    >
      <div v-if="loadingMembers" style="text-align: center; padding: 40px;">
        <i class="el-icon-loading" style="font-size: 32px; color: #8b7fd6;"></i>
        <p style="margin-top: 10px; color: #999;">加载中...</p>
      </div>
      <div v-else-if="groupMembers.length > 0" class="members-list">
        <div 
          v-for="member in groupMembers" 
          :key="member.id"
          class="member-item"
        >
          <div class="member-avatar">
            <i v-if="member.role === 'teacher'" class="el-icon-user-solid" style="color: #8b7fd6;"></i>
            <i v-else class="el-icon-user" style="color: #67c23a;"></i>
          </div>
          <div class="member-info">
            <div class="member-name">{{ member.username }}</div>
            <div class="member-email">{{ member.email }}</div>
          </div>
          <div class="member-role">
            <el-tag :type="member.role === 'teacher' ? 'primary' : 'success'" size="small">
              {{ member.role_display }}
            </el-tag>
          </div>
        </div>
      </div>
      <div v-else style="text-align: center; padding: 60px; color: #999;">
        <i class="el-icon-user" style="font-size: 48px; color: #ddd;"></i>
        <p style="margin-top: 15px;">暂无成员</p>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import request from '@/utils/request'

export default {
  name: 'GroupChatPage',
  data() {
    return {
      isDarkTheme: false,
      groups: [],
      groupsLoading: false,
      selectedGroup: null,
      messages: [],
      messageInput: '',
      students: [],
      isLoading: false,
      creating: false,
      inviting: false,
      asking: false,
      showCreateGroupDialog: false,
      showInviteDialog: false,
      showAIDialog: false,
      createGroupForm: {
        groupName: '',
        studentIds: []
      },
      inviteStudentIds: [],
      aiQuestion: '',
      ws: null,  // WebSocket连接
      reconnectTimer: null,
      
      // 新增功能相关
      searchQuery: '',
      searchResults: [],
      showSearchDialog: false,
      searching: false,
      
      pinnedMessages: [],
      showPinnedPanel: false,
      
      showAnnouncementDialog: false,
      announcement: '',
      
      // 成员列表相关
      showMembersDialog: false,
      groupMembers: [],
      loadingMembers: false,
      announcementText: '',
      
      replyingTo: null,  // 正在回复的消息
      showThreadDialog: false,
      threadMessages: [],
      currentThreadPost: null,
      
      selectedMentions: [],  // 选中要@的用户
      showMentionSelector: false,
      
      uploadingFile: false,
      groupMembers: [],  // 群聊成员列表
      
      // 文件和公告相关
      showFilesDialog: false,
      showAnnouncementViewDialog: false,
      groupFiles: [],
      loadingFiles: false,
      
      // 邀请审核功能相关
      showTeacherInviteDialog: false,
      showStudentInviteDialog: false,
      showPendingInvitationsDialog: false,
      showRejectDialog: false,
      teacherInviteUserIds: [],
      studentInviteForm: {
        invitedUserId: null,
        reason: ''
      },
      pendingInvitations: [],
      loadingInvitations: false,
      rejectReason: '',
      rejectingInvitation: false,
      reviewingInvitationId: null,
      rejectingInvitationId: null,
      allUsers: []
    }
  },
  computed: {
    isTeacher() {
      const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}')
      return userInfo.role === 'teacher'
    },
    uploadHeaders() {
      return {
        'Authorization': `Bearer ${localStorage.getItem('userToken')}`
      }
    }
  },
  watch: {
    showMembersDialog(newVal) {
      if (newVal) {
        this.loadGroupMembers()
      }
    },
    showPendingInvitationsDialog(newVal) {
      if (newVal) {
        this.loadPendingInvitations()
      }
    },
    showTeacherInviteDialog(newVal) {
      if (newVal) {
        this.loadAllUsers()
      }
    },
    showStudentInviteDialog(newVal) {
      if (newVal) {
        this.loadAllUsers()
      }
    }
  },
  mounted() {
    this.loadGroups()
    this.loadAllUsers()
    if (this.isTeacher) {
      this.loadStudents()
    }
  },
  beforeDestroy() {
    // 组件销毁时关闭WebSocket连接
    this.closeWebSocket()
  },
  methods: {
    async loadGroups() {
      this.groupsLoading = true
      try {
        const response = await request.get('/api/v1/groups')
        this.groups = response.groups || []
      } catch (error) {
        this.$message.error('加载群聊列表失败')
        console.error(error)
      } finally {
        this.groupsLoading = false
      }
    },

    async loadStudents() {
      try {
        const response = await request.get('/api/v1/users/students')
        this.students = response || []
      } catch (error) {
        this.$message.error('加载学生列表失败')
        console.error(error)
      }
    },

    async loadGroupMembers() {
      if (!this.selectedGroup) return
      
      this.loadingMembers = true
      try {
        const response = await request.get(`/api/v1/groups/${this.selectedGroup.id}/members`)
        this.groupMembers = response.members || []
      } catch (error) {
        this.$message.error('加载成员列表失败')
        console.error(error)
      } finally {
        this.loadingMembers = false
      }
    },

    async selectGroup(group) {
      // 关闭之前的WebSocket连接
      this.closeWebSocket()
      
      this.selectedGroup = group
      await this.loadMessages(group.id)
      
      // 加载公告和置顶消息
      await this.loadAnnouncement()
      await this.loadPinnedMessages()
      
      // 建立新的WebSocket连接
      this.connectWebSocket(group.id)
    },

    async loadMessages(groupId) {
      this.isLoading = true
      try {
        const response = await request.get(`/api/v1/groups/${groupId}/messages`)
        
        // 确保 response 是数组
        const messages = Array.isArray(response) ? response : (response?.data || response?.messages || [])
        
        this.messages = messages
        this.$nextTick(() => {
          this.scrollToBottom()
        })
      } catch (error) {
        console.error('加载消息时出错:', error)
        this.$message.error(`加载消息失败: ${error.message || '未知错误'}`)
      } finally {
        this.isLoading = false
      }
    },

    async createGroup() {
      if (!this.createGroupForm.groupName.trim()) {
        this.$message.warning('请输入群聊名称')
        return
      }
      if (this.createGroupForm.studentIds.length === 0) {
        this.$message.warning('请至少选择一名学生')
        return
      }

      this.creating = true
      try {
        await request.post('/api/v1/groups/create', {
          group_name: this.createGroupForm.groupName,
          student_ids: this.createGroupForm.studentIds
        })
        this.$message.success('创建成功')
        this.showCreateGroupDialog = false
        this.createGroupForm = { groupName: '', studentIds: [] }
        await this.loadGroups()
      } catch (error) {
        this.$message.error('创建失败')
        console.error(error)
      } finally {
        this.creating = false
      }
    },

    async sendMessage() {
      if (!this.messageInput.trim() || !this.selectedGroup) return

      try {
        // 如果是回复消息，使用回复接口
        if (this.replyingTo) {
          await this.sendReply()
          return
        }
        
        // 如果有@提及，使用提及接口
        if (this.selectedMentions.length > 0) {
          await this.sendMessageWithMentions()
          return
        }
        
        // 普通消息
        await request.post(`/api/v1/groups/${this.selectedGroup.id}/send`, {
          message: this.messageInput
        })
        this.messageInput = ''
        await this.loadMessages(this.selectedGroup.id)
      } catch (error) {
        this.$message.error('发送失败')
        console.error(error)
      }
    },

    async inviteStudents() {
      if (this.inviteStudentIds.length === 0) {
        this.$message.warning('请选择要邀请的学生')
        return
      }

      this.inviting = true
      try {
        await request.post(`/api/v1/groups/${this.selectedGroup.id}/invite`, {
          student_ids: this.inviteStudentIds
        })
        this.$message.success('邀请成功')
        this.showInviteDialog = false
        this.inviteStudentIds = []
        await this.loadGroups()
      } catch (error) {
        this.$message.error('邀请失败')
        console.error(error)
      } finally {
        this.inviting = false
      }
    },

    async askAI() {
      if (!this.aiQuestion.trim()) {
        this.$message.warning('请输入问题')
        return
      }

      this.asking = true
      try {
        await request.post(`/api/v1/groups/${this.selectedGroup.id}/ai-ask`, {
          question: this.aiQuestion
        })
        this.$message.success('AI正在思考中，请稍候...')
        this.showAIDialog = false
        this.aiQuestion = ''
        // 延迟加载消息，等待AI回答
        setTimeout(() => {
          this.loadMessages(this.selectedGroup.id)
        }, 2000)
      } catch (error) {
        this.$message.error('提问失败')
        console.error(error)
      } finally {
        this.asking = false
      }
    },

    getMessageClass(message) {
      if (message.message_type === 'ai_response') {
        return 'ai-message'
      }
      const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}')
      return message.sender_id === userInfo.id ? 'my-message' : 'other-message'
    },

    renderMessage(text) {
      // 简单的Markdown渲染
      return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>')
    },

    formatTime(timestamp) {
      const date = new Date(parseInt(timestamp))
      const now = new Date()
      const diff = now - date

      if (diff < 60000) return '刚刚'
      if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
      if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
      
      return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`
    },

    scrollToBottom() {
      if (this.$refs.messagesContainer) {
        this.$refs.messagesContainer.scrollTop = this.$refs.messagesContainer.scrollHeight
      }
    },

    // ========== WebSocket 相关方法 ==========

    connectWebSocket(groupId) {
      const token = localStorage.getItem('userToken')
      if (!token) {
        console.error('No token found')
        return
      }

      // 使用相对路径，通过 nginx 代理转发 WebSocket，避免硬编码端口
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${wsProtocol}//${window.location.host}/api/v1/ws/groups/${groupId}?token=${token}`

      console.log('Connecting to WebSocket:', wsUrl)

      try {
        this.ws = new WebSocket(wsUrl)

        this.ws.onopen = () => {
          console.log('WebSocket connected to group:', groupId)
          // 发送心跳包
          this.startHeartbeat()
        }

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            this.handleWebSocketMessage(data)
          } catch (error) {
            console.error('Error parsing WebSocket message:', error)
          }
        }

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error)
        }

        this.ws.onclose = () => {
          console.log('WebSocket disconnected from group:', groupId)
          this.stopHeartbeat()
          // 尝试重连
          this.scheduleReconnect(groupId)
        }
      } catch (error) {
        console.error('Error creating WebSocket:', error)
      }
    },

    handleWebSocketMessage(data) {
      console.log('Received WebSocket message:', data)

      switch (data.type) {
        case 'new_message':
          // 新消息
          this.messages.push(data.message)
          this.$nextTick(() => {
            this.scrollToBottom()
          })
          break

        case 'member_joined':
          // 成员加入
          this.$message.info(`有新成员加入群聊`)
          if (this.selectedGroup) {
            this.selectedGroup.member_count = data.online_count
          }
          break

        case 'member_left':
          // 成员离开
          if (this.selectedGroup) {
            this.selectedGroup.member_count = data.online_count
          }
          break

        case 'ai_thinking':
          // AI正在思考
          this.$message.info(data.message)
          break

        case 'ai_response_ready':
          // AI回答就绪，重新加载消息
          console.log('AI 回答就绪，开始重新加载消息...')
          this.$message.success(data.message)
          if (this.selectedGroup) {
            console.log('正在加载群组消息，群组ID:', this.selectedGroup.id)
            this.loadMessages(this.selectedGroup.id).then(() => {
              console.log('消息加载完成，当前消息数量:', this.messages.length)
              console.log('最新消息:', this.messages[this.messages.length - 1])
            }).catch(error => {
              console.error('加载消息时出错:', error)
            })
          }
          break

        case 'ai_error':
          // AI回答失败
          this.$message.error(data.message)
          break

        default:
          console.log('Unknown message type:', data.type)
      }
    },

    closeWebSocket() {
      this.stopHeartbeat()
      if (this.ws) {
        this.ws.close()
        this.ws = null
      }
      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer)
        this.reconnectTimer = null
      }
    },

    startHeartbeat() {
      // 每30秒发送一次心跳包
      this.heartbeatTimer = setInterval(() => {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
          this.ws.send('ping')
        }
      }, 30000)
    },

    stopHeartbeat() {
      if (this.heartbeatTimer) {
        clearInterval(this.heartbeatTimer)
        this.heartbeatTimer = null
      }
    },

    scheduleReconnect(groupId) {
      // 5秒后尝试重连
      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer)
      }
      this.reconnectTimer = setTimeout(() => {
        if (this.selectedGroup && this.selectedGroup.id === groupId) {
          console.log('Attempting to reconnect...')
          this.connectWebSocket(groupId)
        }
      }, 5000)
    },

    // ========== 新增功能方法 ==========
    
    // 文件上传
    async handleFileUpload(event) {
      const file = event.target.files[0]
      if (!file) return
      
      // 文件大小限制 (10MB)
      if (file.size > 10 * 1024 * 1024) {
        this.$message.error('文件大小不能超过10MB')
        return
      }
      
      this.uploadingFile = true
      try {
        const formData = new FormData()
        formData.append('file', file)
        
        await request.post(
          `/api/v1/groups/${this.selectedGroup.id}/upload-file`,
          formData,
          {
            headers: { 'Content-Type': 'multipart/form-data' }
          }
        )
        
        this.$message.success('文件上传成功')
        await this.loadMessages(this.selectedGroup.id)
      } catch (error) {
        this.$message.error('文件上传失败')
        console.error(error)
      } finally {
        this.uploadingFile = false
        // 清空input
        event.target.value = ''
      }
    },
    
    // 打开搜索对话框
    openSearchDialog() {
      this.searchQuery = ''
      this.searchResults = []
      this.searching = false
      this.showSearchDialog = true
    },

    // 搜索消息
    async searchMessages() {
      if (!this.searchQuery.trim()) {
        this.$message.warning('请输入搜索关键词')
        return
      }
      
      this.searching = true
      try {
        const response = await request.post(
          `/api/v1/groups/${this.selectedGroup.id}/search`,
          { query: this.searchQuery, limit: 20 }
        )
        this.searchResults = response
        if (response.length > 0) {
          this.$message.success(`找到 ${response.length} 条消息`)
        } else {
          this.$message.info('未找到相关消息')
        }
      } catch (error) {
        this.$message.error('搜索失败: ' + (error.message || '未知错误'))
        console.error(error)
      } finally {
        this.searching = false
      }
    },
    
    // 置顶消息
    async pinMessage(postId) {
      try {
        await request.post(`/api/v1/groups/${this.selectedGroup.id}/pin`, {
          post_id: postId
        })
        this.$message.success('消息已置顶')
        await this.loadPinnedMessages()
        await this.loadMessages(this.selectedGroup.id)
      } catch (error) {
        this.$message.error('置顶失败')
        console.error(error)
      }
    },
    
    // 取消置顶
    async unpinMessage(postId) {
      try {
        await request.post(`/api/v1/groups/${this.selectedGroup.id}/unpin`, {
          post_id: postId
        })
        this.$message.success('已取消置顶')
        await this.loadPinnedMessages()
        await this.loadMessages(this.selectedGroup.id)
      } catch (error) {
        this.$message.error('取消置顶失败')
        console.error(error)
      }
    },
    
    // 加载置顶消息
    async loadPinnedMessages() {
      if (!this.selectedGroup) return
      
      try {
        const response = await request.get(
          `/api/v1/groups/${this.selectedGroup.id}/pinned`
        )
        this.pinnedMessages = response
      } catch (error) {
        console.error('加载置顶消息失败:', error)
      }
    },
    
    // 回复消息
    replyToMessage(message) {
      this.replyingTo = message
      this.messageInput = `回复 @${message.sender_name}: `
      // 聚焦到输入框
      this.$nextTick(() => {
        const textarea = this.$el.querySelector('.el-textarea__inner')
        if (textarea) textarea.focus()
      })
    },
    
    // 取消回复
    cancelReply() {
      this.replyingTo = null
      this.messageInput = ''
    },
    
    // 发送回复
    async sendReply() {
      if (!this.messageInput.trim() || !this.replyingTo) return
      
      try {
        await request.post(
          `/api/v1/groups/${this.selectedGroup.id}/reply`,
          {
            root_post_id: this.replyingTo.id,
            message: this.messageInput
          }
        )
        this.messageInput = ''
        this.replyingTo = null
        await this.loadMessages(this.selectedGroup.id)
      } catch (error) {
        this.$message.error('回复失败')
        console.error(error)
      }
    },
    
    // 查看线程
    async viewThread(postId) {
      try {
        const response = await request.get(
          `/api/v1/groups/${this.selectedGroup.id}/thread/${postId}`
        )
        this.threadMessages = response
        this.currentThreadPost = postId
        this.showThreadDialog = true
      } catch (error) {
        this.$message.error('加载线程失败')
        console.error(error)
      }
    },
    
    // 设置公告
    async setAnnouncement() {
      if (!this.announcementText.trim()) {
        this.$message.warning('请输入公告内容')
        return
      }
      
      try {
        await request.post(
          `/api/v1/groups/${this.selectedGroup.id}/announcement`,
          { announcement: this.announcementText }
        )
        this.$message.success('公告已设置')
        this.showAnnouncementDialog = false
        await this.loadAnnouncement()
      } catch (error) {
        this.$message.error('设置公告失败')
        console.error(error)
      }
    },
    
    // 加载公告
    async loadAnnouncement() {
      if (!this.selectedGroup) return
      
      try {
        const response = await request.get(
          `/api/v1/groups/${this.selectedGroup.id}/announcement`
        )
        this.announcement = response.announcement
      } catch (error) {
        console.error('加载公告失败:', error)
      }
    },
    
    // @提及用户
    toggleMention(userId) {
      const index = this.selectedMentions.indexOf(userId)
      if (index > -1) {
        this.selectedMentions.splice(index, 1)
      } else {
        this.selectedMentions.push(userId)
      }
    },
    
    // 发送带@的消息
    async sendMessageWithMentions() {
      if (!this.messageInput.trim()) return
      
      try {
        if (this.selectedMentions.length > 0) {
          await request.post(
            `/api/v1/groups/${this.selectedGroup.id}/send-with-mentions`,
            {
              message: this.messageInput,
              mention_user_ids: this.selectedMentions
            }
          )
        } else {
          await this.sendMessage()
          return
        }
        
        this.messageInput = ''
        this.selectedMentions = []
        this.showMentionSelector = false
        await this.loadMessages(this.selectedGroup.id)
      } catch (error) {
        this.$message.error('发送失败')
        console.error(error)
      }
    },

    // 文件上传前的验证
    beforeUpload(file) {
      const isLt10M = file.size / 1024 / 1024 < 10
      if (!isLt10M) {
        this.$message.error('文件大小不能超过 10MB!')
        return false
      }
      this.uploadingFile = true
      return true
    },

    // 文件上传成功回调
    handleUploadSuccess(response, file) {
      this.uploadingFile = false
      this.$message.success('文件上传成功')
      this.loadMessages(this.selectedGroup.id)
    },

    // 文件上传失败回调
    handleUploadError(err, file) {
      this.uploadingFile = false
      this.$message.error('文件上传失败: ' + (err.message || '未知错误'))
      console.error('Upload error:', err)
    },

    // 打开文件列表对话框
    async openFilesDialog() {
      this.showFilesDialog = true
      this.loadingFiles = true
      try {
        const response = await request.get(`/api/v1/groups/${this.selectedGroup.id}/files`)
        this.groupFiles = response
      } catch (error) {
        this.$message.error('获取文件列表失败')
        console.error(error)
      } finally {
        this.loadingFiles = false
      }
    },

    // 打开查看公告对话框
    openAnnouncementViewDialog() {
      this.showAnnouncementViewDialog = true
    },

    // 下载文件
    downloadFile(file) {
      // 构建下载链接
      const token = localStorage.getItem('userToken')
      const downloadUrl = `/api/v1/groups/${this.selectedGroup.id}/files/${file.id}/download?token=${token}`
      
      // 创建隐藏的a标签进行下载
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = file.name
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      
      this.$message.success('开始下载文件')
    },

    // 格式化文件大小
    formatFileSize(bytes) {
      if (bytes === 0) return '0 B'
      const k = 1024
      const sizes = ['B', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
    },

    // ========== 邀请审核功能 ==========

    async loadAllUsers() {
      try {
        const response = await request.get('/api/v1/auth/users/all')
        this.allUsers = response || []
      } catch (error) {
        console.error('加载用户列表失败:', error)
      }
    },

    async teacherInviteUsers() {
      if (this.teacherInviteUserIds.length === 0) {
        this.$message.warning('请选择要邀请的成员')
        return
      }

      this.inviting = true
      try {
        const response = await request.post(
          `/api/v1/groups/${this.selectedGroup.id}/invite-teacher`,
          {
            user_ids: this.teacherInviteUserIds
          }
        )
        
        this.$message.success(`成功邀请 ${response.added_count} 人`)
        if (response.failed_count > 0) {
          this.$message.warning(`${response.failed_count} 人邀请失败`)
        }
        
        this.showTeacherInviteDialog = false
        this.teacherInviteUserIds = []
        await this.loadGroups()
      } catch (error) {
        this.$message.error('邀请失败: ' + (error.message || '未知错误'))
        console.error(error)
      } finally {
        this.inviting = false
      }
    },

    async studentInviteUser() {
      console.log('🎯 学生邀请方法被调用')
      console.log('邀请对象ID:', this.studentInviteForm.invitedUserId)
      console.log('邀请理由:', this.studentInviteForm.reason)
      
      if (!this.studentInviteForm.invitedUserId) {
        this.$message.warning('请选择要邀请的成员')
        return
      }
      if (!this.studentInviteForm.reason.trim()) {
        this.$message.warning('请输入邀请理由')
        return
      }

      this.inviting = true
      try {
        console.log('📤 发送邀请请求...')
        await request.post(
          `/api/v1/groups/${this.selectedGroup.id}/invite-student`,
          {
            invited_user_id: this.studentInviteForm.invitedUserId,
            reason: this.studentInviteForm.reason
          }
        )
        
        this.$message.success('邀请已发送，等待老师审核')
        this.showStudentInviteDialog = false
        this.studentInviteForm = { invitedUserId: null, reason: '' }
      } catch (error) {
        this.$message.error('邀请失败: ' + (error.message || '未知错误'))
        console.error(error)
      } finally {
        this.inviting = false
      }
    },

    async loadPendingInvitations() {
      if (!this.isTeacher) return
      
      this.loadingInvitations = true
      try {
        const response = await request.get(
          `/api/v1/groups/${this.selectedGroup.id}/pending-invitations`
        )
        this.pendingInvitations = response.invitations || []
      } catch (error) {
        this.$message.error('加载待审核邀请失败')
        console.error(error)
      } finally {
        this.loadingInvitations = false
      }
    },

    async approveInvitation(invitationId) {
      this.reviewingInvitationId = invitationId
      try {
        await request.post(
          `/api/v1/groups/invitations/${invitationId}/review`,
          {
            approved: true
          }
        )
        
        this.$message.success('邀请已批准，成员已加入群聊')
        await this.loadPendingInvitations()
        await this.loadGroups()
      } catch (error) {
        this.$message.error('审核失败: ' + (error.message || '未知错误'))
        console.error(error)
      } finally {
        this.reviewingInvitationId = null
      }
    },

    showRejectDialog(invitationId) {
      this.rejectingInvitationId = invitationId
      this.rejectReason = ''
      this.showRejectDialog = true
    },

    async rejectInvitation() {
      if (!this.rejectingInvitationId) return

      this.rejectingInvitation = true
      try {
        await request.post(
          `/api/v1/groups/invitations/${this.rejectingInvitationId}/review`,
          {
            approved: false,
            reject_reason: this.rejectReason
          }
        )
        
        this.$message.success('邀请已拒绝')
        this.showRejectDialog = false
        this.rejectReason = ''
        this.rejectingInvitationId = null
        await this.loadPendingInvitations()
      } catch (error) {
        this.$message.error('拒绝失败: ' + (error.message || '未知错误'))
        console.error(error)
      } finally {
        this.rejectingInvitation = false
      }
    }
  }
}
</script>

<style scoped>
/* 主容器 - 与 ChatPage 一致 */
.group-chat-container {
  display: flex;
  height: 100vh;
  background-color: #f8f9fa;
  overflow: hidden;  /* 防止整体溢出 */
}

/* 左侧群聊列表 - 参考 ChatPage 的 sidebar */
.group-list-sidebar {
  width: 280px;
  background-color: #ffffff;
  border-right: 1px solid #e4dffd;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: width 0.3s ease;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid #e4dffd;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sidebar-header h2 {
  margin: 0;
  font-size: 22px;
  font-weight: bold;
  color: #6c5dd3;
}

.sidebar-header .el-button {
  background: linear-gradient(135deg, #8b7fd6 0%, #9f8ce5 100%);
  border: none;
  border-radius: 20px;
  padding: 8px 16px;
  font-size: 13px;
  transition: all 0.2s;
}

.sidebar-header .el-button:hover {
  background: linear-gradient(135deg, #7d6ecc 0%, #8f7dd9 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(139, 127, 214, 0.3);
}

.group-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 12px;
}

.group-item {
  display: flex;
  align-items: center;
  padding: 10px 15px;
  margin: 5px 0;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
  overflow: hidden;
}

.group-item:hover {
  background-color: #f8f7fd;
}

.group-item.active {
  background: linear-gradient(90deg, #f0edfc 0%, #e4dffd 100%);
  border-left: 3px solid #8b7fd6;
}

.group-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #8b7fd6 0%, #9f8ce5 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  margin-right: 12px;
  flex-shrink: 0;
}

.group-info {
  flex: 1;
  min-width: 0;
}

.group-name {
  font-weight: 500;
  margin-bottom: 4px;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.group-meta {
  font-size: 12px;
  color: #999;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #999;
}

.empty-state i {
  font-size: 64px;
  margin-bottom: 20px;
  color: #e4dffd;
}

.empty-state p {
  margin: 8px 0;
  font-size: 14px;
}

.empty-state .hint {
  font-size: 12px;
  color: #bbb;
}

/* 右侧聊天区域 - 与 ChatPage 一致 */
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #f8f7fd;
  border-radius: 10px;
  margin: 10px;
  height: calc(100vh - 20px);  /* 减去上下margin */
  overflow: hidden;
  position: relative;
}

.no-selection {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #999;
}

.no-selection i {
  font-size: 80px;
  margin-bottom: 20px;
  color: #e4dffd;
}

.no-selection p {
  font-size: 16px;
}

.chat-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;  /* 防止内容溢出 */
  overflow: hidden;
}

.chat-header {
  padding: 20px;
  border-bottom: 1px solid #e4dffd;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #ffffff;
  flex-shrink: 0;  /* 防止被压缩 */
  height: 80px;  /* 固定高度 */
}

.header-left h3 {
  margin: 0 0 4px 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.member-count {
  font-size: 13px;
  color: #999;
}

.member-count i {
  margin-right: 4px;
}

.header-right .el-button {
  background: linear-gradient(135deg, #8b7fd6 0%, #9f8ce5 100%);
  border: none;
  border-radius: 20px;
  color: white;
  transition: all 0.2s;
}

.header-right .el-button:hover {
  background: linear-gradient(135deg, #7d6ecc 0%, #8f7dd9 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(139, 127, 214, 0.3);
}

/* 消息列表 - 参考 ChatPage */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  padding-bottom: 20px;
  display: flex;
  flex-direction: column;
  min-height: 0;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior: contain;
  scroll-behavior: smooth;
}

.message {
  display: flex;
  margin-bottom: 20px;
  width: 100%;
}

.message.my-message {
  justify-content: flex-end;
}

.message.other-message {
  justify-content: flex-start;
}

.message.ai-message {
  justify-content: flex-start;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  flex-shrink: 0;
}

.my-message .message-avatar {
  margin-left: 12px;
  order: 2;
}

.other-message .message-avatar,
.ai-message .message-avatar {
  margin-right: 12px;
}

/* 老师头像 - 金色渐变 */
.teacher-avatar {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: linear-gradient(135deg, #f59e0b 0%, #f97316 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.3);
}

/* 学生头像 - 蓝色渐变 */
.student-avatar {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}

/* AI助手头像 - 紫色渐变 */
.ai-avatar {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.3);
}

.message-content {
  max-width: 70%;
  display: flex;
  flex-direction: column;
}

.my-message .message-content {
  align-items: flex-end;
}

.other-message .message-content,
.ai-message .message-content {
  align-items: flex-start;
}

.message-header {
  margin-bottom: 6px;
  font-size: 12px;
  color: #999;
  display: flex;
  align-items: center;
  gap: 8px;
}

.sender-name {
  font-weight: 500;
  color: #666;
  display: flex;
  align-items: center;
  gap: 6px;
}

/* 角色标识 */
.role-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.2;
}

.teacher-badge {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  color: #f59e0b;
  border: 1px solid #fbbf24;
}

.student-badge {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  color: #3b82f6;
  border: 1px solid #60a5fa;
}

.ai-badge {
  background: linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%);
  color: #8b5cf6;
  border: 1px solid #a78bfa;
}

.message-time {
  color: #bbb;
}

.message-text {
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
  word-break: break-word;
  font-size: 15px;
  max-width: 100%;
}

.my-message .message-text {
  background: linear-gradient(135deg, #8b7fd6 0%, #9f8ce5 100%);
  color: white;
  border-radius: 12px 12px 2px 12px;
}

.other-message .message-text {
  background-color: #f0f0f0;
  color: #333;
  border-radius: 12px 12px 12px 2px;
}

.ai-message .message-text {
  background-color: rgb(226, 220, 251);
  border: 1px solid #e4dffd;
  border-left: 3px solid #8b7fd6;
  color: #333;
  border-radius: 12px 12px 12px 2px;
}

/* 输入区域 - 与 ChatPage 一致 */
.input-container {
  border-top: 1px solid #e4dffd;
  padding: 20px;
  background-color: #ffffff;
  flex-shrink: 0;  /* 防止被压缩 */
  display: flex;
  flex-direction: column;
  gap: 12px;
  border-bottom-left-radius: 10px;
  border-bottom-right-radius: 10px;
  min-height: auto;
}

.input-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}

.input-actions .el-button {
  border-radius: 20px;
  transition: all 0.2s;
  font-size: 13px;
  padding: 8px 16px;
}

.input-actions .el-button:not(.el-button--primary) {
  background: #f8f7fd;
  border: 1px solid #e4dffd;
  color: #6c5dd3;
}

.input-actions .el-button:not(.el-button--primary):hover {
  background: #f0edfc;
  border-color: #8b7fd6;
  transform: translateY(-1px);
}

.input-actions .el-button--primary {
  background: linear-gradient(135deg, #8b7fd6 0%, #9f8ce5 100%);
  border: none;
  color: white;
}

.input-actions .el-button--primary:hover {
  background: linear-gradient(135deg, #7d6ecc 0%, #8f7dd9 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(139, 127, 214, 0.3);
}

/* 回复提示 */
.reply-hint {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: #f0edfc;
  border-left: 3px solid #8b7fd6;
  border-radius: 4px;
  font-size: 13px;
  color: #6c5dd3;
}

.reply-hint i {
  cursor: pointer;
  font-size: 16px;
  color: #999;
  transition: color 0.2s;
}

.reply-hint i:hover {
  color: #6c5dd3;
}

.input-box {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  flex: 1;
}

.input-box >>> .el-textarea {
  flex: 1;
}

.input-box >>> .el-textarea__inner {
  border: 1px solid #e4dffd;
  border-radius: 12px;
  padding: 12px 16px;
  font-size: 14px;
  resize: none;
  transition: border-color 0.3s;
}

.input-box >>> .el-textarea__inner:focus {
  border-color: #8b7fd6;
}

.input-box .el-button {
  background: linear-gradient(135deg, #8b7fd6 0%, #9f8ce5 100%);
  border: none;
  border-radius: 20px;
  padding: 10px 24px;
  color: white;
  transition: all 0.2s;
}

.input-box .el-button:hover:not(:disabled) {
  background: linear-gradient(135deg, #7d6ecc 0%, #8f7dd9 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(139, 127, 214, 0.3);
}

.input-box .el-button:disabled {
  background: #e0e0e0;
  cursor: not-allowed;
}

.loading-message {
  text-align: center;
  color: #999;
  padding: 20px;
}

.loading-message i {
  margin-right: 8px;
  color: #8b7fd6;
}

/* 对话框样式优化 */
>>> .el-dialog {
  border-radius: 12px;
}

>>> .el-dialog__header {
  border-bottom: 1px solid #e4dffd;
  padding: 20px;
}

>>> .el-dialog__title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

>>> .el-dialog__body {
  padding: 20px;
}

>>> .el-form-item__label {
  color: #666;
  font-weight: 500;
}

>>> .el-input__inner,
>>> .el-textarea__inner {
  border: 1px solid #e4dffd;
  border-radius: 8px;
  transition: border-color 0.3s;
}

>>> .el-input__inner:focus,
>>> .el-textarea__inner:focus {
  border-color: #8b7fd6;
}

>>> .el-select {
  width: 100%;
}

>>> .el-dialog__footer .el-button {
  border-radius: 20px;
  padding: 10px 24px;
}

>>> .el-dialog__footer .el-button--primary {
  background: linear-gradient(135deg, #8b7fd6 0%, #9f8ce5 100%);
  border: none;
}

>>> .el-dialog__footer .el-button--primary:hover {
  background: linear-gradient(135deg, #7d6ecc 0%, #8f7dd9 100%);
  box-shadow: 0 4px 12px rgba(139, 127, 214, 0.3);
}

/* 成员列表样式 */
.members-list {
  max-height: 400px;
  overflow-y: auto;
}

.member-item {
  display: flex;
  align-items: center;
  padding: 12px;
  border-bottom: 1px solid #f0f0f0;
  transition: background-color 0.3s;
}

.member-item:hover {
  background-color: #f8f7fd;
}

.member-item:last-child {
  border-bottom: none;
}

.member-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #e4dffd 0%, #f0eeff 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  margin-right: 12px;
}

.member-info {
  flex: 1;
}

.member-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.member-email {
  font-size: 12px;
  color: #999;
}

.member-role {
  margin-left: 12px;
}

/* 滚动条样式 */
.group-list::-webkit-scrollbar,
.messages-container::-webkit-scrollbar,
.members-list::-webkit-scrollbar {
  width: 6px;
}

.group-list::-webkit-scrollbar-track,
.messages-container::-webkit-scrollbar-track {
  background: #f8f7fd;
}

.group-list::-webkit-scrollbar-thumb,
.messages-container::-webkit-scrollbar-thumb {
  background: #e4dffd;
  border-radius: 3px;
}

.group-list::-webkit-scrollbar-thumb:hover,
.messages-container::-webkit-scrollbar-thumb:hover {
  background: #d4cfed;
}

/* 暗色主题 */
.dark-theme {
  background-color: #1a1a1a;
  color: #e0e0e0;
}

.dark-theme .group-list-sidebar,
.dark-theme .chat-area,
.dark-theme .chat-header,
.dark-theme .input-container {
  background-color: #2d2d2d;
  border-color: #404040;
}

.dark-theme .sidebar-header h2 {
  color: #9f8ce5;
}

.dark-theme .group-item:hover {
  background-color: #3d3d3d;
}

.dark-theme .group-item.active {
  background: linear-gradient(90deg, #3d3d3d 0%, #4d4d4d 100%);
}

.dark-theme .other-message .message-text {
  background-color: #3d3d3d;
  color: #e0e0e0;
}

.dark-theme .ai-message .message-text {
  background-color: #3d3d3d;
  border-color: #555;
}

.dark-theme .empty-state i,
.dark-theme .no-selection i {
  color: #555;
}

/* 文件列表项样式 */
.file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 15px;
  border-bottom: 1px solid #f0f0f0;
  transition: background-color 0.2s;
}

.file-item:hover {
  background-color: #f8f7fd;
}

.file-item:last-child {
  border-bottom: none;
}

.file-info {
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 0;
}

.file-details {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 5px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-meta {
  font-size: 12px;
  color: #999;
}

.file-actions {
  margin-left: 15px;
}

.dark-theme >>> .el-input__inner,
.dark-theme >>> .el-textarea__inner {
  background-color: #3d3d3d;
  border-color: #555;
  color: #e0e0e0;
}
</style>
