#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权限检查模块
负责检查和验证系统权限
"""

import os
import subprocess
from typing import Dict, List, Tuple


class PermissionChecker:
    """权限检查器"""
    
    @staticmethod
    def check_backup_directory_access() -> Dict:
        """检查备份目录访问权限"""
        backup_base = f"/Users/{os.getenv('USER', 'unknown')}/Library/Application Support/MobileSync/Backup"
        
        result = {
            'has_permission': False,
            'directory_exists': False,
            'can_list': False,
            'error_message': None,
            'backup_base': backup_base
        }
        
        try:
            # 检查目录是否存在
            if os.path.exists(backup_base):
                result['directory_exists'] = True
                
                # 尝试列出目录内容
                try:
                    os.listdir(backup_base)
                    result['can_list'] = True
                    result['has_permission'] = True
                except PermissionError as e:
                    result['error_message'] = f"权限被拒绝: {e}"
                except Exception as e:
                    result['error_message'] = f"其他错误: {e}"
            else:
                result['error_message'] = "备份目录不存在"
                
        except Exception as e:
            result['error_message'] = f"检查过程中出错: {e}"
        
        return result
    
    @staticmethod
    def check_full_disk_access() -> Dict:
        """检查完全磁盘访问权限"""
        # 尝试访问一些需要特殊权限的系统目录
        test_paths = [
            "/Users/{}/Library/Application Support/MobileSync".format(os.getenv('USER', 'unknown')),
            "/System/Library/CoreServices/SystemUIServer.app",
        ]
        
        results = {}
        has_full_access = True
        
        for path in test_paths:
            try:
                if os.path.exists(path):
                    # 尝试列出内容
                    os.listdir(path)
                    results[path] = {'accessible': True, 'error': None}
                else:
                    results[path] = {'accessible': False, 'error': 'Path does not exist'}
                    has_full_access = False
            except PermissionError:
                results[path] = {'accessible': False, 'error': 'Permission denied'}
                has_full_access = False
            except Exception as e:
                results[path] = {'accessible': False, 'error': str(e)}
                has_full_access = False
        
        return {
            'has_full_disk_access': has_full_access,
            'test_results': results
        }
    
    @staticmethod
    def check_output_directory_permissions(output_path: str) -> Dict:
        """检查输出目录权限"""
        result = {
            'can_create': False,
            'can_write': False,
            'exists': False,
            'error_message': None
        }
        
        try:
            # 检查目录是否存在
            if os.path.exists(output_path):
                result['exists'] = True
                
                # 检查写入权限
                test_file = os.path.join(output_path, '.test_write_permission')
                try:
                    with open(test_file, 'w') as f:
                        f.write('test')
                    os.remove(test_file)
                    result['can_write'] = True
                except Exception as e:
                    result['error_message'] = f"无法写入: {e}"
            else:
                # 尝试创建目录
                try:
                    os.makedirs(output_path, exist_ok=True)
                    result['can_create'] = True
                    result['exists'] = True
                    
                    # 测试写入
                    test_file = os.path.join(output_path, '.test_write_permission')
                    with open(test_file, 'w') as f:
                        f.write('test')
                    os.remove(test_file)
                    result['can_write'] = True
                    
                except Exception as e:
                    result['error_message'] = f"无法创建或写入: {e}"
                    
        except Exception as e:
            result['error_message'] = f"检查过程出错: {e}"
        
        return result
    
    @staticmethod
    def get_permission_fix_suggestions() -> List[str]:
        """获取权限修复建议"""
        return [
            "1. 打开 系统设置 > 隐私与安全性 > 完全磁盘访问权限",
            "2. 点击左下角的锁图标并输入密码进行解锁",
            "3. 点击 '+' 按钮添加应用程序",
            "4. 选择并添加 '终端' 应用程序",
            "5. 如果使用IDE运行脚本，也需要添加对应的IDE应用",
            "6. 重新启动终端或IDE应用程序",
            "7. 重新运行脚本"
        ]
    
    @staticmethod
    def print_permission_status():
        """打印权限状态报告"""
        print("🔍 权限检查报告")
        print("=" * 50)
        
        # 检查备份目录权限
        backup_check = PermissionChecker.check_backup_directory_access()
        print(f"📁 备份目录权限: {'✓' if backup_check['has_permission'] else '❌'}")
        if not backup_check['has_permission']:
            print(f"   错误: {backup_check['error_message']}")
        
        # 检查完全磁盘访问权限
        full_disk_check = PermissionChecker.check_full_disk_access()
        print(f"💾 完全磁盘访问: {'✓' if full_disk_check['has_full_disk_access'] else '❌'}")
        
        # 如果有权限问题，显示修复建议
        if not backup_check['has_permission'] or not full_disk_check['has_full_disk_access']:
            print("\n🔧 修复建议:")
            for suggestion in PermissionChecker.get_permission_fix_suggestions():
                print(f"   {suggestion}")
        
        print("=" * 50)
        return backup_check['has_permission'] and full_disk_check['has_full_disk_access']
