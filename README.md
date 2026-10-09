# 🍱 今天吃什么 - 个人美食记忆系统

> 你的私人美食决策 + 记忆 app

## 功能
- 🎲 一键抽菜（早午晚 3 道）
- 📅 饮食日历 + 打卡
- 📝 吃完拍照 + 评分 + tips 记录
- 📊 历史统计（top 5、累计、本月）
- 📦 数据永久保存 + 一键导出

## 启动

```bash
pip install -r requirements.txt
streamlit run app.py
```

打开 http://localhost:8501

## 数据库
- `data/recipes.db` - SQLite（永久本地存储）
- `data/photos/` - 照片

## 配色
- 主紫 `#7C5FB6`（点睛用）
- 浅紫 `#EDE3F5`（背景）
- 白色 `#FFFFFF`（主背景）

## 数据来源
基于你的 Excel 菜谱（90 道主菜 + 56 个小象超市 + 67 道外卖 + 17 种时令水果）
