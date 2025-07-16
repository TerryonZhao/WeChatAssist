#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 微信聊天记录查询工具
交互式命令行界面，用于查询和导出特定的聊天记录
"""

import sys
import os
from datetime import datetime
from pathlib import Path

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


def print_messages(messages, custom_remark=None, limit=50):
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
        # 联系人分组 - 使用自定义备注
        display_name = custom_remark if custom_remark else msg['contact_display_name']
        if current_contact != display_name:
            current_contact = display_name
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
            sender = custom_remark if custom_remark else msg['contact_remark']
            direction = "📥"
            
        time_str = msg['datetime'].strftime('%H:%M:%S') if msg['datetime'] else "??:??:??"
        
        # 截断长消息
        message_content = str(msg['message'])[:100]  # 确保转换为字符串
        if len(str(msg['message'])) > 100:
            message_content += "..."
        
        print(f"{direction} [{time_str}] {sender}: {message_content}")


def interactive_mode(analyzer):
    """交互式模式 - 查询联系人 -> 选择时间段 -> 输入备注 -> 预览记录 -> 导出记录"""
    print("🎯 微信聊天记录查询工具")
    print("=" * 50)
    
    while True:
        # 步骤 1: 查询并选择联系人
        print("\n📋 步骤 1/5: 选择联系人")
        selected_contact = select_contact_interactive(analyzer)
        
        if not selected_contact:
            print("❌ 未选择联系人，退出查询")
            continue
        
        print(f"✅ 已选择联系人: {selected_contact['display_name']}")
        contact_filter = selected_contact['username']
        
        # 步骤 2: 选择时间段
        print("\n📅 步骤 2/5: 选择时间段")
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
        
        # 步骤 3: 输入自定义备注
        print("\n📝 步骤 3/5: 设置联系人备注")
        default_remark = selected_contact['display_name']
        custom_remark = input(f"请输入联系人备注 (默认: {default_remark}): ").strip()
        if not custom_remark:
            custom_remark = default_remark
        print(f"✅ 联系人备注: {custom_remark}")
        
        # 步骤 4: 预览记录
        print("\n👀 步骤 4/5: 预览聊天记录")
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
        print_messages(messages, custom_remark, limit=20)  # 传递自定义备注
        
        if len(messages) > 20:
            print(f"\n💡 仅显示前20条预览，实际找到 {len(messages)} 条消息")
        
        # 步骤 5: 询问是否导出
        print("\n📁 步骤 5/5: 导出记录")
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
            contact_name = custom_remark[:10]  # 使用自定义备注
            default_name = f"wechat_{contact_name}_{timestamp}.{export_format}"
            output_file = input(f"输出文件名 (默认: {default_name}): ").strip() or default_name
            
            # 执行导出
            print("\n📁 正在导出...")
            success = analyzer.export_messages(all_messages, output_file, export_format, custom_remark)
            
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
    # 检查提取文件目录
    extracted_dir = Path('./extracted_wechat_files')
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
