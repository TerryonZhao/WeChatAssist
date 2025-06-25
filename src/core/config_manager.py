#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
负责加载和管理应用配置
"""

import configparser
import os
from typing import Dict, Any


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = None):
        self.config = configparser.ConfigParser()
        self._set_defaults()
        
        if config_file and os.path.exists(config_file):
            self.load_config(config_file)
    
    def _set_defaults(self):
        """设置默认配置"""
        default_config = {
            'DEFAULT': {
                'output_dir': './extracted_wechat_files',
                'verbose': 'true',
                'auto_create_dir': 'true'
            },
            'file_types': {
                'extract_main_db': 'true',
                'extract_contacts': 'true', 
                'extract_messages': 'true',
                'extract_oplog': 'true',
                'extract_images': 'false',
                'extract_audio': 'false',
                'extract_videos': 'false'
            },
            'advanced': {
                'generate_script': 'true',
                'script_name': 'extract_wechat.sh',
                'backup_extracted_files': 'false',
                'compress_output': 'false'
            }
        }
        
        # 设置默认值
        for section, options in default_config.items():
            if section != 'DEFAULT':
                self.config.add_section(section)
            for key, value in options.items():
                self.config.set(section, key, value)
    
    def load_config(self, config_file: str):
        """加载配置文件"""
        try:
            self.config.read(config_file, encoding='utf-8')
            print(f"✓ 已加载配置文件: {config_file}")
            return True
        except Exception as e:
            print(f"❌ 加载配置文件失败: {e}")
            return False
    
    def get(self, section: str, key: str, fallback: str = None) -> str:
        """获取配置值"""
        return self.config.get(section, key, fallback=fallback)
    
    def getboolean(self, section: str, key: str, fallback: bool = False) -> bool:
        """获取布尔配置值"""
        return self.config.getboolean(section, key, fallback=fallback)
    
    def get_section(self, section: str) -> Dict[str, str]:
        """获取整个配置段"""
        if self.config.has_section(section):
            return dict(self.config.items(section))
        return {}
    
    def save_config(self, config_file: str):
        """保存配置到文件"""
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                self.config.write(f)
            print(f"✓ 配置已保存到: {config_file}")
            return True
        except Exception as e:
            print(f"❌ 保存配置失败: {e}")
            return False
