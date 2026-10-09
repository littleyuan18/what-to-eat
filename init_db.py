"""数据库初始化 + 数据导入"""
import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'recipes.db')
DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'parsed_data.json')

# 设计 6 张表
SCHEMA = """
-- 菜谱主表（核心）
CREATE TABLE IF NOT EXISTS recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    category TEXT,
    sub_category TEXT,
    source TEXT,
    duration INTEGER,
    difficulty TEXT,
    seasons TEXT,
    scenes TEXT,
    spicy TEXT,
    avoid TEXT,
    avg_rating REAL DEFAULT 0,
    total_eaten INTEGER DEFAULT 0,
    last_eaten DATE,
    notes TEXT,
    favorite INTEGER DEFAULT 0,
    skipped INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 吃过的记录（每次吃一条）
CREATE TABLE IF NOT EXISTS eaten (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER,
    date DATE,
    meal TEXT,
    rating INTEGER,
    tips TEXT,
    mood TEXT,
    weather TEXT,
    photo_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(recipe_id) REFERENCES recipes(id)
);

-- 照片（独立表，可以挂在某次吃或某道菜上）
CREATE TABLE IF NOT EXISTS photos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER,
    eaten_id INTEGER,
    file_path TEXT NOT NULL,
    caption TEXT,
    taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(recipe_id) REFERENCES recipes(id),
    FOREIGN KEY(eaten_id) REFERENCES eaten(id)
);

-- 水果时令
CREATE TABLE IF NOT EXISTS fruits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    season TEXT
);

-- 健康相关
CREATE TABLE IF NOT EXISTS health (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT,
    item TEXT,
    detail TEXT,
    note TEXT
);

-- 餐厅外卖
CREATE TABLE IF NOT EXISTS restaurants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    price REAL,
    shop TEXT
);
"""


def init_db():
    os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data'), exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'photos'), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # 执行 schema
    for stmt in SCHEMA.split(';'):
        s = stmt.strip()
        if s:
            cur.execute(s)
    
    # 清空表（仅首次）
    for table in ['recipes', 'eaten', 'photos', 'fruits', 'health', 'restaurants']:
        cur.execute(f"DELETE FROM {table}")
    
    # 导入数据
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 1. 主菜谱
    for r in data['main_recipes']:
        cur.execute("""
            INSERT OR IGNORE INTO recipes (name, category, source)
            VALUES (?, ?, '主菜谱')
        """, (r['name'], r['category']))
    
    # 2. 小象超市半成品
    for r in data['xianovo']['半成品']:
        cur.execute("""
            INSERT OR IGNORE INTO recipes (name, sub_category, source, category)
            VALUES (?, ?, '小象超市', '半成品')
        """, (r['name'], r.get('subtype', '')))
    
    # 3. 火锅采购（保留作库存选项）
    for r in data['xianovo']['火锅采购']:
        cur.execute("""
            INSERT OR IGNORE INTO recipes (name, sub_category, source, category)
            VALUES (?, ?, '小象超市', '火锅食材')
        """, (r['name'], r.get('subtype', '')))
    
    # 4. 外卖
    for r in data['restaurants']:
        cur.execute("""
            INSERT OR IGNORE INTO recipes (name, source, category)
            VALUES (?, '外卖', '外卖')
        """, (f"{r['name']}（{r['shop']}）",))
    
    # 5. 水果时令
    for f in data['fruits']:
        cur.execute("""
            INSERT OR IGNORE INTO fruits (name, season) VALUES (?, ?)
        """, (f['name'], f['season']))
    
    # 6. 健康
    for h in data['health']:
        cur.execute("""
            INSERT OR IGNORE INTO health (category, item, detail, note)
            VALUES (?, ?, ?, ?)
        """, (h['category'], h['item'], h.get('detail', ''), h.get('note', '')))
    
    # 7. 餐厅
    for r in data['restaurants']:
        cur.execute("""
            INSERT OR IGNORE INTO restaurants (name, price, shop)
            VALUES (?, ?, ?)
        """, (r['name'], r['price'], r['shop']))
    
    conn.commit()
    
    # 统计
    cur.execute("SELECT COUNT(*) FROM recipes WHERE source='主菜谱'")
    print(f"  主菜谱：{cur.fetchone()[0]} 道")
    cur.execute("SELECT COUNT(*) FROM recipes WHERE source='小象超市'")
    print(f"  小象超市：{cur.fetchone()[0]} 项")
    cur.execute("SELECT COUNT(*) FROM recipes WHERE source='外卖'")
    print(f"  外卖：{cur.fetchone()[0]} 道")
    cur.execute("SELECT COUNT(*) FROM fruits")
    print(f"  水果时令：{cur.fetchone()[0]} 种")
    cur.execute("SELECT COUNT(*) FROM health")
    print(f"  健康相关：{cur.fetchone()[0]} 条")
    cur.execute("SELECT COUNT(*) FROM restaurants")
    print(f"  餐厅：{cur.fetchone()[0]} 家")
    
    conn.close()
    print(f"\n✅ 数据库已建：{DB_PATH}")


if __name__ == '__main__':
    init_db()
