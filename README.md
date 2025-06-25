# 📱 微信备份提取工具

## 🎯 概述

这是一个完全可复用的微信备份提取工具，可以从任何iOS设备备份中提取微信聊天记录、联系人等重要数据。采用模块化设计，支持命令行参数、配置文件、交互式界面等多种使用方式。

## 📁 项目结构

```
WeChatAssist/
├── wechat_extractor.py              # 🚀 主执行脚本
├── quick_extract.sh                 # ⚡ 快速提取脚本
├── wechat_extractor_config.ini      # ⚙️ 配置文件模板
├── batch_config_example.json        # 📋 批量处理示例
├── src/                             # 📦 源码模块
│   ├── core/                        # 核心功能
│   │   ├── backup_analyzer.py       # 备份分析模块
│   │   ├── file_extractor.py        # 文件提取模块
│   │   └── config_manager.py        # 配置管理模块
│   ├── utils/                       # 工具模块
│   │   ├── permission_checker.py    # 权限检查模块
│   │   └── backup_discovery.py      # 备份发现模块
│   └── cli/                         # 命令行界面
│       └── interactive.py           # 交互式界面模块
└── extract_wechat_files/            # 示例提取结果目录
```

## 🔧 使用前准备

### 权限设置（重要！）

在使用工具前，请先解决权限问题：

1. **打开系统设置**：`系统设置 > 隐私与安全性 > 完全磁盘访问权限`

2. **添加终端权限**：点击 `+` 号，添加 `终端` 应用

3. **验证权限**：运行以下命令测试权限
```bash
ls "/Users/$(whoami)/Library/Application Support/MobileSync/Backup/"
```

如果看到备份文件夹列表，说明权限设置成功！

### 查找备份路径
```bash
# 自动查找所有iOS备份
find "/Users/$(whoami)/Library/Application Support/MobileSync/Backup" -name "Manifest.db" 2>/dev/null
```

## 🚀 使用方法

### 方法1: 最简单使用（推荐）
```bash
# 快速提取（自动选择最新备份）
./quick_extract.sh

# 交互式模式（推荐新手）
python3 wechat_extractor.py --interactive

# 自动提取最新的微信备份
python3 wechat_extractor.py --auto
```

### 方法2: 手动指定路径
```bash
# 指定备份路径
python3 wechat_extractor.py "备份路径"

# 指定备份路径和输出路径
python3 wechat_extractor.py "备份路径" -o "输出路径"
```

### 方法3: 高级功能
```bash
# 发现所有iOS备份
python3 wechat_extractor.py --discover

# 仅分析不提取
python3 wechat_extractor.py "备份路径" --analyze-only

# 选择性提取指定类型文件
python3 wechat_extractor.py "备份路径" --types main messages

# 批量处理多个备份
python3 wechat_extractor.py --batch batch_config.json
```

### 方法4: 权限和诊断
```bash
# 检查系统权限
python3 wechat_extractor.py --check-permissions

# 查看所有选项
python3 wechat_extractor.py --help
```

## 📋 实际使用示例

### 示例1: 交互式模式（推荐）
```bash
cd /Users/macbook/Documents/MyGit/WeChatAssist
python3 wechat_extractor.py --interactive
# 会自动引导您完成所有步骤
```

### 示例2: 自动模式
```bash
cd /Users/macbook/Documents/MyGit/WeChatAssist
python3 wechat_extractor.py --auto
# 自动提取最新的微信备份
```

### 示例3: 手动指定
```bash
cd /Users/macbook/Documents/MyGit/WeChatAssist
python3 wechat_extractor.py \
  "/Users/macbook/Library/Application Support/MobileSync/Backup/设备ID" \
  -o ~/Documents/wechat_backup_$(date +%Y%m%d)
```

### 示例4: 批量处理
```bash
# 编辑 batch_config_example.json 文件
python3 wechat_extractor.py --batch batch_config_example.json
```

## 🔧 主要特点

### ✅ 模块化设计
1. **核心模块**: 备份分析、文件提取、配置管理
2. **工具模块**: 权限检查、备份发现
3. **界面模块**: 交互式命令行界面
4. **管道式**: 主执行脚本统一调度各模块

### ✅ 完全可复用
1. **路径灵活**: 支持任意iOS备份路径
2. **输出自定义**: 可指定任意输出目录
3. **多种模式**: 交互式、自动化、批量处理
4. **错误处理**: 智能处理各种异常情况
5. **权限检查**: 自动检测和提示权限问题

### ✅ 适用场景
- 单个备份提取
- 批量处理多个备份
- 家庭成员设备备份
- 历史备份数据迁移
- 自动化脚本集成
- 定期备份提取

## 📊 输出文件说明

提取的文件都使用统一命名：
- `MM.sqlite` - 主数据库（包含主要聊天数据）
- `WCDB_Contact.sqlite` - 联系人数据库
- `WCDB_OpLog.sqlite` - 操作日志
- `message_1.sqlite` - 聊天记录1
- `message_2.sqlite` - 聊天记录2
- `message_3.sqlite` - 聊天记录3
- `message_4.sqlite` - 聊天记录4

## 💡 推荐使用方式

### 新手用户
```bash
# 推荐：交互式模式，有引导和提示
python3 wechat_extractor.py --interactive
```

### 日常使用
```bash
# 推荐：自动模式，一键提取最新备份
python3 wechat_extractor.py --auto
```

### 自动化脚本
```bash
#!/bin/bash
# 自动化备份提取脚本
cd /path/to/WeChatAssist

# 自动提取最新备份
python3 wechat_extractor.py --auto

# 或者批量处理
python3 wechat_extractor.py --batch production_batch_config.json
```

## ⚠️ 注意事项

### 1. **权限问题详解**

iOS备份文件通常需要特殊权限才能访问：

#### macOS 权限设置
- **完全磁盘访问权限**: 在 `系统设置 > 隐私与安全性 > 完全磁盘访问权限` 中添加：
  - `终端` 应用
  - `Python` 解释器（如果有）
  - 或者运行脚本的应用

#### 常见权限错误
```bash
# 如果遇到这类错误：
Permission denied: '/Users/用户名/Library/Application Support/MobileSync/Backup/...'
Operation not permitted
```

#### 解决方案
```bash
# 方法1: 使用 sudo（不推荐，但可能有效）
sudo python3 wechat_extractor.py "备份路径"

# 方法2: 修改备份文件权限
sudo chmod -R 755 "/Users/用户名/Library/Application Support/MobileSync/Backup/"

# 方法3: 复制备份到其他位置
cp -r "/Users/用户名/Library/Application Support/MobileSync/Backup/设备ID" ~/Desktop/backup_copy
python3 wechat_extractor.py ~/Desktop/backup_copy
```

### 2. **空间**: 提取的文件可能较大，确保有足够磁盘空间
### 3. **隐私**: 提取的文件包含私人信息，请妥善保管
### 4. **加密**: 某些数据库可能已加密，需要专门工具解密

## 📞 技术支持

### 常见问题排查

#### 权限问题
如果遇到权限错误，按以下步骤检查：

1. **检查备份路径权限**
```bash
# 检查目录是否存在
ls -la "/Users/$(whoami)/Library/Application Support/MobileSync/Backup/"

# 检查具体备份目录权限
ls -la "/Users/$(whoami)/Library/Application Support/MobileSync/Backup/设备ID"
```

2. **macOS 系统权限设置**
   - 打开 `系统设置 > 隐私与安全性 > 完全磁盘访问权限`
   - 点击 `+` 添加 `终端` 应用
   - 如果使用 IDE，也需要添加对应的应用

3. **临时解决方案**
```bash
# 复制备份到可访问位置
cp -r "备份路径" ~/Desktop/temp_backup
python3 wechat_extractor.py ~/Desktop/temp_backup
```

#### 其他问题检查清单
1. **备份路径是否正确**: 确认路径存在且包含 `Manifest.db` 文件
2. **输出目录是否可写**: 确认有权限在目标位置创建文件
3. **Python版本**: 推荐使用 Python 3.6+ 版本
4. **磁盘空间**: 确保有足够空间存储提取的文件

### 获取备份路径
如果不知道备份位置，可以运行：
```bash
# 查找所有 iOS 备份
find "/Users/$(whoami)/Library/Application Support/MobileSync/Backup" -name "Manifest.db" 2>/dev/null
```

## 🔍 查看更多选项

使用帮助命令查看所有可用选项：
```bash
python3 wechat_extractor.py --help
```

## 📈 版本历史

- **v1.0.0**: 由 `Claude 4` 生成
