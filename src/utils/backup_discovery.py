#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
备份发现模块
负责自动发现和管理iOS备份
"""

import os
import sqlite3
from typing import List, Dict, Optional
from datetime import datetime
import plistlib


class BackupDiscovery:
    """备份发现器"""
    
    def __init__(self):
        self.backup_base = f"/Users/{os.getenv('USER', 'unknown')}/Library/Application Support/MobileSync/Backup"
    
    def discover_all_backups(self) -> List[Dict]:
        """发现所有iOS备份"""
        discovered_backups = []
        
        if not os.path.exists(self.backup_base):
            return discovered_backups
        
        try:
            for item in os.listdir(self.backup_base):
                backup_path = os.path.join(self.backup_base, item)
                
                if os.path.isdir(backup_path):
                    backup_info = self._analyze_backup(backup_path, item)
                    if backup_info:
                        discovered_backups.append(backup_info)
        
        except PermissionError:
            print("❌ 无权限访问备份目录，请检查系统权限设置")
        except Exception as e:
            print(f"❌ 发现备份时出错: {e}")
        
        # 按修改时间排序（最新的在前）
        discovered_backups.sort(key=lambda x: x.get('last_modified', 0), reverse=True)
        return discovered_backups
    
    def discover_wechat_backups(self) -> List[Dict]:
        """发现包含微信数据的备份"""
        all_backups = self.discover_all_backups()
        return [backup for backup in all_backups if backup.get('has_wechat', False)]
    
    def _analyze_backup(self, backup_path: str, backup_id: str) -> Optional[Dict]:
        """分析单个备份"""
        manifest_db = os.path.join(backup_path, 'Manifest.db')
        info_plist = os.path.join(backup_path, 'Info.plist')
        
        # 检查必要文件
        if not os.path.exists(manifest_db):
            return None
        
        backup_info = {
            'id': backup_id,
            'path': backup_path,
            'has_wechat': False,
            'device_info': {},
            'backup_info': {},
            'file_counts': {},
            'last_modified': 0
        }
        
        try:
            # 获取备份基本信息
            stat = os.stat(backup_path)
            backup_info['last_modified'] = stat.st_mtime
            backup_info['last_modified_str'] = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            
            # 读取Info.plist
            if os.path.exists(info_plist):
                backup_info['device_info'] = self._read_info_plist(info_plist)
            
            # 分析Manifest.db
            backup_info['backup_info'], backup_info['file_counts'] = self._analyze_manifest_db(manifest_db)
            
            # 检查是否有微信数据
            backup_info['has_wechat'] = self._check_wechat_in_backup(manifest_db)
            
        except Exception as e:
            print(f"⚠️  分析备份 {backup_id} 时出错: {e}")
        
        return backup_info
    
    def _read_info_plist(self, info_plist_path: str) -> Dict:
        """读取Info.plist文件"""
        try:
            with open(info_plist_path, 'rb') as f:
                plist_data = plistlib.load(f)
            
            return {
                'device_name': plist_data.get('Device Name', 'Unknown'),
                'display_name': plist_data.get('Display Name', 'Unknown'),
                'product_type': plist_data.get('Product Type', 'Unknown'),
                'product_version': plist_data.get('Product Version', 'Unknown'),
                'serial_number': plist_data.get('Serial Number', 'Unknown'),
                'unique_identifier': plist_data.get('Unique Identifier', 'Unknown'),
                'last_backup_date': plist_data.get('Last Backup Date', None)
            }
        except Exception as e:
            print(f"⚠️  读取Info.plist失败: {e}")
            return {}
    
    def _analyze_manifest_db(self, manifest_db_path: str) -> tuple:
        """分析Manifest.db文件"""
        backup_info = {}
        file_counts = {
            'total_files': 0,
            'app_files': 0,
            'system_files': 0,
            'media_files': 0
        }
        
        try:
            conn = sqlite3.connect(manifest_db_path)
            cursor = conn.cursor()
            
            # 总文件数
            cursor.execute("SELECT COUNT(*) FROM Files")
            file_counts['total_files'] = cursor.fetchone()[0]
            
            # 应用文件数
            cursor.execute("SELECT COUNT(*) FROM Files WHERE domain LIKE 'AppDomain-%'")
            file_counts['app_files'] = cursor.fetchone()[0]
            
            # 系统文件数
            cursor.execute("SELECT COUNT(*) FROM Files WHERE domain LIKE 'SystemDomain-%'")
            file_counts['system_files'] = cursor.fetchone()[0]
            
            # 媒体文件数
            cursor.execute("""
                SELECT COUNT(*) FROM Files 
                WHERE relativePath LIKE '%.jpg' 
                   OR relativePath LIKE '%.png' 
                   OR relativePath LIKE '%.mp4' 
                   OR relativePath LIKE '%.mov'
                   OR relativePath LIKE '%.m4a'
            """)
            file_counts['media_files'] = cursor.fetchone()[0]
            
            # 获取备份版本信息
            try:
                cursor.execute("SELECT * FROM Properties")
                properties = dict(cursor.fetchall())
                backup_info['properties'] = properties
            except:
                pass
            
            conn.close()
            
        except Exception as e:
            print(f"⚠️  分析Manifest.db失败: {e}")
        
        return backup_info, file_counts
    
    def _check_wechat_in_backup(self, manifest_db_path: str) -> bool:
        """检查备份中是否包含微信数据"""
        try:
            conn = sqlite3.connect(manifest_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM Files WHERE domain LIKE '%tencent.xin%'")
            count = cursor.fetchone()[0]
            conn.close()
            return count > 0
        except:
            return False
    
    def print_backup_list(self, backups: List[Dict] = None):
        """打印备份列表"""
        if backups is None:
            backups = self.discover_all_backups()
        
        if not backups:
            print("❌ 未发现任何iOS备份")
            return
        
        print("📱 发现的iOS备份:")
        print("-" * 80)
        
        for i, backup in enumerate(backups, 1):
            device_info = backup.get('device_info', {})
            wechat_status = "✓" if backup.get('has_wechat', False) else "❌"
            
            print(f"{i:2d}. {backup['id']}")
            print(f"    设备: {device_info.get('device_name', 'Unknown')} ({device_info.get('product_type', 'Unknown')})")
            print(f"    系统: {device_info.get('product_version', 'Unknown')}")
            print(f"    时间: {backup.get('last_modified_str', 'Unknown')}")
            print(f"    微信: {wechat_status}")
            print(f"    文件: {backup.get('file_counts', {}).get('total_files', 0):,}")
            print()
    
    def get_backup_by_index(self, index: int, backups: List[Dict] = None) -> Optional[Dict]:
        """根据索引获取备份"""
        if backups is None:
            backups = self.discover_all_backups()
        
        if 0 <= index < len(backups):
            return backups[index]
        return None
    
    def find_latest_wechat_backup(self) -> Optional[Dict]:
        """查找最新的包含微信数据的备份"""
        wechat_backups = self.discover_wechat_backups()
        return wechat_backups[0] if wechat_backups else None
