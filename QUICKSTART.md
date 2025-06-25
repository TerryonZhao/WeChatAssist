# 🚀 快速开始指南

## 新手用户（推荐）

```bash
# 1. 设置权限（重要！）
# 打开：系统设置 > 隐私与安全性 > 完全磁盘访问权限
# 添加：终端应用

# 2. 使用交互式模式
python3 wechat_extractor.py --interactive
```

## 快速用户

```bash
# 自动提取最新微信备份
python3 wechat_extractor.py --auto

# 或使用快速脚本
./quick_extract.sh
```

## 高级用户

```bash
# 发现所有备份
python3 wechat_extractor.py --discover

# 批量处理
python3 wechat_extractor.py --batch batch_config.json

# 自定义提取
python3 wechat_extractor.py "备份路径" --types main messages -o "输出路径"
```

## 故障排除

```bash
# 检查权限
python3 wechat_extractor.py --check-permissions

# 查看帮助
python3 wechat_extractor.py --help
```
