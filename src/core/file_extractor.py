#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件提取模块
负责从iOS备份中提取微信文件
"""

import os
import shutil
from typing import Dict, List, Optional
from .backup_analyzer import BackupAnalyzer


class FileExtractor:
    """文件提取器"""
    
    def __init__(self, backup_path: str, output_path: str):
        self.backup_path = backup_path
        self.output_path = output_path
        self.analyzer = BackupAnalyzer(backup_path)
        self.extracted_files = []
        
    def extract_all(self, analysis_result: Dict = None) -> Dict:
        """提取所有重要文件"""
        if analysis_result is None:
            analysis_result = self.analyzer.analyze_wechat_files()
        
        if not analysis_result.get('success', False):
            return {'success': False, 'error': 'Analysis failed'}
        
        # 创建输出目录
        os.makedirs(self.output_path, exist_ok=True)
        print(f"\n📦 开始提取到: {self.output_path}")
        
        important_files = analysis_result['important_files']
        success_count = 0
        total_count = 0
        
        # 提取各类文件
        file_mappings = [
            ('main', 'MM.sqlite'),
            ('contacts', 'WCDB_Contact.sqlite'),
            ('oplog', 'WCDB_OpLog.sqlite')
        ]
        
        for key, filename in file_mappings:
            if key in important_files:
                total_count += 1
                file_info = important_files[key]
                if self._extract_single_file(file_info, filename):
                    success_count += 1
        
        # 提取聊天记录
        if 'messages' in important_files:
            for i, msg_file in enumerate(important_files['messages'], 1):
                total_count += 1
                filename = f'message_{i}.sqlite'
                if self._extract_single_file(msg_file, filename):
                    success_count += 1
        
        result = {
            'success': success_count > 0,
            'extracted_count': success_count,
            'total_count': total_count,
            'output_path': self.output_path,
            'extracted_files': self.extracted_files.copy()
        }
        
        self._print_extraction_summary(result)
        return result
    
    def extract_selective(self, file_types: List[str], analysis_result: Dict = None) -> Dict:
        """选择性提取指定类型的文件"""
        if analysis_result is None:
            analysis_result = self.analyzer.analyze_wechat_files()
        
        if not analysis_result.get('success', False):
            return {'success': False, 'error': 'Analysis failed'}
        
        os.makedirs(self.output_path, exist_ok=True)
        print(f"\n📦 选择性提取到: {self.output_path}")
        
        important_files = analysis_result['important_files']
        success_count = 0
        total_count = 0
        
        # 根据选择的类型进行提取
        type_mappings = {
            'main': ('main', 'MM.sqlite'),
            'contacts': ('contacts', 'WCDB_Contact.sqlite'),
            'oplog': ('oplog', 'WCDB_OpLog.sqlite'),
            'messages': ('messages', None)  # 特殊处理
        }
        
        for file_type in file_types:
            if file_type in type_mappings:
                key, filename = type_mappings[file_type]
                
                if key in important_files:
                    if file_type == 'messages':
                        # 处理多个聊天记录文件
                        for i, msg_file in enumerate(important_files['messages'], 1):
                            total_count += 1
                            msg_filename = f'message_{i}.sqlite'
                            if self._extract_single_file(msg_file, msg_filename):
                                success_count += 1
                    else:
                        total_count += 1
                        file_info = important_files[key]
                        if self._extract_single_file(file_info, filename):
                            success_count += 1
        
        result = {
            'success': success_count > 0,
            'extracted_count': success_count,
            'total_count': total_count,
            'output_path': self.output_path,
            'extracted_files': self.extracted_files.copy()
        }
        
        self._print_extraction_summary(result)
        return result
    
    def _extract_single_file(self, file_info: Dict, dst_filename: str) -> bool:
        """提取单个文件"""
        try:
            file_id = file_info['file_id']
            description = file_info['description']
            
            src_path = os.path.join(self.backup_path, file_id[:2], file_id)
            dst_path = os.path.join(self.output_path, dst_filename)
            
            if not os.path.exists(src_path):
                print(f"  ❌ {description} - 源文件不存在: {src_path}")
                return False
            
            shutil.copy2(src_path, dst_path)
            
            # 记录提取的文件信息
            file_size = os.path.getsize(dst_path)
            size_mb = file_size / (1024 * 1024)
            
            self.extracted_files.append({
                'name': dst_filename,
                'description': description,
                'size_bytes': file_size,
                'size_mb': round(size_mb, 1),
                'source_id': file_id
            })
            
            print(f"  ✓ {description} ({size_mb:.1f} MB)")
            return True
            
        except Exception as e:
            print(f"  ❌ {file_info.get('description', 'Unknown')} - 提取失败: {e}")
            return False
    
    def _print_extraction_summary(self, result: Dict):
        """打印提取摘要"""
        print(f"\n=== 提取完成 ===")
        print(f"✓ 成功提取: {result['extracted_count']}/{result['total_count']} 个文件")
        
        if result['extracted_files']:
            total_size = sum(f['size_mb'] for f in result['extracted_files'])
            print(f"✓ 总大小: {total_size:.1f} MB")
            print(f"✓ 输出目录: {result['output_path']}")
    
    def get_extracted_files_info(self) -> List[Dict]:
        """获取已提取文件的详细信息"""
        return self.extracted_files.copy()
    
    def verify_extracted_files(self) -> Dict:
        """验证已提取的文件"""
        verification_result = {
            'valid_files': [],
            'invalid_files': [],
            'missing_files': []
        }
        
        for file_info in self.extracted_files:
            file_path = os.path.join(self.output_path, file_info['name'])
            
            if not os.path.exists(file_path):
                verification_result['missing_files'].append(file_info)
                continue
            
            current_size = os.path.getsize(file_path)
            if current_size == file_info['size_bytes']:
                verification_result['valid_files'].append(file_info)
            else:
                verification_result['invalid_files'].append({
                    **file_info,
                    'current_size': current_size
                })
        
        return verification_result
