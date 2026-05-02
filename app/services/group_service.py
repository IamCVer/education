# app/services/group_service.py
"""
[职责] 群组聊天业务逻辑层 - 封装与Mattermost的交互
"""
from typing import List, Optional
import os
import asyncio
import json
from datetime import datetime
from uuid import uuid4
from app.db.redis_client import get_redis_client

try:
    from mattermostdriver import Driver
    from mattermostdriver.exceptions import ResourceNotFound
except ImportError:
    Driver = None
    ResourceNotFound = None


class GroupService:
    """群组服务 - 作为Mattermost的代理"""
    
    def __init__(self):
        """初始化Mattermost配置（admin账户仅用于系统级操作）"""
        self.mattermost_enabled = False
        self.admin_driver = None  # admin账户仅用于创建用户、团队等系统操作
        self.driver = None  # 保留兼容性
        
        # 从环境变量获取 Mattermost 配置
        self.mm_url = os.getenv('MATTERMOST_URL', 'mattermost')
        self.mm_port = int(os.getenv('MATTERMOST_PORT', 8065))
        self.mm_username = os.getenv('MATTERMOST_USERNAME', 'admin')
        self.mm_password = os.getenv('MATTERMOST_PASSWORD', 'admin123')
        self.mm_token = (
            os.getenv('MATTERMOST_TOKEN')
            or os.getenv('MATTERMOST_PERSONAL_ACCESS_TOKEN')
            or os.getenv('MATTERMOST_BOT_TOKEN')
        )
        
        # 检查mattermostdriver是否可用
        if Driver is None:
            print("❌ mattermostdriver模块未安装，群聊功能将不可用")
            return
        
        try:
            # 初始化admin driver用于系统级操作（创建用户、团队等）
            admin_options = {
                'url': self.mm_url,
                'port': self.mm_port,
                'scheme': 'http',
                'basepath': '/api/v4',
                'verify': False
            }

            if self.mm_token:
                admin_options['token'] = self.mm_token
                auth_mode = 'token'
            else:
                admin_options['login_id'] = self.mm_username
                admin_options['password'] = self.mm_password
                auth_mode = f'用户名 {self.mm_username}'
            
            self.admin_driver = Driver(admin_options)
            self.admin_driver.login()
            
            # 保留driver引用以兼容旧代码
            self.driver = self.admin_driver
            self.bot_user_id = self.admin_driver.users.get_user('me')['id']
            
            self.mattermost_enabled = True
            print(f"✅ Mattermost服务已连接（认证方式: {auth_mode}）")
            print(f"   提示：群聊将由实际的老师账户创建和管理")
        except Exception as e:
            print(f"❌ 初始化 Mattermost 失败: {e}")
            if not self.mm_token:
                print(
                    "请检查 MATTERMOST_USERNAME / MATTERMOST_PASSWORD 是否与 Mattermost 实际管理员一致，"
                    "或改为配置 MATTERMOST_TOKEN"
                )
            print("群聊功能将不可用")
            
    
    def _check_mattermost_available(self):
        """检查 Mattermost 是否可用"""
        if not self.mattermost_enabled or not self.admin_driver:
            raise Exception("Mattermost 服务未配置或不可用")
    
    async def _get_user_driver(self, user_id: int) -> Driver:
        """为指定用户创建并登录Mattermost Driver"""
        from app.models.user_model import User
        
        # 获取用户信息
        user = await User.get(id=user_id)
        username = user.email.split('@')[0]
        
        # 确保用户在Mattermost中存在
        await self._ensure_mattermost_user_exists(user_id)
        
        # 创建新的driver并登录
        user_options = {
            'url': self.mm_url,
            'port': self.mm_port,
            'scheme': 'http',
            'basepath': '/api/v4',
            'verify': False,
            'login_id': username,
            'password': 'default_password_123'  # 统一的默认密码
        }
        
        user_driver = Driver(user_options)
        try:
            user_driver.login()
            print(f"✅ 用户 {username} 登录Mattermost成功")
            return user_driver
        except Exception as e:
            print(f"❌ 用户 {username} 登录失败: {e}")
            raise Exception(f"无法以用户 {username} 身份登录Mattermost")
    
    async def _ensure_mattermost_user_exists(self, user_id: int) -> str:
        """确保用户在Mattermost中存在，如果不存在则创建"""
        from app.models.user_model import User
        
        user = await User.get(id=user_id)
        username = user.email.split('@')[0]
        
        try:
            mm_user = self.admin_driver.users.get_user_by_username(username)
            return mm_user['id']
        except ResourceNotFound:
            # 用户不存在，使用admin权限创建
            user_data = {
                'email': user.email,
                'username': username,
                'password': 'default_password_123',
                'first_name': username,
                'last_name': ''
            }
            mm_user = self.admin_driver.users.create_user(options=user_data)
            print(f"✅ 创建Mattermost用户: {username}")
            return mm_user['id']
    
    async def create_group(self, creator_id: int, group_name: str, student_ids: List[int]) -> dict:
        """
        创建群聊 - 使用老师自己的账户创建
        
        Args:
            creator_id: 创建者ID（老师）
            group_name: 群聊名称
            student_ids: 学生ID列表
        Returns:
            群聊信息
        """
        self._check_mattermost_available()
        
        # 1. 获取团队ID
        team_id = await self._get_or_create_team()
        
        # 2. 使用老师的账户登录
        teacher_driver = await self._get_user_driver(creator_id)
        mattermost_creator_id = await self._ensure_mattermost_user_exists(creator_id)
        
        # 3. 确保老师是团队成员
        try:
            self.admin_driver.teams.add_user_to_team(
                team_id, 
                options={'team_id': team_id, 'user_id': mattermost_creator_id}
            )
        except Exception as e:
            print(f"⚠️ 添加老师到团队: {e}")
        
        # 4. 使用老师账户创建私有频道（群聊）
        import time
        channel_name = f'group-{creator_id}-{int(time.time())}'
        
        channel_data = {
            'team_id': team_id,
            'name': channel_name,
            'display_name': group_name,
            'type': 'P',  # P = Private channel
            'purpose': f'群聊: {group_name}'
        }
        
        # 使用老师的driver创建频道
        channel = teacher_driver.channels.create_channel(channel_data)
        print(f"✅ 老师创建频道: channel_id={channel['id']}, name={channel['display_name']}")
        
        # 5. 添加学生到频道
        for student_id in student_ids:
            mattermost_student_id = await self._ensure_mattermost_user_exists(student_id)
            
            # 确保学生是团队成员
            try:
                self.admin_driver.teams.add_user_to_team(
                    team_id, 
                    options={'team_id': team_id, 'user_id': mattermost_student_id}
                )
            except:
                pass
            
            # 使用老师账户添加学生到频道
            teacher_driver.channels.add_user(channel['id'], options={'user_id': mattermost_student_id})
        
        # 6. 登出老师账户
        try:
            teacher_driver.logout()
        except:
            pass
        
        return {
            'id': channel['id'],
            'name': channel['display_name'],
            'member_count': len(student_ids) + 1,
            'created_at': str(channel['create_at'])
        }
    
    async def get_user_groups(self, user_id: int) -> List[dict]:
        """
        获取用户所属的所有群聊
        
        Args:
            user_id: 用户ID
        
        Returns:
            群聊列表
        """
        # 如果 Mattermost 不可用，返回空列表
        if not self.mattermost_enabled or not self.driver:
            return []
        
        try:
            mattermost_user_id = await self._get_mattermost_user_id(user_id)
            team_id = await self._get_or_create_team()
            
            # 获取用户的所有频道
            channels = self.driver.channels.get_channels_for_user(mattermost_user_id, team_id)
            
            groups = []
            for channel in channels:
                if channel['type'] == 'P':  # 只返回私有频道（群聊）
                    # 获取频道成员数
                    members = self.driver.channels.get_channel_members(channel['id'])
                    
                    groups.append({
                        'id': channel['id'],
                        'name': channel['display_name'],
                        'member_count': len(members),
                        'created_at': str(channel['create_at'])  # 转换为字符串
                    })
            
            return groups
        except ResourceNotFound:
            # 用户还没有加入任何频道，返回空列表
            return []
    
    async def get_messages(self, group_id: str, limit: int = 50, offset: int = 0) -> List[dict]:
        """
        获取群聊的历史消息
        
        Args:
            group_id: 群聊ID（Mattermost频道ID）
            limit: 消息数量限制
            offset: 偏移量
        
        Returns:
            消息列表
        """
        # 获取频道的帖子（消息）
        posts = self.driver.posts.get_posts_for_channel(group_id, params={'per_page': limit, 'page': offset})
        
        messages = []
        # posts['order'] 是从新到旧的顺序
        for post_id in reversed(posts['order']):  # 反转顺序，让旧消息在前
            post = posts['posts'][post_id]
            
            # 检查是否是系统消息
            message_text = post['message']
            is_system_message = (
                'joined the channel' in message_text or 
                'added to the channel' in message_text or
                'removed from the channel' in message_text or
                'left the channel' in message_text
            )
            
            # 跳过系统消息（不显示）
            if is_system_message and post.get('type') == 'system_join_leave':
                continue
            
            # 获取发送者信息
            sender = self.driver.users.get_user(post['user_id'])
            sender_username = sender.get('username', '')
            
            # 跳过 admin 用户的消息（除非是特殊格式的消息）
            if sender_username == 'admin':
                # 检查是否有 [发送者]: 格式（兼容旧消息）
                import re
                sender_pattern = re.match(r'^\[([^\]]+)\]:\s*(.*)$', message_text)
                if not sender_pattern:
                    # 如果不是特殊格式，跳过这条消息
                    continue
            
            # 获取发送者的应用 ID
            sender_app_id = await self._get_app_user_id(post['user_id'])
            
            # 根据 Mattermost 用户名获取显示名称
            actual_sender_name = sender.get('username', sender.get('email', '未知用户'))
            actual_message = message_text
            
            # 获取用户角色
            sender_role = 'student'  # 默认为学生
            try:
                from app.models.user_model import User
                user = await User.get(id=sender_app_id)
                # 将枚举转换为字符串
                sender_role = user.role.value if hasattr(user.role, 'value') else str(user.role)
            except Exception:
                pass
            
            # 如果是 admin 发送的消息，检查是否有 [发送者]: 格式（兼容旧消息）
            if sender_username == 'admin':
                import re
                sender_pattern = re.match(r'^\[([^\]]+)\]:\s*(.*)$', message_text)
                if sender_pattern:
                    actual_sender_name = sender_pattern.group(1)
                    actual_message = sender_pattern.group(2)
                    # 尝试根据名称找到对应的用户 ID
                    from app.models.user_model import User
                    try:
                        # 尝试通过邮箱前缀查找用户
                        user = await User.get(email__startswith=actual_sender_name)
                        sender_app_id = user.id
                    except:
                        pass
            
            # 确定消息类型（增强AI消息识别）
            if is_system_message:
                message_type = 'system'
            elif (
                sender.get('username') == 'ai-assistant' or 
                'AI助手' in actual_sender_name or 
                actual_message.startswith('🤖') or 
                (sender.get('username') == 'admin' and actual_sender_name == 'AI助手')
            ):
                message_type = 'ai_response'
                # 移除AI消息前缀（如果存在）
                if actual_message.startswith('🤖 '):
                    actual_message = actual_message[2:].strip()
            else:
                message_type = 'text'
            
            msg_data = {
                'id': post['id'],
                'sender_id': sender_app_id,
                'sender_name': actual_sender_name,
                'sender_role': sender_role,  # 添加用户角色
                'message': actual_message,
                'message_type': message_type,
                'created_at': str(post['create_at'])  # 转换为字符串
            }
            messages.append(msg_data)
        
        return messages
    
    async def send_message(self, group_id: str, user_id: int, message: str):
        """
        发送消息到群聊
        
        Args:
            group_id: 群聊ID
            user_id: 发送者ID
            message: 消息内容
        """
        # 获取发送者的 Mattermost 用户 ID
        mattermost_user_id = await self._get_mattermost_user_id(user_id)
        
        # 获取发送者信息用于创建临时连接
        from app.models.user_model import User
        sender = await User.get(id=user_id)
        sender_username = sender.email.split('@')[0]
        
        # 为该用户创建临时的 Mattermost 连接
        try:
            # 创建新的驱动实例
            user_driver = Driver({
                'url': os.getenv('MATTERMOST_URL', 'mattermost'),
                'port': int(os.getenv('MATTERMOST_PORT', 8065)),
                'scheme': 'http',
                'basepath': '/api/v4',
                'verify': False,
                'login_id': sender_username,  # 使用用户的用户名
                'password': 'default_password_123'  # 默认密码
            })
            
            # 尝试登录
            user_driver.login()
            
            # 用该用户的身份发送消息
            post_data = {
                'channel_id': group_id,
                'message': message
            }
            user_driver.posts.create_post(options=post_data)
            
            # 登出并清理
            user_driver.logout()
            
        except Exception as e:
            print(f"无法用用户 {sender_username} 发送消息: {e}")
            # 如果失败，回退到使用 admin 账户发送
            formatted_message = f"[{sender_username}]: {message}"
            post_data = {
                'channel_id': group_id,
                'message': formatted_message
            }
            self.driver.posts.create_post(options=post_data)
    
    async def invite_students(self, group_id: str, student_ids: List[int]):
        """
        邀请学生加入群聊
        
        Args:
            group_id: 群聊ID
            student_ids: 学生ID列表
        """
        # 获取团队ID
        team_id = await self._get_or_create_team()
        
        for student_id in student_ids:
            mattermost_student_id = await self._get_mattermost_user_id(student_id)
            
            # 先确保学生是团队成员
            try:
                self.driver.teams.add_user_to_team(
                    team_id, 
                    options={'team_id': team_id, 'user_id': mattermost_student_id}
                )
            except Exception as e:
                # 如果已经是团队成员，忽略错误
                print(f"添加用户到团队时出错（可能已是成员）: {e}")
            
            # 然后将学生添加到频道（群聊）
            self.driver.channels.add_user(group_id, options={'user_id': mattermost_student_id})
    
    async def ask_ai(self, group_id: str, question: str):
        """
        向AI助手提问（基于知识图谱）
        
        Args:
            group_id: 群聊ID
            question: 问题
        """
        # 1. 调用现有的知识图谱问答服务
        from app.services.qa_service import handle_new_question
        from app.schemas.qa_schemas import QuestionCreate
        from app.db.redis_client import get_redis_client
        import json
        
        # 创建问题对象
        question_obj = QuestionCreate(text=question, force_regenerate=False)
        
        # 处理问题并获取任务ID
        # 优先使用AI系统用户，避免污染真实用户的问答历史
        from app.models.user_model import User
        try:
            # 优先使用AI系统专用账户
            ai_system_user = await User.filter(email="ai-system@education.com").first()
            if ai_system_user:
                user_id = ai_system_user.id
            else:
                # 降级方案：使用第一个admin用户
                admin_user = await User.filter(role="admin").first()
                user_id = admin_user.id if admin_user else 1
        except:
            user_id = 1  # 最终降级方案
        
        result = await handle_new_question(question_obj, user_id=user_id)
        question_id = result.get("question_id")
        
        answer = ""
        
        # 如果有缓存的答案，立即使用
        if result.get("status") == "completed_from_cache":
            from app.services.caching_service import get_cache_service
            cache_service = get_cache_service()
            cached_result = await cache_service.get_cached_answer(question)
            if cached_result:
                answer = cached_result["answer"]
        else:
            # 等待答案生成（最多等待30秒）
            redis_client = get_redis_client()
            max_attempts = 60  # 60 * 0.5秒 = 30秒
            
            print(f"⏳ 等待AI答案生成，问题ID: {question_id}")
            
            for attempt in range(max_attempts):
                await asyncio.sleep(0.5)  # 等待0.5秒
                
                # 尝试从Redis获取答案
                try:
                    cached_data = await redis_client.get(f"question_answer:{question_id}")
                    if cached_data:
                        answer_data = json.loads(cached_data)
                        answer = answer_data["answer"]
                        print(f"✅ 在第{attempt + 1}次尝试后获取到答案（用时{(attempt + 1) * 0.5}秒）")
                        break
                except Exception as e:
                    if attempt % 10 == 0:  # 每5秒输出一次日志
                        print(f"⏳ 第{attempt + 1}次尝试，从Redis获取答案时出错: {e}")
            
            if not answer:
                print(f"⚠️ 等待30秒后仍未获取到答案，尝试从缓存获取...")
            
            # 如果还是没有答案，尝试从缓存获取
            if not answer:
                try:
                    from app.services.caching_service import get_cache_service
                    cache_service = get_cache_service()
                    cached_result = await cache_service.get_cached_answer(question)
                    if cached_result:
                        answer = cached_result["answer"]
                except:
                    pass
        
        # 如果还是没有答案，提供默认回复
        if not answer:
            answer = f"抱歉，关于\"{question}\"的问题生成答案超时。请稍后再试或联系管理员。"
            print(f"❌ AI答案生成超时，问题ID: {question_id}")
        else:
            print(f"✅ 成功获取AI答案，长度: {len(answer)} 字符")
        
        # 2. 获取AI助手的Mattermost用户ID
        ai_user_id = await self._get_or_create_ai_user()
        
        # 3. 确保AI助手是频道成员
        try:
            self.driver.channels.add_user(group_id, options={'user_id': ai_user_id})
        except:
            pass  # 如果已经是成员，忽略
        
        # 4. 以AI助手的名义发送回答到群聊
        send_success = False
        send_method = None
        
        # 尝试方案1：使用AI助手账户发送
        try:
            print(f"ℹ️ 尝试使用AI助手账户发送消息...")
            ai_driver = Driver({
                'url': os.getenv('MATTERMOST_URL', 'mattermost'),
                'port': int(os.getenv('MATTERMOST_PORT', 8065)),
                'scheme': 'http',
                'basepath': '/api/v4',
                'verify': False,
                'login_id': 'ai-assistant',
                'password': 'ai_password_123'
            })
            ai_driver.login()
            
            post_data = {
                'channel_id': group_id,
                'message': f"🤖 {answer}"
            }
            result = ai_driver.posts.create_post(options=post_data)
            ai_driver.logout()
            
            send_success = True
            send_method = 'ai_assistant'
            print(f"✅ AI助手账户发送成功，消息ID: {result.get('id', 'unknown')}")
            
        except Exception as e:
            print(f"❌ AI助手账户发送失败: {e}")
            
            # 尝试方案2：回退到admin账户发送
            try:
                print(f"ℹ️ 尝试使用admin账户发送消息...")
                post_data = {
                    'channel_id': group_id,
                    'message': f"[AI助手]: {answer}"
                }
                result = self.driver.posts.create_post(options=post_data)
                send_success = True
                send_method = 'admin'
                print(f"✅ Admin账户发送成功，消息ID: {result.get('id', 'unknown')}")
                
            except Exception as admin_error:
                print(f"❌ Admin账户也无法发送消息: {admin_error}")
                send_success = False
        
        # 返回发送状态
        if not send_success:
            raise Exception("AI回答发送失败，所有发送方案均失败")
        
        return {
            'success': send_success,
            'method': send_method,
            'answer': answer
        }
    
    async def is_group_member(self, group_id: str, user_id: int) -> bool:
        """
        检查用户是否是群聊成员
        
        Args:
            group_id: 群聊ID
            user_id: 用户ID
        
        Returns:
            是否是成员
        """
        try:
            mattermost_user_id = await self._get_mattermost_user_id(user_id)
            member = self.driver.channels.get_channel_member(group_id, mattermost_user_id)
            return member is not None
        except ResourceNotFound:
            return False
    
    async def get_group_members(self, group_id: str) -> List[dict]:
        """
        获取群聊成员列表
        
        Args:
            group_id: 群聊ID
        
        Returns:
            成员列表
        """
        from app.models.user_model import User
        
        try:
            # 获取频道的所有成员
            members = self.driver.channels.get_channel_members(group_id)
            
            member_list = []
            for member in members:
                mm_user_id = member['user_id']
                
                # 获取Mattermost用户信息
                mm_user = self.driver.users.get_user(mm_user_id)
                username = mm_user.get('username', '')
                
                # 过滤掉系统账户
                if username in ['admin', 'ai-assistant']:
                    continue
                
                # 获取应用用户ID和角色
                try:
                    app_user = await User.get(email=mm_user['email'])
                    user_id = app_user.id
                    user_role = app_user.role.value if hasattr(app_user.role, 'value') else str(app_user.role)
                    user_email = app_user.email
                except:
                    # 如果找不到对应的应用用户，跳过
                    continue
                
                member_list.append({
                    'id': user_id,
                    'username': username,
                    'email': user_email,
                    'role': user_role,
                    'role_display': '老师' if user_role == 'teacher' else '学生'
                })
            
            return member_list
        except Exception as e:
            print(f"获取群成员列表失败: {e}")
            return []
    
    # ========== 辅助方法 ==========
    async def _get_or_create_team(self) -> str:
        """获取或创建默认团队"""
        # 尝试获取当前用户所属的团队
        try:
            teams = self.driver.teams.get_user_teams(self.bot_user_id)
            if teams:
                return teams[0]['id']
        except:
            pass
        
        # 如果没有团队，创建一个
        team_data = {
            'name': 'education',
            'display_name': '教育问答系统',
            'type': 'I'  # I = Invite only
        }
        
        team = self.driver.teams.create_team(options=team_data)
        
        # 将当前用户（Bot）添加到团队
        self.driver.teams.add_user_to_team(team['id'], options={'team_id': team['id'], 'user_id': self.bot_user_id})
        
        return team['id']
    
    async def _get_mattermost_user_id(self, app_user_id: int) -> str:
        """
        根据应用用户ID获取Mattermost用户ID
        如果用户不存在，则创建
        
        Args:
            app_user_id: 应用用户ID
        
        Returns:
            Mattermost用户ID
        """
        from app.models.user_model import User
        
        # 从数据库获取用户信息
        user = await User.get(id=app_user_id)
        
        # 尝试在Mattermost中查找用户（使用email作为username）
        username = user.email.split('@')[0]  # 从email提取用户名
        try:
            mm_user = self.driver.users.get_user_by_username(username)
            return mm_user['id']
        except ResourceNotFound:
            # 用户不存在，创建新用户
            user_data = {
                'email': user.email,
                'username': username,
                'password': 'default_password_123',  # 默认密码，用户不会直接登录Mattermost
                'first_name': username,
                'last_name': ''
            }
            
            mm_user = self.driver.users.create_user(options=user_data)
            return mm_user['id']
    
    async def _get_app_user_id(self, mattermost_user_id: str) -> int:
        """
        根据Mattermost用户ID获取应用用户ID
        
        Args:
            mattermost_user_id: Mattermost用户ID
        
        Returns:
            应用用户ID
        """
        from app.models.user_model import User
        
        mm_user = self.driver.users.get_user(mattermost_user_id)
        # 通过 email 查找用户（因为 User 模型没有 username 字段）
        try:
            app_user = await User.get(email=mm_user['email'])
            return app_user.id
        except:
            # 如果找不到用户（例如系统用户 admin），返回 0
            return 0
    
    async def _get_or_create_ai_user(self) -> str:
        """获取或创建AI助手用户"""
        try:
            ai_user = self.driver.users.get_user_by_username('ai-assistant')
            # 确保AI助手是团队成员
            team_id = await self._get_or_create_team()
            try:
                self.driver.teams.add_user_to_team(team_id, options={'team_id': team_id, 'user_id': ai_user['id']})
            except:
                pass  # 如果已经是成员，忽略
                
            return ai_user['id']
        except ResourceNotFound:
            # 创建AI助手用户
            user_data = {
                'email': 'ai@education.com',
                'username': 'ai-assistant',
                'password': 'ai_password_123',
                'first_name': 'AI',
                'last_name': '助手'
            }
            
            ai_user = self.driver.users.create_user(options=user_data)
            
            # 将AI助手添加到团队
            team_id = await self._get_or_create_team()
            try:
                self.driver.teams.add_user_to_team(team_id, options={'team_id': team_id, 'user_id': ai_user['id']})
            except:
                pass
            
            return ai_user['id']
    
    # ========== 新增功能方法 ==========
    
    async def upload_file(self, group_id: str, user_id: int, file_data: bytes, file_name: str):
        """
        上传文件到群聊
        
        Args:
            group_id: 群聊ID
            user_id: 上传者ID
            file_data: 文件二进制数据
            file_name: 文件名
        
        Returns:
            文件信息
        """
        mattermost_user_id = await self._get_mattermost_user_id(user_id)
        
        # 上传文件
        files = {'files': (file_name, file_data)}
        file_response = self.driver.files.upload_file(
            channel_id=group_id,
            files=files
        )
        
        file_info = file_response['file_infos'][0]
        
        # 创建包含文件的消息
        from app.models.user_model import User
        sender = await User.get(id=user_id)
        sender_name = sender.email.split('@')[0]
        
        post_data = {
            'channel_id': group_id,
            'message': f'📎 {sender_name} 分享了文件: {file_name}',
            'file_ids': [file_info['id']]
        }
        self.driver.posts.create_post(options=post_data)
        
        return {
            'id': file_info['id'],
            'name': file_info['name'],
            'size': file_info['size'],
            'mime_type': file_info['mime_type'],
            'url': f"/api/v4/files/{file_info['id']}",
            'created_at': str(file_info['create_at'])
        }
    
    async def get_group_files(self, group_id: str):
        """获取群聊的所有文件"""
        try:
            # 获取频道的所有消息（包含文件）
            posts = self.driver.posts.get_posts_for_channel(group_id, params={'per_page': 200})
            
            files = []
            if posts and 'posts' in posts:
                for post_id in posts.get('order', []):
                    post = posts['posts'][post_id]
                    # 检查消息是否包含文件
                    if post.get('file_ids') and len(post['file_ids']) > 0:
                        # 获取上传者信息
                        uploader = self.driver.users.get_user(post['user_id'])
                        uploader_app_id = await self._get_app_user_id(post['user_id'])
                        
                        for file_id in post['file_ids']:
                            try:
                                # 打印post结构以便调试
                                print(f"Post keys: {post.keys()}")
                                print(f"File ID: {file_id}")
                                if 'metadata' in post:
                                    print(f"Metadata: {post['metadata']}")
                                
                                # 直接从post的metadata中获取文件信息
                                file_metadata = post.get('metadata', {}).get('files', [])
                                file_info = None
                                
                                # 查找对应的文件元数据
                                for f in file_metadata:
                                    if f.get('id') == file_id:
                                        file_info = f
                                        break
                                
                                if file_info:
                                    files.append({
                                        'id': file_info['id'],
                                        'name': file_info.get('name', f'文件_{file_id[:8]}'),
                                        'size': file_info.get('size', 0),
                                        'mime_type': file_info.get('mime_type', 'unknown'),
                                        'uploader': uploader.get('username', 'unknown'),
                                        'uploader_id': uploader_app_id,
                                        'created_at': str(post['create_at'])
                                    })
                                    print(f"成功获取文件信息: {file_info.get('name')}, 大小: {file_info.get('size')} bytes")
                                else:
                                    # 如果metadata中没有，使用基本信息
                                    print(f"文件 {file_id} 的metadata不存在，使用基本信息")
                                    files.append({
                                        'id': file_id,
                                        'name': f'文件_{file_id[:8]}',
                                        'size': 0,
                                        'mime_type': 'unknown',
                                        'uploader': uploader.get('username', 'unknown'),
                                        'uploader_id': uploader_app_id,
                                        'created_at': str(post['create_at'])
                                    })
                            except Exception as e:
                                print(f"获取文件 {file_id} 信息失败: {e}")
                                # 如果获取文件信息失败，使用基本信息
                                files.append({
                                    'id': file_id,
                                    'name': f'文件_{file_id[:8]}',
                                    'size': 0,
                                    'mime_type': 'unknown',
                                    'uploader': uploader.get('username', 'unknown'),
                                    'uploader_id': uploader_app_id,
                                    'created_at': str(post['create_at'])
                                })
            
            # 按创建时间倒序排序
            files.sort(key=lambda x: x['created_at'], reverse=True)
            return files
        except Exception as e:
            print(f"获取群文件列表失败: {e}")
            return []
    
    async def download_file(self, file_id: str):
        """下载文件"""
        try:
            # 使用HTTP请求直接从Mattermost下载文件
            import requests
            
            # 获取Mattermost配置
            mattermost_url = self.driver.client.url
            token = self.driver.client.token
            
            # 构建正确的下载URL（注意：driver.client.url 已经包含了 /api/v4）
            # 所以我们需要去掉它，只保留基础URL
            base_url = mattermost_url.replace('/api/v4', '')
            download_url = f"{base_url}/api/v4/files/{file_id}"
            
            print(f"下载文件URL: {download_url}")
            
            headers = {'Authorization': f'Bearer {token}'}
            
            response = requests.get(download_url, headers=headers)
            response.raise_for_status()
            
            content = response.content
            
            # 从响应头获取文件名
            content_disposition = response.headers.get('Content-Disposition', '')
            if 'filename=' in content_disposition:
                # 处理可能的引号
                name = content_disposition.split('filename=')[1].strip('"').strip("'")
            else:
                name = f'file_{file_id[:8]}'
            
            mime_type = response.headers.get('Content-Type', 'application/octet-stream')
            size = len(content)
            
            print(f"成功下载文件: {name}, 大小: {size} bytes")
            
            return {
                'content': content,
                'name': name,
                'mime_type': mime_type,
                'size': size
            }
        except Exception as e:
            print(f"下载文件失败: {e}")
            import traceback
            traceback.print_exc()
            raise Exception(f"下载文件失败: {e}")
    
    async def search_messages(self, group_id: str, query: str, user_id: int, limit: int = 20):
        """
        搜索群聊消息
        
        Args:
            group_id: 群聊ID
            query: 搜索关键词
            user_id: 搜索用户ID
            limit: 结果数量限制
        
        Returns:
            搜索结果列表
        """
        try:
            team_id = await self._get_or_create_team()
            
            # 使用正确的 API 方法进行搜索
            search_params = {
                'terms': query,
                'is_or_search': False,
                'time_zone_offset': 0,
                'include_deleted_channels': False,
                'page': 0,
                'per_page': 100  # 获取更多结果以便过滤
            }
            
            # 使用 teams.search_posts 方法
            results = self.driver.teams.search_posts(team_id, search_params)
            
            # 过滤出当前群聊的消息
            messages = []
            if results and 'posts' in results:
                for post_id in results.get('order', []):
                    post = results['posts'][post_id]
                    if post['channel_id'] == group_id:
                        # 获取发送者信息
                        sender = self.driver.users.get_user(post['user_id'])
                        sender_app_id = await self._get_app_user_id(post['user_id'])
                        
                        messages.append({
                            'id': post['id'],
                            'sender_id': sender_app_id,
                            'sender_name': sender.get('username', 'unknown'),
                            'message': post['message'],
                            'message_type': 'text',
                            'created_at': str(post['create_at'])
                        })
                        
                        # 限制返回数量
                        if len(messages) >= limit:
                            break
            
            return messages
        except Exception as e:
            print(f"搜索消息失败: {e}")
            # 如果搜索API失败，使用简单的本地过滤方法
            return await self._search_messages_fallback(group_id, query, limit)
    
    async def _search_messages_fallback(self, group_id: str, query: str, limit: int = 20):
        """搜索消息的备用方法 - 获取所有消息并在本地过滤"""
        try:
            # 获取最近的消息
            posts = self.driver.posts.get_posts_for_channel(group_id, params={'per_page': 200})
            
            messages = []
            if posts and 'posts' in posts:
                query_lower = query.lower()
                for post_id in posts.get('order', []):
                    post = posts['posts'][post_id]
                    # 在消息内容中搜索关键词
                    if query_lower in post.get('message', '').lower():
                        sender = self.driver.users.get_user(post['user_id'])
                        sender_app_id = await self._get_app_user_id(post['user_id'])
                        
                        messages.append({
                            'id': post['id'],
                            'sender_id': sender_app_id,
                            'sender_name': sender.get('username', 'unknown'),
                            'message': post['message'],
                            'message_type': 'text',
                            'created_at': str(post['create_at'])
                        })
                        
                        if len(messages) >= limit:
                            break
            
            return messages
        except Exception as e:
            print(f"备用搜索方法也失败: {e}")
            return []
    
    async def pin_message(self, post_id: str):
        """置顶消息"""
        self.driver.posts.pin_post(post_id)
    
    async def unpin_message(self, post_id: str):
        """取消置顶消息"""
        self.driver.posts.unpin_post(post_id)
    
    async def get_pinned_messages(self, group_id: str):
        """获取群聊的所有置顶消息"""
        try:
            # 使用正确的API端点获取置顶帖子
            pinned_posts = self.driver.posts.get_posts_for_channel(group_id, params={'pinned': 'true'})
            
            messages = []
            if pinned_posts and 'posts' in pinned_posts:
                for post_id in pinned_posts.get('order', []):
                    post = pinned_posts['posts'][post_id]
                    if post.get('is_pinned'):
                        sender = self.driver.users.get_user(post['user_id'])
                        sender_app_id = await self._get_app_user_id(post['user_id'])
                        
                        messages.append({
                            'id': post['id'],
                            'sender_id': sender_app_id,
                            'sender_name': sender.get('username', 'unknown'),
                            'message': post['message'],
                            'message_type': 'text',
                            'created_at': str(post['create_at']),
                            'is_pinned': True
                        })
            
            return messages
        except Exception as e:
            print(f"获取置顶消息失败: {e}")
            return []
    
    async def send_message_with_mentions(self, group_id: str, user_id: int, message: str, mention_user_ids: List[int]):
        """发送带@提及的消息"""
        # 构建提及文本
        mention_text = ""
        for mention_id in mention_user_ids:
            mm_user_id = await self._get_mattermost_user_id(mention_id)
            mm_user = self.driver.users.get_user(mm_user_id)
            mention_text += f"@{mm_user['username']} "
        
        full_message = f"{mention_text}{message}"
        
        # 发送消息
        await self.send_message(group_id, user_id, full_message)
    
    async def reply_to_message(self, group_id: str, root_post_id: str, user_id: int, message: str):
        """回复消息（创建线程）"""
        from app.models.user_model import User
        sender = await User.get(id=user_id)
        sender_username = sender.email.split('@')[0]
        
        # 创建回复消息
        try:
            user_driver = Driver({
                'url': os.getenv('MATTERMOST_URL', 'mattermost'),
                'port': int(os.getenv('MATTERMOST_PORT', 8065)),
                'scheme': 'http',
                'basepath': '/api/v4',
                'verify': False,
                'login_id': sender_username,
                'password': 'default_password_123'
            })
            user_driver.login()
            
            post_data = {
                'channel_id': group_id,
                'message': message,
                'root_id': root_post_id  # 指定父消息
            }
            user_driver.posts.create_post(options=post_data)
            user_driver.logout()
            
        except Exception as e:
            print(f"用户 {sender_username} 回复失败: {e}")
            # 回退到admin账户
            post_data = {
                'channel_id': group_id,
                'message': f"[{sender_username}]: {message}",
                'root_id': root_post_id
            }
            self.driver.posts.create_post(options=post_data)
    
    async def get_thread(self, post_id: str):
        """获取消息线程（所有回复）"""
        thread = self.driver.posts.get_thread(post_id)
        
        messages = []
        for reply_id in thread.get('order', []):
            post = thread['posts'][reply_id]
            sender = self.driver.users.get_user(post['user_id'])
            sender_app_id = await self._get_app_user_id(post['user_id'])
            
            messages.append({
                'id': post['id'],
                'sender_id': sender_app_id,
                'sender_name': sender.get('username', 'unknown'),
                'message': post['message'],
                'message_type': 'text',
                'created_at': str(post['create_at']),
                'root_id': post.get('root_id')
            })
        
        return messages
    
    async def set_announcement(self, group_id: str, announcement: str):
        """设置群公告"""
        channel_data = {
            'id': group_id,
            'header': announcement
        }
        self.driver.channels.update_channel(group_id, options=channel_data)
    
    async def get_announcement(self, group_id: str):
        """获取群公告"""
        channel = self.driver.channels.get_channel(group_id)
        return channel.get('header', '')
    
    async def add_reaction(self, post_id: str, user_id: int, emoji_name: str):
        """给消息添加表情反应"""
        mattermost_user_id = await self._get_mattermost_user_id(user_id)
        
        reaction_data = {
            'user_id': mattermost_user_id,
            'post_id': post_id,
            'emoji_name': emoji_name
        }
        self.driver.reactions.create_reaction(options=reaction_data)
    
    async def get_reactions(self, post_id: str):
        """获取消息的所有反应"""
        reactions = self.driver.reactions.get_reactions(post_id)
        
        # 按表情分组
        reaction_dict = {}
        for reaction in reactions:
            emoji = reaction['emoji_name']
            if emoji not in reaction_dict:
                reaction_dict[emoji] = []
            reaction_dict[emoji].append(reaction['user_id'])
        
        return reaction_dict
    
    # ========== 邀请审核功能 ==========
    
    async def student_invite_user(self, group_id: str, inviter_id: int, invited_user_id: int, reason: str) -> dict:
        """
        学生邀请用户进入群聊（需要老师审核）
        
        Args:
            group_id: 群聊ID
            inviter_id: 邀请者ID（学生）
            invited_user_id: 被邀请者ID
            reason: 邀请理由
        
        Returns:
            邀请信息
        """
        from app.models.user_model import User
        
        # 验证邀请者是学生
        inviter = await User.get(id=inviter_id)
        if inviter.role != "student":
            raise Exception("只有学生可以使用此邀请方式")
        
        # 验证被邀请者不在群聊中
        is_member = await self.is_group_member(group_id, invited_user_id)
        if is_member:
            raise Exception("该用户已经是群聊成员")
        
        # 获取群聊信息
        group = self.driver.channels.get_channel(group_id)
        
        # 获取邀请者和被邀请者信息
        inviter_name = inviter.email.split('@')[0]
        invited_user = await User.get(id=invited_user_id)
        invited_user_name = invited_user.email.split('@')[0]
        
        # 创建邀请记录
        invitation_id = str(uuid4())
        invitation_data = {
            "id": invitation_id,
            "group_id": group_id,
            "group_name": group['display_name'],
            "inviter_id": inviter_id,
            "inviter_name": inviter_name,
            "inviter_role": "student",
            "invited_user_id": invited_user_id,
            "invited_user_name": invited_user_name,
            "reason": reason,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "reviewed_at": None,
            "reviewed_by": None
        }
        
        # 存储到Redis
        redis_client = get_redis_client()
        await redis_client.setex(
            f"group_invitation:{invitation_id}",
            86400 * 7,  # 7天过期
            json.dumps(invitation_data, ensure_ascii=False)
        )
        
        # 添加到待审核列表
        redis_key = f"group_pending_invitations:{group_id}"
        await redis_client.sadd(redis_key, invitation_id)
        print(f"📌 邀请已添加到待审核列表: key={redis_key}, invitation_id={invitation_id}")
        
        # 验证邀请是否成功添加
        pending_ids = await redis_client.smembers(redis_key)
        print(f"📌 待审核邀请列表: {pending_ids}")
        
        # 发送通知给群聊的老师
        try:
            from app.services.notification_service import notify_pending_invitation
            # 获取群聊所有老师成员并发送通知
            all_teachers = await User.filter(role="teacher")
            for teacher in all_teachers:
                await notify_pending_invitation(
                    teacher_id=teacher.id,
                    group_name=group['display_name'],
                    inviter_name=inviter_name,
                    invited_user_name=invited_user_name,
                    reason=reason
                )
        except Exception as e:
            print(f"发送邀请通知失败: {e}")
        
        return invitation_data
    
    async def teacher_invite_users(self, group_id: str, teacher_id: int, user_ids: List[int]) -> dict:
        """
        老师直接邀请用户进入群聊（无需审核）
        
        Args:
            group_id: 群聊ID
            teacher_id: 老师ID
            user_ids: 要邀请的用户ID列表
        
        Returns:
            邀请结果
        """
        from app.models.user_model import User
        
        # 验证邀请者是老师
        teacher = await User.get(id=teacher_id)
        if teacher.role != "teacher":
            raise Exception("只有老师可以使用此邀请方式")
        
        # 获取群聊信息
        group = self.driver.channels.get_channel(group_id)
        team_id = group['team_id']
        
        added_users = []
        failed_users = []
        
        for user_id in user_ids:
            try:
                # 检查用户是否已在群聊中
                is_member = await self.is_group_member(group_id, user_id)
                if is_member:
                    failed_users.append({"user_id": user_id, "reason": "已是群聊成员"})
                    continue
                
                # 确保用户在Mattermost中存在
                mattermost_user_id = await self._ensure_mattermost_user_exists(user_id)
                
                # 确保用户是团队成员
                try:
                    self.admin_driver.teams.add_user_to_team(
                        team_id,
                        options={'team_id': team_id, 'user_id': mattermost_user_id}
                    )
                except:
                    pass
                
                # 添加用户到频道
                self.admin_driver.channels.add_user(group_id, options={'user_id': mattermost_user_id})
                
                user = await User.get(id=user_id)
                added_users.append({
                    "user_id": user_id,
                    "user_name": user.email.split('@')[0]
                })
                
            except Exception as e:
                user = await User.get(id=user_id)
                failed_users.append({
                    "user_id": user_id,
                    "user_name": user.email.split('@')[0],
                    "reason": str(e)
                })
        
        return {
            "added_count": len(added_users),
            "failed_count": len(failed_users),
            "added_users": added_users,
            "failed_users": failed_users
        }
    
    async def get_pending_invitations(self, group_id: str) -> List[dict]:
        """
        获取群聊的待审核邀请列表（仅老师可见）
        
        Args:
            group_id: 群聊ID
        
        Returns:
            待审核邀请列表
        """
        redis_client = get_redis_client()
        
        # 获取所有待审核邀请ID
        redis_key = f"group_pending_invitations:{group_id}"
        invitation_ids = await redis_client.smembers(redis_key)
        print(f"🔍 查询待审核邀请: key={redis_key}, 邀请ID列表={invitation_ids}")
        
        invitations = []
        for invitation_id in invitation_ids:
            # 处理字节串转换
            if isinstance(invitation_id, bytes):
                invitation_id = invitation_id.decode('utf-8')
            
            invitation_key = f"group_invitation:{invitation_id}"
            invitation_data = await redis_client.get(invitation_key)
            print(f"🔍 查询邀请数据: key={invitation_key}, data={invitation_data}")
            
            if invitation_data:
                invitations.append(json.loads(invitation_data))
        
        # 按创建时间排序
        invitations.sort(key=lambda x: x['created_at'], reverse=True)
        print(f"🔍 返回邀请列表: {len(invitations)}条邀请")
        
        return invitations
    
    async def review_invitation(self, invitation_id: str, teacher_id: int, approved: bool, reject_reason: Optional[str] = None) -> dict:
        """
        老师审核邀请
        
        Args:
            invitation_id: 邀请ID
            teacher_id: 审核老师ID
            approved: 是否批准
            reject_reason: 拒绝理由
        
        Returns:
            审核结果
        """
        from app.models.user_model import User
        
        redis_client = get_redis_client()
        
        # 获取邀请信息
        invitation_data = await redis_client.get(f"group_invitation:{invitation_id}")
        if not invitation_data:
            raise Exception("邀请不存在")
        
        invitation = json.loads(invitation_data)
        
        # 检查邀请状态
        if invitation['status'] != 'pending':
            raise Exception(f"邀请已{invitation['status']}")
        
        # 更新邀请状态
        invitation['status'] = 'approved' if approved else 'rejected'
        invitation['reviewed_at'] = datetime.now().isoformat()
        invitation['reviewed_by'] = teacher_id
        
        if not approved:
            invitation['reject_reason'] = reject_reason
        
        # 如果批准，添加用户到群聊
        if approved:
            try:
                group_id = invitation['group_id']
                invited_user_id = invitation['invited_user_id']
                
                # 获取群聊信息
                group = self.driver.channels.get_channel(group_id)
                team_id = group['team_id']
                
                # 确保用户在Mattermost中存在
                mattermost_user_id = await self._ensure_mattermost_user_exists(invited_user_id)
                
                # 确保用户是团队成员
                try:
                    self.admin_driver.teams.add_user_to_team(
                        team_id,
                        options={'team_id': team_id, 'user_id': mattermost_user_id}
                    )
                except:
                    pass
                
                # 添加用户到频道
                self.admin_driver.channels.add_user(group_id, options={'user_id': mattermost_user_id})
                
            except Exception as e:
                raise Exception(f"添加用户到群聊失败: {str(e)}")
        
        # 保存更新后的邀请信息
        await redis_client.setex(
            f"group_invitation:{invitation_id}",
            86400 * 7,
            json.dumps(invitation, ensure_ascii=False)
        )
        
        # 从待审核列表中移除
        await redis_client.srem(f"group_pending_invitations:{invitation['group_id']}", invitation_id)
        
        return invitation
    
    async def get_user_invitations(self, user_id: int) -> List[dict]:
        """
        获取用户收到的所有邀请
        
        Args:
            user_id: 用户ID
        
        Returns:
            邀请列表
        """
        redis_client = get_redis_client()
        
        # 获取用户的所有邀请
        invitations = []
        
        # 扫描所有邀请
        cursor = 0
        while True:
            cursor, keys = await redis_client.scan(cursor, match="group_invitation:*")
            
            for key in keys:
                invitation_data = await redis_client.get(key)
                if invitation_data:
                    invitation = json.loads(invitation_data)
                    if invitation['invited_user_id'] == user_id:
                        invitations.append(invitation)
            
            if cursor == 0:
                break
        
        # 按创建时间排序
        invitations.sort(key=lambda x: x['created_at'], reverse=True)
        
        return invitations
