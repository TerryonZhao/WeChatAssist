#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
备份分析模块
负责分析iOS备份中的微信文件
"""

import sqlite3
import os
from typing import Dict, List, Tuple, Optional


class BackupAnalyzer:
    """备份分析器"""
    
    def __init__(self, backup_path: str):
        self.backup_path = backup_path
        self.manifest_db = os.path.join(backup_path, 'Manifest.db')
        self.important_files = {}
        
    def validate_backup(self) -> bool:
        """验证备份路径的有效性"""
        if not os.path.exists(self.backup_path):
            print(f"❌ 备份路径不存在: {self.backup_path}")
            return False
        
        if not os.path.exists(self.manifest_db):
            print(f"❌ Manifest.db不存在: {self.manifest_db}")
            return False
        
        # 检查是否有Info.plist和Status.plist
        info_plist = os.path.join(self.backup_path, 'Info.plist')
        if not os.path.exists(info_plist):
            print(f"⚠️  警告: 未找到Info.plist文件，可能不是完整的iOS备份")
        
        return True
    
    def check_wechat_exists(self) -> bool:
        """检查备份中是否存在微信数据"""
        try:
            conn = sqlite3.connect(self.manifest_db)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM Files WHERE domain LIKE '%tencent.xin%'")
            count = cursor.fetchone()[0]
            conn.close()
            return count > 0
        except Exception as e:
            print(f"❌ 检查微信数据时出错: {e}")
            return False
    
    def analyze_wechat_files(self) -> Dict:
        """分析微信文件并返回详细信息"""
        if not self.validate_backup():
            return {'success': False, 'error': 'Backup validation failed'}
        
        print("🔍 分析微信文件...")
        
        try:
            conn = sqlite3.connect(self.manifest_db)
            cursor = conn.cursor()
            
            # 查找数据库文件
            cursor.execute("""
                SELECT fileID, relativePath, flags, file
                FROM Files 
                WHERE domain LIKE '%tencent.xin%' 
                AND (relativePath LIKE '%.sqlite' OR relativePath LIKE '%.db')
                ORDER BY relativePath
            """)
            
            db_files = cursor.fetchall()
            self._categorize_files(db_files)
            
            # 统计信息
            cursor.execute("SELECT COUNT(*) FROM Files WHERE domain LIKE '%tencent.xin%'")
            total_files = cursor.fetchone()[0]
            
            # 获取其他微信文件统计
            stats = self._get_file_statistics(cursor)
            
            conn.close()
            
            result = {
                'success': True,
                'important_files': dict(self.important_files),
                'total_files': total_files,
                'statistics': stats,
                'backup_path': self.backup_path
            }
            
            self._print_analysis_summary(result)
            return result
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _categorize_files(self, db_files: List[Tuple]):
        """分类重要文件"""
        for file_id, path, flags, file_blob in db_files:
            if 'MM.sqlite' in path:
                self.important_files['main'] = {
                    'file_id': file_id,
                    'path': path,
                    'description': '主数据库'
                }
            elif 'WCDB_Contact.sqlite' in path:
                self.important_files['contacts'] = {
                    'file_id': file_id,
                    'path': path,
                    'description': '联系人数据库'
                }
            elif 'message_' in path and '.sqlite' in path:
                if 'messages' not in self.important_files:
                    self.important_files['messages'] = []
                self.important_files['messages'].append({
                    'file_id': file_id,
                    'path': path,
                    'description': f'聊天记录{len(self.important_files.get("messages", [])) + 1}'
                })
            elif 'WCDB_OpLog.sqlite' in path:
                self.important_files['oplog'] = {
                    'file_id': file_id,
                    'path': path,
                    'description': '操作日志'
                }
    
    def _get_file_statistics(self, cursor) -> Dict:
        """获取文件统计信息"""
        stats = {}
        
        # 图片文件
        cursor.execute("""
            SELECT COUNT(*) FROM Files 
            WHERE domain LIKE '%tencent.xin%' 
            AND (relativePath LIKE '%.jpg' OR relativePath LIKE '%.png' OR relativePath LIKE '%.gif')
        """)
        stats['images'] = cursor.fetchone()[0]
        
        # 音频文件
        cursor.execute("""
            SELECT COUNT(*) FROM Files 
            WHERE domain LIKE '%tencent.xin%' 
            AND (relativePath LIKE '%.m4a' OR relativePath LIKE '%.wav' OR relativePath LIKE '%.amr')
        """)
        stats['audio'] = cursor.fetchone()[0]
        
        # 视频文件
        cursor.execute("""
            SELECT COUNT(*) FROM Files 
            WHERE domain LIKE '%tencent.xin%' 
            AND (relativePath LIKE '%.mp4' OR relativePath LIKE '%.mov')
        """)
        stats['videos'] = cursor.fetchone()[0]
        
        return stats
    
    def _print_analysis_summary(self, result: Dict):
        """打印分析摘要"""
        print("\n=== 分析结果 ===")
        print(f"✓ 重要数据库文件: {len(result['important_files'])}")
        print(f"✓ 微信文件总数: {result['total_files']}")
        
        stats = result['statistics']
        print(f"✓ 图片文件: {stats['images']}")
        print(f"✓ 音频文件: {stats['audio']}")
        print(f"✓ 视频文件: {stats['videos']}")
        
        print("\n=== 重要文件详情 ===")
        for category, files in result['important_files'].items():
            if category == 'messages' and isinstance(files, list):
                print(f"📝 {category}: {len(files)} 个文件")
                for msg_file in files:
                    print(f"  - {msg_file['description']}")
            elif isinstance(files, dict):
                print(f"📄 {files['description']}")
    
    def get_file_path(self, file_id: str) -> str:
        """根据文件ID获取实际文件路径"""
        return os.path.join(self.backup_path, file_id[:2], file_id)
