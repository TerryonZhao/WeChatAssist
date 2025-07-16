# 📱 WeChatAssist

## 🎯 概述

微信助手工具集包含两个核心工具：
1. **微信备份提取工具** (`wechat_extractor.py`) - 从iOS备份中提取微信数据
2. **聊天记录查询工具** (`chat_query.py`) - 根据联系人和时间段导出聊天记录

## 📁 项目结构

```
WeChatAssist/
├── wechat_extractor.py              # 🚀 备份提取工具
├── chat_query.py                    # 🔍 聊天记录查询工具
├── wechat_extractor_config.ini      # ⚙️ 配置文件
├── src/                             # 📦 源码模块
│   ├── core/                        # 核心功能
│   ├── utils/                       # 工具模块
│   ├── cli/                         # 命令行界面
│   └── tools/                       # 分析工具
└── extracted_wechat_files/          # 提取结果目录
```

---

## 🔧 第一部分：微信备份提取

### 功能说明
从iOS设备备份中提取微信数据库文件，包括：
- 主数据库 (`MM.sqlite`)
- 联系人数据库 (`WCDB_Contact.sqlite`)
- 聊天记录数据库 (`message_*.sqlite`)
- 操作日志 (`WCDB_OpLog.sqlite`)

### 使用方法

#### 1. 准备工作
```bash
# 设置系统权限：系统设置 > 隐私与安全性 > 完全磁盘访问权限
# 添加"终端"应用的权限

# 查找备份路径
find "/Users/$(whoami)/Library/Application Support/MobileSync/Backup" -name "Manifest.db" 2>/dev/null
```

#### 2. 运行提取
```bash
# 交互式模式
python3 wechat_extractor.py
```

#### 3. 输出结果
提取的文件保存在 `extracted_wechat_files/` 目录中，统一命名格式。

---

## 🔍 第二部分：聊天记录查询

### 功能说明
从已提取的微信数据库中查询和导出特定聊天记录，支持：
- 按联系人筛选
- 按时间范围筛选
- 按关键字搜索
- 自定义联系人备注
- 多种导出格式（TXT、JSON、CSV）

### 使用方法

#### 1. 确保数据已提取
```bash
# 先运行备份提取工具
python3 wechat_extractor.py
```

#### 2. 查询聊天记录
```bash
# 交互式查询（推荐）
python3 chat_query.py

# 指定提取文件目录
python3 chat_query.py ./extracted_wechat_files
```

#### 3. 操作流程
1. **选择联系人**：输入关键字搜索联系人
2. **设置时间范围**：指定开始和结束时间（可选）
3. **关键字过滤**：搜索特定内容（可选）
4. **设置备注**：自定义联系人显示名称
5. **预览记录**：查看前20条消息
6. **导出记录**：选择格式并保存到文件

### 导出格式示例

#### TXT格式
```
👤 张三（自定义备注）
==================

📅 2024-07-15
-----------
📤 [14:30:25] 我: 你好，在忙什么？
� [14:32:10] 张三: 在看书，你呢？
```

#### JSON格式
```json
[
  {
    "datetime": "2024-07-15 14:30:25",
    "direction": 0,
    "message": "你好，在忙什么？",
    "contact_display_name": "张三"
  }
]
```

---

## 💡 使用建议

### 新手用户
```bash
# 1. 先提取备份
python3 wechat_extractor.py

# 2. 再查询记录
python3 chat_query.py
```

### 日常使用
```bash
# 快速查询特定联系人最近聊天
python3 chat_query.py
# 然后按提示操作
```

## ⚠️ 注意事项

1. **权限设置**：macOS需要在"完全磁盘访问权限"中添加终端权限
2. **数据隐私**：提取和导出的文件包含私人信息，请妥善保管
3. **存储空间**：确保有足够磁盘空间存储提取的文件
4. **Python版本**：推荐使用Python 3.6+

## 🔧 故障排除

### 权限问题
```bash
# 检查备份目录权限
ls -la "/Users/$(whoami)/Library/Application Support/MobileSync/Backup/"

# 临时解决方案：复制备份到可访问位置
cp -r "备份路径" ~/Desktop/temp_backup
python3 wechat_extractor.py ~/Desktop/temp_backup
```

### 找不到数据
```bash
# 确认提取文件目录存在
ls -la ./extracted_wechat_files/

# 检查是否包含必要的数据库文件
ls -la ./extracted_wechat_files/*.sqlite
```
## 📈 版本历史

- **v1.0.0**: 由 `Claude 4` 生成
