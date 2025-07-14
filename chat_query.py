#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 微信聊天记录查询工具
交互式命令行界面，用于查询和导出特定的聊天记录
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
import argparse

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from tools.chat_analyzer import ChatAnalyzer
except ImportError:
    # 备用导入路径
    sys.path.insert(0, os.path.dirname(__file__))
    from src.tools.chat_analyzer import ChatAnalyzer


def parse_date(date_str: str) -> datetime:
    """解析日期字符串"""
    formats = [
        '%Y-%m-%d',
        '%Y-%m-%d %H:%M:%S',
        '%Y/%m/%d',
        '%Y/%m/%d %H:%M:%S',
        '%m-%d',
        '%m/%d'
    ]
    
    for fmt in formats:
        try:
            parsed = datetime.strptime(date_str, fmt)
            # 如果没有指定年份，使用当前年份
            if '%Y' not in fmt:
                parsed = parsed.replace(year=datetime.now().year)
            return parsed
        except ValueError:
            continue
    
    raise ValueError(f"无法解析日期格式: {date_str}")


def print_contacts(contacts):
    """打印联系人列表"""
    print("\n📋 可用联系人列表:")
    print("-" * 60)
    print(f"{'序号':<4} {'显示名称':<20} {'用户名':<25} {'备注':<15}")
    print("-" * 60)
    
    for i, contact in enumerate(contacts, 1):
        remark = contact.get('remark', '')[:15] if contact.get('remark') else ''
        username = contact['username'][:25]
        display_name = contact['display_name'][:20]
        
        print(f"{i:<4} {display_name:<20} {username:<25} {remark:<15}")
    
    print("-" * 60)
    print(f"总计: {len(contacts)} 个联系人")


def print_messages(messages, limit=50):
    """打印消息列表"""
    if not messages:
        print("📭 没有找到匹配的消息")
        return
    
    print(f"\n💬 找到 {len(messages)} 条消息")
    if len(messages) > limit:
        print(f"   仅显示前 {limit} 条")
        messages = messages[:limit]
    
    print("-" * 80)
    
    current_contact = None
    current_date = None
    
    for msg in messages:
        # 联系人分组
        if current_contact != msg['contact_display_name']:
            current_contact = msg['contact_display_name']
            print(f"\n👤 {current_contact}")
            print("=" * 40)
        
        # 日期分组
        if msg['datetime']:
            msg_date = msg['datetime'].strftime('%Y-%m-%d')
            if current_date != msg_date:
                current_date = msg_date
                print(f"\n📅 {msg_date}")
                print("-" * 20)
        
        # 消息内容
        if msg['direction'] == 0:
            sender = "我"
            direction = "📤"
        else:
            sender = msg['contact_display_name']
            direction = "📥"
            
        time_str = msg['datetime'].strftime('%H:%M:%S') if msg['datetime'] else "??:??:??"
        
        # 截断长消息
        message_content = str(msg['message'])[:100]  # 确保转换为字符串
        if len(str(msg['message'])) > 100:
            message_content += "..."
        
        print(f"{direction} [{time_str}] {sender}: {message_content}")
        
        # 移除特殊消息类型说明，因为只处理文字消息


def get_message_type_description(msg_type: int) -> str:
    """获取消息类型描述"""
    type_map = {
        1: "文本消息",
        3: "图片",
        34: "语音消息",
        43: "视频",
        47: "表情包",
        48: "位置信息",
        49: "链接/小程序",
        50: "视频通话",
        62: "小视频",
        10000: "系统消息"
    }
    return type_map.get(msg_type, f"未知类型({msg_type})")


def print_statistics(stats):
    """打印统计信息"""
    print("\n📊 聊天统计信息")
    print("=" * 50)
    
    print(f"📝 总消息数: {stats['total_messages']}")
    
    if stats['time_range']:
        tr = stats['time_range']
        print(f"📅 时间范围: {tr['earliest'].strftime('%Y-%m-%d')} ~ {tr['latest'].strftime('%Y-%m-%d')}")
        print(f"⏰ 时间跨度: {tr['span_days']:.1f} 天")
    
    if stats['contacts']:
        print("\n👥 联系人统计:")
        for contact, data in sorted(stats['contacts'].items(), key=lambda x: x[1]['total'], reverse=True)[:10]:
            print(f"   {contact}: {data['total']} 条 (发送:{data['sent']} 接收:{data['received']})")
    
    if stats['message_types']:
        print("\n📱 消息类型统计:")
        for msg_type, count in sorted(stats['message_types'].items(), key=lambda x: x[1], reverse=True):
            print(f"   {msg_type}: {count} 条")


def interactive_mode(analyzer):
    """简化的交互式模式 - 查询联系人 -> 选择时间段 -> 预览记录 -> 导出记录"""
    print("🎯 微信聊天记录查询工具")
    print("=" * 50)
    
    while True:
        print("\n� 开始查询聊天记录")
        print("=" * 30)
        
        # 步骤 1: 查询并选择联系人
        print("\n📋 步骤 1/4: 选择联系人")
        selected_contact = select_contact_interactive(analyzer)
        
        if not selected_contact:
            print("❌ 未选择联系人，退出查询")
            continue
        
        print(f"✅ 已选择联系人: {selected_contact['display_name']}")
        contact_filter = selected_contact['username']
        
        # 步骤 2: 选择时间段
        print("\n📅 步骤 2/4: 选择时间段")
        start_time = None
        end_time = None
        
        start_str = input("开始时间 (格式: YYYY-MM-DD 或 MM-DD, 留空表示不限): ").strip()
        if start_str:
            try:
                start_time = parse_date(start_str)
                print(f"✅ 开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            except ValueError as e:
                print(f"❌ {e}")
                continue
        
        end_str = input("结束时间 (格式同上, 留空表示不限): ").strip()
        if end_str:
            try:
                end_time = parse_date(end_str)
                if end_time.hour == 0 and end_time.minute == 0:
                    end_time = end_time.replace(hour=23, minute=59, second=59)
                print(f"✅ 结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            except ValueError as e:
                print(f"❌ {e}")
                continue
        
        # 可选: 关键字过滤
        keyword = input("关键字过滤 (留空表示不限): ").strip() or None
        if keyword:
            print(f"✅ 关键字: {keyword}")
        
        # 步骤 3: 预览记录
        print("\n👀 步骤 3/4: 预览聊天记录")
        print("🔍 正在搜索...")
        
        messages = analyzer.search_messages(
            contact_filter=contact_filter,
            start_time=start_time,
            end_time=end_time,
            keyword=keyword,
            limit=100  # 先查询100条用于预览
        )
        
        if not messages:
            print("📭 没有找到匹配的消息")
            continue
        
        # 显示预览
        print(f"\n� 找到 {len(messages)} 条消息")
        print_messages(messages, limit=20)  # 只显示前20条预览
        
        if len(messages) > 20:
            print(f"\n💡 仅显示前20条预览，实际找到 {len(messages)} 条消息")
        
        # 步骤 4: 询问是否导出
        print("\n📁 步骤 4/4: 导出记录")
        export_choice = input("是否要导出这些记录? (y/n): ").strip().lower()
        
        if export_choice == 'y':
            # 重新查询所有消息（无数量限制）
            print("🔍 正在获取完整记录...")
            all_messages = analyzer.search_messages(
                contact_filter=contact_filter,
                start_time=start_time,
                end_time=end_time,
                keyword=keyword
            )
            
            # 选择导出格式
            print("\n导出格式:")
            print("1. TXT (推荐)")
            print("2. JSON")
            print("3. CSV")
            
            format_choice = input("选择格式 (1-3): ").strip()
            format_map = {'1': 'txt', '2': 'json', '3': 'csv'}
            export_format = format_map.get(format_choice, 'txt')
            
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            contact_name = selected_contact['display_name'][:10]  # 取前10个字符
            default_name = f"wechat_{contact_name}_{timestamp}.{export_format}"
            output_file = input(f"输出文件名 (默认: {default_name}): ").strip() or default_name
            
            # 执行导出
            print("\n📁 正在导出...")
            success = analyzer.export_messages(all_messages, output_file, export_format)
            
            if success:
                print(f"✅ 导出完成: {output_file}")
                print(f"📊 共导出 {len(all_messages)} 条消息")
            else:
                print("❌ 导出失败")
        
        # 询问是否继续
        print("\n" + "=" * 50)
        continue_choice = input("是否继续查询其他联系人? (y/n): ").strip().lower()
        
        if continue_choice != 'y':
            print("👋 再见!")
            break


def search_contacts(analyzer, search_term):
    """搜索联系人"""
    contacts = analyzer.get_contact_list()
    
    if not search_term:
        return contacts
    
    search_term = search_term.lower()
    matched_contacts = []
    
    for contact in contacts:
        # 检查用户名、显示名称、备注是否包含搜索词
        if (search_term in contact['username'].lower() or 
            search_term in contact['display_name'].lower() or
            search_term in contact.get('remark', '').lower()):
            matched_contacts.append(contact)
    
    return matched_contacts


def select_contact_interactive(analyzer):
    """交互式选择联系人 - 简化版本"""
    while True:
        search_term = input("🔍 请输入联系人名称关键字: ").strip()
        
        if not search_term:
            print("❌ 请输入关键字")
            continue
            
        matched_contacts = search_contacts(analyzer, search_term)
        
        if not matched_contacts:
            print("❌ 没有找到匹配的联系人，请重试")
            continue
        
        if len(matched_contacts) == 1:
            # 如果只有一个匹配结果，直接确认
            contact = matched_contacts[0]
            print(f"✅ 找到联系人: {contact['display_name']}")
            return contact
        
        # 显示匹配结果
        print(f"\n📋 找到 {len(matched_contacts)} 个匹配的联系人:")
        print("-" * 70)
        print(f"{'序号':<4} {'显示名称':<20} {'用户名':<25} {'备注':<15}")
        print("-" * 70)
        
        for i, contact in enumerate(matched_contacts, 1):
            remark = contact.get('remark', '')[:15] if contact.get('remark') else ''
            username = contact['username'][:25]
            display_name = contact['display_name'][:20]
            
            print(f"{i:<4} {display_name:<20} {username:<25} {remark:<15}")
        
        print("-" * 70)
        
        if len(matched_contacts) > 10:
            print("💡 结果较多，建议输入更具体的关键字")
            continue
        
        # 选择联系人
        while True:
            choice = input(f"\n请选择联系人 (1-{len(matched_contacts)}, 0=重新搜索): ").strip()
            
            if choice == '0':
                break
            
            try:
                index = int(choice) - 1
                if 0 <= index < len(matched_contacts):
                    return matched_contacts[index]
                else:
                    print("❌ 无效的选择")
            except ValueError:
                print("❌ 请输入数字")
        
        # 如果选择了0，继续外层循环重新搜索
        if choice == '0':
            continue
    
    return None


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='🔍 微信聊天记录查询工具')
    parser.add_argument('extracted_dir', nargs='?', 
                       default='./extracted_wechat_files',
                       help='提取文件目录路径')
    
    # 命令行模式参数
    parser.add_argument('--contact', help='联系人过滤条件')
    parser.add_argument('--start-time', help='开始时间 (YYYY-MM-DD)')
    parser.add_argument('--end-time', help='结束时间 (YYYY-MM-DD)')
    parser.add_argument('--keyword', help='消息关键字')
    parser.add_argument('--limit', type=int, default=50, help='显示数量限制')
    parser.add_argument('--export', help='导出文件路径')
    parser.add_argument('--format', choices=['json', 'txt', 'csv'], default='json', help='导出格式')
    parser.add_argument('--stats', action='store_true', help='显示统计信息')
    parser.add_argument('--list-contacts', action='store_true', help='列出所有联系人')
    parser.add_argument('--search-contacts', help='搜索联系人（支持模糊匹配）')
    
    args = parser.parse_args()
    
    # 检查提取文件目录
    extracted_dir = Path(args.extracted_dir)
    if not extracted_dir.exists():
        print(f"❌ 提取文件目录不存在: {extracted_dir}")
        print("💡 请先运行 wechat_extractor.py 提取微信数据")
        return False
    
    # 创建分析器
    try:
        analyzer = ChatAnalyzer(str(extracted_dir))
    except Exception as e:
        print(f"❌ 初始化分析器失败: {e}")
        return False
    
    # 命令行模式
    if any([args.contact, args.start_time, args.end_time, args.keyword, 
            args.export, args.stats, args.list_contacts, args.search_contacts]):
        
        if args.list_contacts:
            contacts = analyzer.get_contact_list()
            print_contacts(contacts)
            return True
        
        if args.search_contacts:
            matched_contacts = search_contacts(analyzer, args.search_contacts)
            if matched_contacts:
                print(f"\n📋 找到 {len(matched_contacts)} 个匹配的联系人:")
                print("-" * 80)
                print(f"{'序号':<4} {'显示名称':<25} {'用户名':<30} {'备注':<20}")
                print("-" * 80)
                
                for i, contact in enumerate(matched_contacts, 1):
                    remark = contact.get('remark', '')[:20] if contact.get('remark') else ''
                    username = contact['username'][:30]
                    display_name = contact['display_name'][:25]
                    
                    print(f"{i:<4} {display_name:<25} {username:<30} {remark:<20}")
                
                print("-" * 80)
                print(f"总计: {len(matched_contacts)} 个匹配的联系人")
            else:
                print("❌ 没有找到匹配的联系人")
            return True
        
        # 解析时间参数
        start_time = None
        end_time = None
        
        if args.start_time:
            try:
                start_time = parse_date(args.start_time)
            except ValueError as e:
                print(f"❌ {e}")
                return False
        
        if args.end_time:
            try:
                end_time = parse_date(args.end_time)
                if end_time.hour == 0 and end_time.minute == 0:
                    end_time = end_time.replace(hour=23, minute=59, second=59)
            except ValueError as e:
                print(f"❌ {e}")
                return False
        
        if args.stats:
            # 显示统计信息
            stats = analyzer.get_chat_statistics(
                contact_filter=args.contact,
                start_time=start_time,
                end_time=end_time
            )
            print_statistics(stats)
            
        elif args.export:
            # 导出模式
            messages = analyzer.search_messages(
                contact_filter=args.contact,
                start_time=start_time,
                end_time=end_time,
                keyword=args.keyword
            )
            
            if messages:
                success = analyzer.export_messages(messages, args.export, args.format)
                return success
            else:
                print("📭 没有找到匹配的消息")
                return False
        
        else:
            # 查询模式
            messages = analyzer.search_messages(
                contact_filter=args.contact,
                start_time=start_time,
                end_time=end_time,
                keyword=args.keyword,
                limit=args.limit * 2
            )
            print_messages(messages, args.limit)
    
    else:
        # 交互式模式
        interactive_mode(analyzer)
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  用户取消操作")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 程序执行出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
