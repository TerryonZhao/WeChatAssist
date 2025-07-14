#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 微信聊天记录分析工具
根据联系人、时间范围等条件提取和分析特定的聊天记录
"""

import sqlite3
import json
import re
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any


class ChatAnalyzer:
    """微信聊天记录分析器"""
    
    def __init__(self, extracted_files_dir: str):
        """
        初始化分析器
        
        Args:
            extracted_files_dir: 提取文件目录路径
        """
        self.extracted_dir = Path(extracted_files_dir)
        self.contact_db = self.extracted_dir / "WCDB_Contact.sqlite"
        self.message_dbs = list(self.extracted_dir.glob("message_*.sqlite"))
        
        # 缓存联系人信息
        self._contacts_cache = None
        self._contact_mapping = None  # 哈希值到用户名的映射
        
    def _get_contacts(self) -> Dict[str, Dict[str, Any]]:
        """获取联系人信息"""
        if self._contacts_cache is not None:
            return self._contacts_cache
            
        contacts = {}
        if not self.contact_db.exists():
            print("⚠️  联系人数据库不存在")
            return contacts
            
        try:
            conn = sqlite3.connect(str(self.contact_db))
            cursor = conn.cursor()
            
            # 查询联系人信息
            cursor.execute("""
                SELECT userName, dbContactRemark, type, certificationFlag
                FROM Friend
            """)
            
            for row in cursor.fetchall():
                username = row[0]
                remark_blob = row[1]
                contact_type = row[2]
                cert_flag = row[3]
                
                # 解析备注信息
                remark = self._parse_contact_remark(remark_blob) if remark_blob else ""
                
                contacts[username] = {
                    'username': username,
                    'remark': remark,
                    'type': contact_type,
                    'cert_flag': cert_flag,
                    'display_name': remark if remark else username
                }
            
            conn.close()
            self._contacts_cache = contacts
            
        except Exception as e:
            print(f"❌ 读取联系人信息失败: {e}")
            
        return contacts
    
    def _parse_contact_remark(self, remark_blob: bytes) -> str:
        """解析联系人备注信息"""
        if not remark_blob:
            return ""
            
        try:
            # 尝试直接解码
            if isinstance(remark_blob, str):
                return remark_blob
            
            # 如果是bytes，尝试多种编码
            for encoding in ['utf-8', 'utf-16', 'gbk']:
                try:
                    decoded = remark_blob.decode(encoding)
                    # 过滤掉控制字符
                    decoded = ''.join(char for char in decoded if char.isprintable())
                    if decoded.strip():
                        return decoded.strip()
                except:
                    continue
                    
        except Exception:
            pass
            
        return ""
    
    def _build_contact_mapping(self):
        """构建聊天表哈希值到联系人的映射 - 改进版本"""
        if self._contact_mapping is not None:
            return
            
        contacts = self._get_contacts()
        self._contact_mapping = {}
        
        # 遍历所有消息数据库，建立表名哈希到联系人的映射
        for db_path in self.message_dbs:
            try:
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                
                # 获取所有聊天表
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name LIKE 'Chat_%'
                    AND name NOT LIKE 'ChatExt2_%'
                """)
                
                for (table_name,) in cursor.fetchall():
                    # 提取哈希值
                    hash_value = table_name.replace('Chat_', '')
                    
                    # 方法1: 尝试通过哈希值直接匹配联系人用户名
                    matched_contact = None
                    for username, contact in contacts.items():
                        # 检查是否username或其MD5哈希匹配表名
                        import hashlib
                        username_hash = hashlib.md5(username.encode('utf-8')).hexdigest()
                        if hash_value.lower() == username_hash.lower():
                            matched_contact = contact
                            break
                    
                    # 方法2: 如果直接匹配失败，尝试分析消息内容
                    if not matched_contact:
                        try:
                            # 获取该表的一些消息样本
                            cursor.execute(f"""
                                SELECT Message FROM {table_name} 
                                WHERE Message IS NOT NULL 
                                AND Message != ''
                                AND LENGTH(Message) > 0
                                LIMIT 20
                            """)
                            
                            messages = cursor.fetchall()
                            potential_usernames = set()
                            
                            for (message,) in messages:
                                if message:
                                    # 安全处理消息内容，避免编码错误
                                    try:
                                        if isinstance(message, bytes):
                                            message_str = message.decode('utf-8', errors='ignore')
                                        else:
                                            message_str = str(message)
                                        
                                        # 查找消息中的用户名模式
                                        usernames = re.findall(r'(wxid_[a-zA-Z0-9]+|[a-zA-Z0-9_]+@[a-zA-Z0-9_]+)', message_str)
                                        potential_usernames.update(usernames)
                                    except Exception:
                                        # 如果无法处理消息内容，跳过
                                        continue
                            
                            # 匹配已知联系人
                            for username in potential_usernames:
                                if username in contacts:
                                    matched_contact = contacts[username]
                                    break
                                    
                        except Exception as e:
                            print(f"⚠️  分析表 {table_name} 时出错: {e}")
                    
                    # 方法3: 如果仍然找不到，创建一个未知联系人记录
                    if not matched_contact:
                        # 尝试从表中获取一些统计信息来生成描述性名称
                        try:
                            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                            msg_count = cursor.fetchone()[0]
                            
                            cursor.execute(f"""
                                SELECT MIN(CreateTime), MAX(CreateTime) FROM {table_name}
                                WHERE CreateTime > 0
                            """)
                            time_range = cursor.fetchone()
                            
                            if time_range and time_range[0]:
                                start_date = datetime.fromtimestamp(time_range[0]).strftime('%Y-%m')
                                display_name = f"未知联系人_{start_date}_{msg_count}条消息"
                            else:
                                display_name = f"未知联系人_{hash_value[:8]}"
                                
                        except:
                            display_name = f"未知联系人_{hash_value[:8]}"
                        
                        matched_contact = {
                            'username': f'unknown_{hash_value}',
                            'display_name': display_name,
                            'remark': '',
                            'type': 0,
                            'cert_flag': 0
                        }
                    
                    self._contact_mapping[hash_value] = matched_contact
                        
                conn.close()
                
            except Exception as e:
                print(f"❌ 处理数据库 {db_path} 失败: {e}")
    
    def get_contact_list(self) -> List[Dict[str, Any]]:
        """获取联系人列表"""
        contacts = self._get_contacts()
        self._build_contact_mapping()
        
        # 合并联系人信息和聊天映射
        all_contacts = []
        
        # 添加已知联系人
        for contact in contacts.values():
            all_contacts.append(contact)
        
        # 添加聊天记录中发现的未知联系人
        for hash_value, contact in self._contact_mapping.items():
            if contact['username'].startswith('unknown_'):
                all_contacts.append(contact)
        
        return sorted(all_contacts, key=lambda x: x['display_name'])
    
    def search_messages(self, 
                       contact_filter: Optional[str] = None,
                       start_time: Optional[datetime] = None,
                       end_time: Optional[datetime] = None,
                       keyword: Optional[str] = None,
                       limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        搜索消息记录（仅文字消息）
        
        Args:
            contact_filter: 联系人过滤条件（用户名或备注名）
            start_time: 开始时间
            end_time: 结束时间
            keyword: 消息内容关键字
            limit: 限制返回数量
            
        Returns:
            消息列表（仅包含文字消息）
        """
        self._build_contact_mapping()
        contacts = self._get_contacts()
        
        all_messages = []
        
        # 确定要搜索的联系人
        target_contacts = []
        if contact_filter:
            contact_filter_lower = contact_filter.lower()
            for contact in contacts.values():
                if (contact_filter_lower in contact['username'].lower() or 
                    contact_filter_lower in contact['display_name'].lower() or
                    contact_filter_lower in contact['remark'].lower()):
                    target_contacts.append(contact)
        
        # 遍历所有消息数据库
        for db_path in self.message_dbs:
            try:
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                
                # 获取所有聊天表
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name LIKE 'Chat_%'
                    AND name NOT LIKE 'ChatExt2_%'
                """)
                
                tables = cursor.fetchall()
                
                for (table_name,) in tables:
                    hash_value = table_name.replace('Chat_', '')
                    table_contact = self._contact_mapping.get(hash_value)
                    
                    # 如果指定了联系人过滤条件，检查是否匹配
                    if contact_filter and target_contacts:
                        if not table_contact:
                            continue
                            
                        match_found = False
                        for target in target_contacts:
                            if (target['username'] == table_contact['username'] or
                                target['display_name'] == table_contact['display_name']):
                                match_found = True
                                break
                        
                        if not match_found:
                            continue
                    
                    # 构建查询条件
                    where_conditions = ["Type = 1"]  # 只处理文字消息
                    params = []
                    
                    if start_time:
                        where_conditions.append("CreateTime >= ?")
                        params.append(int(start_time.timestamp()))
                    
                    if end_time:
                        where_conditions.append("CreateTime <= ?")
                        params.append(int(end_time.timestamp()))
                    
                    if keyword:
                        where_conditions.append("Message LIKE ?")
                        params.append(f"%{keyword}%")
                    
                    # 移除message_type参数，因为我们只处理文字消息
                    
                    where_clause = " AND ".join(where_conditions)
                    
                    # 查询消息
                    query = f"""
                        SELECT CreateTime, Des, Message, Type, MesLocalID, MesSvrID, Status
                        FROM {table_name}
                        WHERE {where_clause}
                        ORDER BY CreateTime ASC
                    """
                    
                    if limit and not contact_filter:  # 如果没有联系人过滤，直接限制数量
                        query += f" LIMIT {limit}"
                    
                    cursor.execute(query, params)
                    rows = cursor.fetchall()
                    
                    for row in rows:
                        create_time, des, message, msg_type, local_id, svr_id, status = row
                        
                        # 解析时间
                        try:
                            msg_datetime = datetime.fromtimestamp(create_time)
                        except:
                            msg_datetime = None
                        
                        # 获取联系人信息
                        contact_info = table_contact or {
                            'username': f'unknown_{hash_value[:8]}',
                            'display_name': f'未知联系人_{hash_value[:8]}',
                            'remark': ''
                        }
                        
                        # 安全处理消息内容
                        safe_message = ""
                        if message:
                            try:
                                if isinstance(message, bytes):
                                    safe_message = message.decode('utf-8', errors='ignore')
                                else:
                                    safe_message = str(message)
                            except:
                                safe_message = "[无法显示的内容]"
                        
                        message_data = {
                            'contact_username': contact_info['username'],
                            'contact_display_name': contact_info['display_name'],
                            'contact_remark': contact_info.get('remark', ''),
                            'timestamp': create_time,
                            'datetime': msg_datetime,
                            'message': safe_message,
                            'message_type': msg_type,
                            'direction': des,  # 1=接收, 0=发送
                            'local_id': local_id,
                            'server_id': svr_id,
                            'status': status,
                            'table_hash': hash_value,
                            'database': db_path.name
                        }
                        
                        all_messages.append(message_data)
                
                conn.close()
                
            except Exception as e:
                print(f"❌ 搜索数据库 {db_path} 失败: {e}")
        
        # 按时间排序
        all_messages.sort(key=lambda x: x['timestamp'])
        
        # 应用数量限制
        if limit and len(all_messages) > limit:
            all_messages = all_messages[:limit]
        
        return all_messages
    
    def export_messages(self, messages: List[Dict[str, Any]], 
                       output_file: str, format: str = 'json') -> bool:
        """
        导出消息到文件
        
        Args:
            messages: 消息列表
            output_file: 输出文件路径
            format: 导出格式 ('json', 'csv', 'txt')
            
        Returns:
            是否成功
        """
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if format.lower() == 'json':
                # JSON格式
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(messages, f, ensure_ascii=False, indent=2, default=str)
            
            elif format.lower() == 'csv':
                # CSV格式
                if messages:
                    # 手动创建CSV，不依赖pandas
                    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
                        if messages:
                            fieldnames = messages[0].keys()
                            writer = csv.DictWriter(f, fieldnames=fieldnames)
                            writer.writeheader()
                            for msg in messages:
                                # 处理datetime对象
                                row = {}
                                for key, value in msg.items():
                                    if isinstance(value, datetime):
                                        row[key] = value.strftime('%Y-%m-%d %H:%M:%S')
                                    else:
                                        row[key] = value
                                writer.writerow(row)
                
            elif format.lower() == 'txt':
                # 文本格式
                with open(output_path, 'w', encoding='utf-8') as f:
                    current_contact = None
                    for msg in messages:
                        # 联系人分组
                        if current_contact != msg['contact_display_name']:
                            current_contact = msg['contact_display_name']
                            f.write(f"\n{'='*50}\n")
                            f.write(f"联系人: {current_contact}\n")
                            f.write(f"{'='*50}\n\n")
                        
                        # 消息内容
                        # 消息内容
                        if msg['direction'] == 0:
                            sender = "我"
                        else:
                            sender = msg['contact_display_name']
                            
                        time_str = msg['datetime'].strftime('%Y-%m-%d %H:%M:%S') if msg['datetime'] else "未知时间"
                        
                        f.write(f"[{time_str}] {sender}: {msg['message']}\n")
                        f.write("\n")
            
            else:
                print(f"❌ 不支持的导出格式: {format}")
                return False
            
            print(f"✅ 已导出 {len(messages)} 条消息到: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ 导出失败: {e}")
            return False
    
    def _get_message_type_description(self, msg_type: int) -> str:
        """获取消息类型描述"""
        type_map = {
            1: "文本",
            3: "图片",
            34: "语音",
            43: "视频",
            47: "表情包",
            48: "位置",
            49: "链接/小程序",
            50: "视频通话",
            62: "小视频",
            10000: "系统消息"
        }
        return type_map.get(msg_type, f"未知类型({msg_type})")
    
    def get_chat_statistics(self, contact_filter: Optional[str] = None,
                           start_time: Optional[datetime] = None,
                           end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        获取聊天统计信息
        
        Args:
            contact_filter: 联系人过滤条件
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            统计信息字典
        """
        messages = self.search_messages(
            contact_filter=contact_filter,
            start_time=start_time,
            end_time=end_time
        )
        
        if not messages:
            return {
                'total_messages': 0,
                'contacts': [],
                'message_types': {},
                'time_range': {},
                'daily_stats': {}
            }
        
        # 基本统计
        total_messages = len(messages)
        
        # 联系人统计
        contact_stats = {}
        for msg in messages:
            contact = msg['contact_display_name']
            if contact not in contact_stats:
                contact_stats[contact] = {'sent': 0, 'received': 0, 'total': 0}
            
            if msg['direction'] == 0:  # 发送
                contact_stats[contact]['sent'] += 1
            else:  # 接收
                contact_stats[contact]['received'] += 1
            contact_stats[contact]['total'] += 1
        
        # 消息类型统计
        type_stats = {}
        for msg in messages:
            msg_type = msg['message_type']
            type_desc = self._get_message_type_description(msg_type)
            type_stats[type_desc] = type_stats.get(type_desc, 0) + 1
        
        # 时间范围统计
        timestamps = [msg['timestamp'] for msg in messages if msg['timestamp']]
        if timestamps:
            time_range = {
                'earliest': datetime.fromtimestamp(min(timestamps)),
                'latest': datetime.fromtimestamp(max(timestamps)),
                'span_days': (max(timestamps) - min(timestamps)) / 86400
            }
        else:
            time_range = {}
        
        # 每日统计
        daily_stats = {}
        for msg in messages:
            if msg['datetime']:
                date_key = msg['datetime'].strftime('%Y-%m-%d')
                if date_key not in daily_stats:
                    daily_stats[date_key] = {'sent': 0, 'received': 0, 'total': 0}
                
                if msg['direction'] == 0:
                    daily_stats[date_key]['sent'] += 1
                else:
                    daily_stats[date_key]['received'] += 1
                daily_stats[date_key]['total'] += 1
        
        return {
            'total_messages': total_messages,
            'contacts': contact_stats,
            'message_types': type_stats,
            'time_range': time_range,
            'daily_stats': daily_stats
        }
