#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 微信备份提取工具 - 主执行脚本
📱 完全可复用的微信备份提取工具，支持多种使用方式

使用方法:
    python wechat_extractor.py [备份路径] [选项]
    python wechat_extractor.py --interactive
    python wechat_extractor.py --discover
"""

import sys
import os
import argparse
import json
from pathlib import Path
from datetime import datetime

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core import ConfigManager, BackupAnalyzer, FileExtractor
from src.utils import PermissionChecker, BackupDiscovery
from src.cli import InteractiveMode


class WeChatExtractorPipeline:
    """微信提取器管道"""
    
    def __init__(self, config_file: str = None):
        self.config_manager = ConfigManager(config_file)
        self.discovery = BackupDiscovery()
        
    def run_interactive(self) -> bool:
        """运行交互式模式"""
        interactive = InteractiveMode(self.config_manager)
        return interactive.run()
    
    def run_discovery(self) -> bool:
        """运行发现模式"""
        print("🔍 发现iOS备份...")
        backups = self.discovery.discover_all_backups()
        
        if not backups:
            print("❌ 未发现任何iOS备份")
            return False
        
        self.discovery.print_backup_list(backups)
        
        # 显示微信备份统计
        wechat_backups = [b for b in backups if b.get('has_wechat', False)]
        print(f"\n📊 统计信息:")
        print(f"   总备份数: {len(backups)}")
        print(f"   包含微信: {len(wechat_backups)}")
        
        return True
    
    def run_single_extraction(self, backup_path: str, output_path: str = None, 
                            analyze_only: bool = False, file_types: list = None) -> bool:
        """运行单个备份提取"""
        
        # 设置输出路径
        if output_path is None:
            output_path = self.config_manager.get('DEFAULT', 'output_dir')
        
        print(f"🎯 处理备份: {backup_path}")
        print(f"📁 输出目录: {output_path}")
        print("-" * 50)
        
        try:
            # 分析阶段
            analyzer = BackupAnalyzer(backup_path)
            analysis_result = analyzer.analyze_wechat_files()
            
            if not analysis_result.get('success', False):
                print(f"❌ 分析失败: {analysis_result.get('error', 'Unknown error')}")
                return False
            
            # 如果仅分析，返回成功
            if analyze_only:
                print("✓ 分析完成（仅分析模式）")
                return True
            
            # 提取阶段
            extractor = FileExtractor(backup_path, output_path)
            
            if file_types:
                extract_result = extractor.extract_selective(file_types, analysis_result)
            else:
                extract_result = extractor.extract_all(analysis_result)
            
            if extract_result.get('success', False):
                print(f"\n🎉 提取成功完成!")
                print(f"✓ 提取了 {extract_result['extracted_count']} 个文件")
                print(f"✓ 输出目录: {extract_result['output_path']}")
                return True
            else:
                print(f"❌ 提取失败")
                return False
                
        except Exception as e:
            print(f"❌ 处理过程中出错: {e}")
            return False
    
    def run_batch_processing(self, batch_config_file: str) -> bool:
        """运行批量处理"""
        try:
            with open(batch_config_file, 'r', encoding='utf-8') as f:
                batch_config = json.load(f)
            
            results = {}
            success_count = 0
            
            for job_name, job_config in batch_config.items():
                print(f"\n🔄 处理任务: {job_name}")
                print("-" * 30)
                
                backup_path = job_config.get('backup_path')
                output_path = job_config.get('output_path')
                file_types = job_config.get('file_types')
                
                if not backup_path:
                    print(f"❌ 任务 {job_name}: 缺少备份路径")
                    results[job_name] = {'success': False, 'error': 'Missing backup_path'}
                    continue
                
                success = self.run_single_extraction(
                    backup_path, output_path, False, file_types
                )
                
                results[job_name] = {'success': success}
                if success:
                    success_count += 1
            
            # 保存批量处理结果
            result_file = 'batch_results.json'
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': str(datetime.now()),
                    'total_jobs': len(batch_config),
                    'successful_jobs': success_count,
                    'results': results
                }, f, ensure_ascii=False, indent=2)
            
            print(f"\n📊 批量处理完成: {success_count}/{len(batch_config)} 成功")
            print(f"📄 结果已保存到: {result_file}")
            
            return success_count > 0
            
        except Exception as e:
            print(f"❌ 批量处理失败: {e}")
            return False
    
    def auto_extract_latest(self) -> bool:
        """自动提取最新的微信备份"""
        print("🔍 查找最新的微信备份...")
        
        latest_backup = self.discovery.find_latest_wechat_backup()
        if not latest_backup:
            print("❌ 未找到包含微信数据的备份")
            return False
        
        print(f"✓ 找到最新备份: {latest_backup['id']}")
        
        # 生成带时间戳的输出目录
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = f"./wechat_backup_{timestamp}"
        
        return self.run_single_extraction(latest_backup['path'], output_path)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='🎯 微信备份提取工具 - 完全可复用版本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s --interactive                    # 交互式模式
  %(prog)s --discover                       # 发现所有备份
  %(prog)s /path/to/backup                  # 提取指定备份
  %(prog)s /path/to/backup -o ./output      # 指定输出目录
  %(prog)s --auto                           # 自动提取最新备份
  %(prog)s --batch batch_config.json       # 批量处理
        """
    )
    
    # 位置参数
    parser.add_argument('backup_path', nargs='?', help='iOS备份目录路径')
    
    # 输出选项
    parser.add_argument('-o', '--output', help='输出目录路径')
    parser.add_argument('-c', '--config', help='配置文件路径')
    
    # 模式选项
    parser.add_argument('-i', '--interactive', action='store_true', help='交互式模式')
    parser.add_argument('-d', '--discover', action='store_true', help='发现所有备份')
    parser.add_argument('--auto', action='store_true', help='自动提取最新的微信备份')
    parser.add_argument('--analyze-only', action='store_true', help='仅分析不提取')
    
    # 批量处理
    parser.add_argument('--batch', help='批量处理配置文件')
    
    # 文件类型选择
    parser.add_argument('--types', nargs='+', 
                       choices=['main', 'contacts', 'messages', 'oplog'],
                       help='指定要提取的文件类型')
    
    # 其他选项
    parser.add_argument('--check-permissions', action='store_true', help='检查系统权限')
    parser.add_argument('--version', action='version', version='WeChatExtractor 2.0.0')
    
    args = parser.parse_args()
    
    try:
        # 创建管道
        pipeline = WeChatExtractorPipeline(args.config)
        
        # 权限检查
        if args.check_permissions:
            return PermissionChecker.print_permission_status()
        
        # 交互式模式
        if args.interactive:
            return pipeline.run_interactive()
        
        # 发现模式
        if args.discover:
            return pipeline.run_discovery()
        
        # 自动模式
        if args.auto:
            return pipeline.auto_extract_latest()
        
        # 批量处理
        if args.batch:
            return pipeline.run_batch_processing(args.batch)
        
        # 单个备份处理
        if args.backup_path:
            return pipeline.run_single_extraction(
                args.backup_path, 
                args.output, 
                args.analyze_only,
                args.types
            )
        
        # 默认：尝试当前目录或显示帮助
        if os.path.exists('./Manifest.db'):
            print("✓ 在当前目录发现iOS备份")
            return pipeline.run_single_extraction('.', args.output, args.analyze_only, args.types)
        else:
            # 尝试自动模式
            print("🔍 尝试自动查找最新备份...")
            if pipeline.auto_extract_latest():
                return True
            
            print("\n❌ 未指定备份路径且未找到可用备份")
            parser.print_help()
            return False
    
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
