#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交互式界面模块
提供用户友好的交互式操作界面
"""

import os
from typing import Optional, List, Dict
from ..core import ConfigManager, BackupAnalyzer, FileExtractor
from ..utils import BackupDiscovery, PermissionChecker


class InteractiveMode:
    """交互式模式管理器"""
    
    def __init__(self, config_manager: ConfigManager = None):
        self.config_manager = config_manager or ConfigManager()
        self.discovery = BackupDiscovery()
        self.selected_backup = None
        self.selected_output = None
    
    def run(self) -> bool:
        """运行交互式模式"""
        print("🎯 微信备份提取工具 - 交互式模式")
        print("=" * 50)
        
        # 1. 权限检查
        if not self._check_permissions():
            return False
        
        # 2. 选择备份
        if not self._select_backup():
            return False
        
        # 3. 选择输出目录
        if not self._select_output_directory():
            return False
        
        # 4. 选择提取选项
        extract_options = self._select_extract_options()
        
        # 5. 执行提取
        return self._execute_extraction(extract_options)
    
    def _check_permissions(self) -> bool:
        """检查系统权限"""
        print("\n🔍 检查系统权限...")
        
        if PermissionChecker.print_permission_status():
            return True
        
        print("\n❌ 权限检查失败")
        retry = input("是否继续尝试? (y/N): ").strip().lower()
        return retry in ['y', 'yes']
    
    def _select_backup(self) -> bool:
        """选择备份"""
        print("\n📱 查找iOS备份...")
        
        backups = self.discovery.discover_all_backups()
        if not backups:
            print("❌ 未发现任何iOS备份")
            backup_path = input("请手动输入备份路径: ").strip()
            if backup_path and os.path.exists(backup_path):
                self.selected_backup = {
                    'path': backup_path,
                    'id': 'manual',
                    'manual': True
                }
                return True
            return False
        
        # 显示备份列表
        self.discovery.print_backup_list(backups)
        
        # 用户选择
        while True:
            try:
                choice = input(f"\n请选择备份 (1-{len(backups)}) 或输入自定义路径: ").strip()
                
                if choice.isdigit():
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(backups):
                        self.selected_backup = backups[choice_idx]
                        return True
                    else:
                        print("❌ 无效选择，请重试")
                elif os.path.exists(choice):
                    self.selected_backup = {
                        'path': choice,
                        'id': 'manual',
                        'manual': True
                    }
                    return True
                elif choice.lower() in ['q', 'quit', 'exit']:
                    return False
                else:
                    print("❌ 无效输入，请重试 (输入 'q' 退出)")
                    
            except ValueError:
                print("❌ 请输入有效的数字")
            except KeyboardInterrupt:
                print("\n⏹️  用户取消操作")
                return False
    
    def _select_output_directory(self) -> bool:
        """选择输出目录"""
        default_output = self.config_manager.get('DEFAULT', 'output_dir')
        
        print(f"\n📁 输出目录设置")
        print(f"默认输出目录: {default_output}")
        
        output_path = input("输出目录 (直接回车使用默认): ").strip()
        if not output_path:
            output_path = default_output
        
        # 检查输出目录权限
        perm_check = PermissionChecker.check_output_directory_permissions(output_path)
        if not (perm_check['can_create'] or perm_check['can_write']):
            print(f"❌ 输出目录权限不足: {perm_check['error_message']}")
            return False
        
        self.selected_output = output_path
        print(f"✓ 输出目录: {output_path}")
        return True
    
    def _select_extract_options(self) -> Dict:
        """选择提取选项"""
        print(f"\n⚙️  提取选项")
        
        options = {
            'extract_all': True,
            'file_types': ['main', 'contacts', 'messages', 'oplog'],
            'analyze_only': False
        }
        
        # 简化选择：提供几个预设选项
        print("选择提取模式:")
        print("1. 全部文件 (推荐)")
        print("2. 仅数据库文件")
        print("3. 仅聊天记录")
        print("4. 仅分析不提取")
        print("5. 自定义选择")
        
        while True:
            try:
                choice = input("请选择 (1-5): ").strip()
                
                if choice == '1':
                    # 默认已设置为全部
                    break
                elif choice == '2':
                    options['file_types'] = ['main', 'contacts', 'oplog']
                    break
                elif choice == '3':
                    options['file_types'] = ['messages']
                    break
                elif choice == '4':
                    options['analyze_only'] = True
                    options['extract_all'] = False
                    break
                elif choice == '5':
                    options = self._custom_file_selection()
                    break
                else:
                    print("❌ 无效选择，请重试")
                    
            except KeyboardInterrupt:
                print("\n⏹️  用户取消操作")
                return {'extract_all': False}
        
        return options
    
    def _custom_file_selection(self) -> Dict:
        """自定义文件选择"""
        print("\n自定义文件选择:")
        
        file_options = {
            'main': '主数据库 (MM.sqlite)',
            'contacts': '联系人数据库 (WCDB_Contact.sqlite)',
            'messages': '聊天记录 (message_*.sqlite)',
            'oplog': '操作日志 (WCDB_OpLog.sqlite)'
        }
        
        selected_types = []
        
        for key, description in file_options.items():
            choice = input(f"提取 {description}? (Y/n): ").strip().lower()
            if choice in ['', 'y', 'yes']:
                selected_types.append(key)
        
        if not selected_types:
            print("⚠️  未选择任何文件类型，将提取所有文件")
            selected_types = list(file_options.keys())
        
        return {
            'extract_all': False,
            'file_types': selected_types,
            'analyze_only': False
        }
    
    def _execute_extraction(self, options: Dict) -> bool:
        """执行提取"""
        if not self.selected_backup or not self.selected_output:
            print("❌ 备份或输出目录未选择")
            return False
        
        backup_path = self.selected_backup['path']
        
        print(f"\n🚀 开始处理...")
        print(f"备份: {self.selected_backup.get('id', 'Unknown')}")
        print(f"路径: {backup_path}")
        print(f"输出: {self.selected_output}")
        print("-" * 50)
        
        try:
            # 分析阶段
            analyzer = BackupAnalyzer(backup_path)
            analysis_result = analyzer.analyze_wechat_files()
            
            if not analysis_result.get('success', False):
                print(f"❌ 分析失败: {analysis_result.get('error', 'Unknown error')}")
                return False
            
            # 如果仅分析，到此结束
            if options.get('analyze_only', False):
                print("✓ 分析完成（仅分析模式）")
                return True
            
            # 提取阶段
            extractor = FileExtractor(backup_path, self.selected_output)
            
            if options.get('extract_all', True):
                extract_result = extractor.extract_all(analysis_result)
            else:
                extract_result = extractor.extract_selective(
                    options.get('file_types', []), 
                    analysis_result
                )
            
            if extract_result.get('success', False):
                print(f"\n🎉 提取成功完成!")
                print(f"✓ 提取了 {extract_result['extracted_count']} 个文件")
                print(f"✓ 输出目录: {extract_result['output_path']}")
                return True
            else:
                print(f"❌ 提取失败: {extract_result.get('error', 'Unknown error')}")
                return False
                
        except KeyboardInterrupt:
            print("\n⏹️  用户取消操作")
            return False
        except Exception as e:
            print(f"❌ 处理过程中出错: {e}")
            return False
