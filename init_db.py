"""数据库初始化 + 数据导入（v1.0）"""
import sqlite3
import json
import os
from datetime import datetime, date, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'recipes.db')
DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'parsed_data.json')

# ============= Schema =============
SCHEMA = """
-- 菜谱主表（含主菜谱、减脂期、小象超市等）
CREATE TABLE IF NOT EXISTS recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT,
    sub_category TEXT,
    source TEXT,  -- 主菜谱 / 减脂期 / 小象超市
    note TEXT,
    UNIQUE(name, source)
);

-- 吃完记录
CREATE TABLE IF NOT EXISTS eaten (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dish_name TEXT NOT NULL,
    meal TEXT,  -- 早 / 午 / 晚
    eaten_date DATE,
    source TEXT,  -- 自做 / 外卖 / 外出 / 小象
    rating INTEGER,  -- 1-5
    tips TEXT,
    mood TEXT,
    weather TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 照片
CREATE TABLE IF NOT EXISTS photos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    eaten_id INTEGER,
    file_path TEXT NOT NULL,
    caption TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 冰箱
CREATE TABLE IF NOT EXISTS fridge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    layer INTEGER,  -- 1 / 2 / 3
    food_type TEXT,  -- 蔬菜 / 冷藏 / 冷冻
    put_date DATE,
    used INTEGER DEFAULT 0,  -- 0 在用 / 1 已用
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 肺食材
CREATE TABLE IF NOT EXISTS lung_foods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT,
    name TEXT NOT NULL
);

-- 饮料/甜点
CREATE TABLE IF NOT EXISTS drinks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner TEXT,  -- po / bo / 公用
    name TEXT NOT NULL
);

-- 餐厅
CREATE TABLE IF NOT EXISTS restaurants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    dishes TEXT,
    type TEXT  -- 外卖 / 外出
);

-- 外卖/外出额度记录
CREATE TABLE IF NOT EXISTS takeout_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_date DATE,
    meal TEXT,  -- 早 / 午 / 晚
    source TEXT,  -- 外卖 / 外出 / 小象
    dish TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 心情/场景
CREATE TABLE IF NOT EXISTS moods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT,  -- 救急 / 姨妈期 / 心情差
    UNIQUE(name, category)
);
"""


def init_db():
    """幂等初始化函数"""
    os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data'), exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'photos'), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    for stmt in SCHEMA.split(';'):
        s = stmt.strip()
        if s:
            cur.execute(s)
    conn.commit()
    
    # 检查是否需要导入数据
    count = cur.execute("SELECT COUNT(*) FROM recipes").fetchone()[0]
    if count > 0:
        conn.close()
        return
    
    # 导入数据
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 1. 主菜谱
    for r in data.get('main_recipes', []):
        cur.execute("""
            INSERT OR IGNORE INTO recipes (name, category, source, note)
            VALUES (?, ?, '主菜谱', ?)
        """, (r['name'], r['category'], r.get('note', '')))
    
    # 2. 减脂期食谱
    for r in data.get('diet_recipes', []):
        cur.execute("""
            INSERT OR IGNORE INTO recipes (name, category, source, note)
            VALUES (?, ?, '减脂期', ?)
        """, (r['name'], r['category'], r.get('note', '')))
    
    # 3. 小象超市
    for r in data.get('xiaoxiang', []):
        cur.execute("""
            INSERT OR IGNORE INTO recipes (name, sub_category, source, category)
            VALUES (?, ?, '小象超市', '半成品')
        """, (r['name'], r.get('type', '')))
    
    # 4. 肺食材
    for r in data.get('lung_foods', []):
        cur.execute("""
            INSERT OR IGNORE INTO lung_foods (type, name) VALUES (?, ?)
        """, (r['type'], r['name']))
    
    # 5. 饮料
    for r in data.get('drinks', []):
        cur.execute("""
            INSERT OR IGNORE INTO drinks (owner, name) VALUES (?, ?)
        """, (r['owner'], r['name']))
    
    # 6. 餐厅
    for r in data.get('restaurants', []):
        # 简单判断：菜名里有"饺子/海鲜/砂锅"等可能是外出，其他外卖
        is_outdoor = any(kw in r['name'] for kw in ['饺子', '海鲜', '火锅', '小馆', '面馆', '茶', '咖啡'])
        rtype = '外出' if is_outdoor else '外卖'
        cur.execute("""
            INSERT OR IGNORE INTO restaurants (name, dishes, type) VALUES (?, ?, ?)
        """, (r['name'], r['dishes'], rtype))
    
    # 7. 心情/场景（默认列表）
    default_moods = [
        ('救急', '救急'),
        ('姨妈期', '姨妈期'),
        ('心情差', '心情差'),
        ('加班', '加班'),
        ('减脂', '减脂'),
        ('招待', '招待'),
        ('雨天', '雨天'),
        ('二人食', '场景'),
    ]
    for m, cat in default_moods:
        cur.execute("INSERT OR IGNORE INTO moods (name, category) VALUES (?, ?)", (m, cat))
    
    conn.commit()
    conn.close()


def reset_data():
    """重置所有业务数据（保留 schema）—— 用于用户主动重置"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for t in ['eaten', 'photos', 'fridge', 'takeout_log']:
        cur.execute(f"DELETE FROM {t}")
    conn.commit()
    conn.close()


if __name__ == '__main__':
    init_db()
    print("✅ 数据库初始化完成")
    # 显示数据统计
    conn = sqlite3.connect(DB_PATH)
    for t in ['recipes', 'lung_foods', 'drinks', 'restaurants', 'moods']:
        n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t}: {n} 条")
    conn.close()
