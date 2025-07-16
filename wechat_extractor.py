#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 微信备份提取工具 - 交互式版本
📱 交互式微信备份提取工具
"""

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core import ConfigManager
from src.cli import InteractiveMode


class WeChatExtractorPipeline:
    """微信提取器管道"""
    
    def __init__(self, config_file: str = None):
        self.config_manager = ConfigManager(config_file)
        
    def run_interactive(self) -> bool:
        """运行交互式模式"""
        interactive = InteractiveMode(self.config_manager)
        return interactive.run()


def main():
    """主函数"""
    print("🎯 微信备份提取工具")
    print("=" * 50)
    
    try:
        # 创建管道并运行交互式模式
        pipeline = WeChatExtractorPipeline()
        return pipeline.run_interactive()
    
    except KeyboardInterrupt:
        print("\n⏹️  用户取消操作")
        return False
    except Exception as e:
        print(f"❌ 程序执行出错: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
