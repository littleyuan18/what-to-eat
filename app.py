"""
今天吃什么 - 个人美食记忆系统
Streamlit Web App v1.0

Tab 结构（5 个）：
1. 首页 - 抽菜
2. 发现 - 菜库浏览
3. 日历 - 打卡历史
4. 冰箱 - 食物库存
5. 我的 - 统计 + 设置
"""
import streamlit as st
import sqlite3
import os
import json
import random
from datetime import datetime, date, timedelta
from pathlib import Path

# ============= 路径配置 =============
HERE = Path(__file__).parent
DB_PATH = HERE / 'data' / 'recipes.db'
PHOTOS_DIR = HERE / 'data' / 'photos'

# 启动时确保目录存在
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
PHOTOS_DIR.mkdir(parents=True, exist_ok=True)

# 启动时自动初始化数据库（幂等）
import init_db
try:
    init_db.init_db()
except Exception as _e:
    import traceback
    print(f"[init_db] warning: {_e}")
    traceback.print_exc()

# ============= 配色（紫色点睛） =============
PURPLE = '#7C5FB6'
PURPLE_DARK = '#5A3D8F'
PURPLE_LIGHT = '#EDE3F5'
PURPLE_BG = '#F8F4FC'
GRAY_BG = '#FAFAFA'
GRAY_TEXT = '#6B6B6B'
GRAY_LINE = '#EEEEEE'
RED = '#E53935'
GREEN = '#16A34A'
ORANGE = '#EA580C'

# ============= CSS 样式 =============
CSS = f"""
<style>
/* 全局 */
.stApp {{ background: {GRAY_BG}; }}

/* 隐藏默认元素 */
#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}
header {{visibility: hidden;}}
[data-testid="stToolbar"] {{visibility: hidden;}}
[data-testid="stDecoration"] {{visibility: hidden;}}

/* 侧边栏 */
[data-testid="stSidebar"] {{
    background: white;
    border-right: 1px solid {GRAY_LINE};
}}

/* 主标题 */
h1, h2, h3 {{ color: #1A1A1A; font-weight: 600; }}
h2 {{ font-size: 1.4rem !important; }}
h3 {{ font-size: 1.1rem !important; }}

/* 紫色主按钮 */
.stButton > button {{
    border-radius: 20px;
    border: 1px solid {GRAY_LINE};
    background: white;
    color: #1A1A1A;
    transition: all 0.2s;
    padding: 0.5rem 1rem;
}}
.stButton > button:hover {{
    border-color: {PURPLE};
    color: {PURPLE};
    transform: translateY(-1px);
}}
.stButton > button:focus {{
    border-color: {PURPLE};
    color: {PURPLE};
    box-shadow: 0 0 0 1px {PURPLE_LIGHT};
}}

/* 紫色大按钮 (primary) */
button[kind="primary"] {{
    background: {PURPLE} !important;
    color: white !important;
    border: none !important;
    border-radius: 24px !important;
    font-weight: 600 !important;
    padding: 0.75rem 1.5rem !important;
    box-shadow: 0 4px 12px {PURPLE_LIGHT} !important;
}}
button[kind="primary"]:hover {{
    background: {PURPLE_DARK} !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 16px {PURPLE_LIGHT} !important;
}}

/* 卡片 */
.recipe-card {{
    background: white;
    border-radius: 16px;
    padding: 16px;
    margin: 8px 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    border: 1px solid {GRAY_LINE};
}}
.recipe-card-big {{
    background: white;
    border-radius: 20px;
    padding: 20px;
    margin: 12px 0;
    box-shadow: 0 4px 16px rgba(124, 95, 182, 0.08);
    border: 1px solid {PURPLE_LIGHT};
}}

/* chip 标签 */
.chip {{
    display: inline-block;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 12px;
    margin-right: 6px;
    background: {GRAY_BG};
    color: {GRAY_TEXT};
    border: 1px solid {GRAY_LINE};
}}
.chip-purple {{
    background: {PURPLE_LIGHT};
    color: {PURPLE_DARK};
    border-color: {PURPLE_LIGHT};
}}
.chip-red {{
    background: #FEE2E2;
    color: {RED};
    border-color: #FEE2E2;
}}
.chip-green {{
    background: #DCFCE7;
    color: {GREEN};
    border-color: #DCFCE7;
}}
.chip-orange {{
    background: #FED7AA;
    color: {ORANGE};
    border-color: #FED7AA;
}}

/* 小贴士 */
.tip {{
    background: {PURPLE_BG};
    border-left: 3px solid {PURPLE};
    padding: 10px 14px;
    border-radius: 6px;
    margin: 8px 0;
    color: #1A1A1A;
    font-size: 13px;
}}

/* 警告 */
.warning {{
    background: #FEF3C7;
    border-left: 3px solid {ORANGE};
    padding: 10px 14px;
    border-radius: 6px;
    margin: 8px 0;
    color: #92400E;
    font-size: 13px;
}}

/* 紧急 */
.urgent {{
    background: #FEE2E2;
    border-left: 3px solid {RED};
    padding: 10px 14px;
    border-radius: 6px;
    margin: 8px 0;
    color: #991B1B;
    font-size: 13px;
}}

/* 隐藏滚动条 */
::-webkit-scrollbar {{ width: 0; }}
</style>
"""


# ============= 数据库工具 =============
def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def query(sql, params=()):
    conn = get_db()
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return rows


def query_one(sql, params=()):
    conn = get_db()
    row = conn.execute(sql, params).fetchone()
    conn.close()
    return row


def execute(sql, params=()):
    conn = get_db()
    cur = conn.execute(sql, params)
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return last_id


# ============= 工具函数 =============
def get_current_season():
    m = datetime.now().month
    if m in (3, 4, 5): return '春'
    if m in (6, 7, 8): return '夏'
    if m in (9, 10, 11): return '秋'
    return '冬'


def is_workday(d=None):
    d = d or date.today()
    return d.weekday() < 5  # 0-4 = 周一到周五


def get_week_range(d=None):
    """本周一 → 周日"""
    d = d or date.today()
    start = d - timedelta(days=d.weekday())
    end = start + timedelta(days=6)
    return start, end


def get_today_zh():
    """今天中文周几"""
    days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    return days[date.today().weekday()]


# ============= 推荐算法 =============
def recommend_self_cook(meal='早'):
    """自己做的早+午同款：肉/海鲜 + 素菜 + 主食"""
    main = query("SELECT name FROM recipes WHERE source='主菜谱' AND category='肉' ORDER BY RANDOM() LIMIT 1")
    seafood = query("SELECT name FROM recipes WHERE source='主菜谱' AND category='海鲜' ORDER BY RANDOM() LIMIT 1")
    veg = query("SELECT name FROM recipes WHERE source='主菜谱' AND category='素菜' ORDER BY RANDOM() LIMIT 1")
    staple = query("SELECT name FROM recipes WHERE source='主菜谱' AND category='主食' ORDER BY RANDOM() LIMIT 1")
    
    # 肉或海鲜 二选一
    meat_or_seafood = main[0]['name'] if random.random() > 0.5 and main else (seafood[0]['name'] if seafood else '未知')
    
    dishes = []
    if meat_or_seafood:
        dishes.append({'name': meat_or_seafood, 'cat': '肉/海鲜'})
    if veg:
        dishes.append({'name': veg[0]['name'], 'cat': '素菜'})
    if staple:
        dishes.append({'name': staple[0]['name'], 'cat': '主食'})
    
    return dishes


def recommend_diet_dinner():
    """减脂期晚餐：肉/海鲜 + 素菜 + 主食"""
    return recommend_self_cook()  # 同结构，从 减脂期 拉
    # 实际上重写：需要从 减脂期 拉
    # 但这里简化用主菜谱（实际实现见下）


def recommend_takeout(source='外卖'):
    """外卖 / 外出"""
    rows = query("SELECT name, dishes FROM restaurants WHERE type=? ORDER BY RANDOM() LIMIT 3", (source,))
    return [{'name': r['name'], 'dishes': r['dishes'] or '推荐菜'} for r in rows]


def recommend_xiaoxiang():
    """小象半成品"""
    rows = query("SELECT name, sub_category FROM recipes WHERE source='小象超市' ORDER BY RANDOM() LIMIT 3")
    return [{'name': r['name'], 'cat': r['sub_category'] or '半成品'} for r in rows]


# ============= 额度检查 =============
WEEKLY_TAKEOUT_LIMIT = 4  # 一周 4 顿

def get_takeout_count_this_week():
    """本周已用外卖/外出次数"""
    start, end = get_week_range()
    return query_one(
        "SELECT COUNT(*) as cnt FROM takeout_log WHERE log_date BETWEEN ? AND ?",
        (start.isoformat(), end.isoformat())
    )['cnt']


def get_takeout_remaining():
    """本周还剩几次"""
    used = get_takeout_count_this_week()
    return max(0, WEEKLY_TAKEOUT_LIMIT - used)


# ============= 冰箱 =============
FOOD_EXPIRY = {
    '蔬菜': 2,    # 2 天
    '冷藏': 2,    # 2 天
    '冷冻': 90,   # 3 个月
}

def get_fridge_items():
    """冰箱所有食物，按到期排序"""
    rows = query("SELECT * FROM fridge WHERE used=0 ORDER BY put_date ASC")
    items = []
    today = date.today()
    for r in rows:
        put = datetime.strptime(r['put_date'], '%Y-%m-%d').date() if r['put_date'] else today
        days_valid = FOOD_EXPIRY.get(r['food_type'], 7)
        days_left = days_valid - (today - put).days
        items.append({
            **dict(r),
            'put_date': r['put_date'],
            'days_valid': days_valid,
            'days_left': days_left,
            'expired': days_left < 0,
        })
    # 排序：到期 < 0 排最前，然后按 days_left 升序
    items.sort(key=lambda x: (not x['expired'], x['days_left']))
    return items


def get_expiring_items():
    """即将到期的食物（提前 1 天 / 2 周）"""
    items = get_fridge_items()
    expiring = []
    for it in items:
        if it['days_left'] < 0:
            expiring.append((it, 'urgent', f"已过期 {-it['days_left']} 天"))
        elif it['food_type'] == '冷冻' and it['days_left'] <= 14:
            expiring.append((it, 'warn', f"还剩 {it['days_left']} 天到期"))
        elif it['days_left'] <= 1:
            expiring.append((it, 'warn', f"还剩 {it['days_left']} 天到期"))
    return expiring


# ============= 页面渲染 =============
def render_sidebar():
    """侧边栏：5 Tab 导航"""
    if 'page' not in st.session_state:
        st.session_state.page = '首页'
    
    page = st.session_state.page
    
    with st.sidebar:
        st.markdown(f"### 🍱 今天吃什么")
        st.markdown(f"<div style='color:{GRAY_TEXT};font-size:12px;margin-bottom:20px;'>{date.today().isoformat()} · {get_today_zh()}</div>", unsafe_allow_html=True)
        
        tabs = [
            ('🍱', '首页', '抽菜'),
            ('🔍', '发现', '菜库'),
            ('📅', '日历', '历史'),
            ('🧊', '冰箱', '库存'),
            ('👤', '我的', '统计'),
        ]
        for emoji, name, sub in tabs:
            is_active = (page == name)
            btn_label = f"{emoji}  {name}" + (f" · {sub}" if not is_active else "")
            if st.button(btn_label, key=f"nav_{name}", use_container_width=True, type="primary" if is_active else "secondary"):
                st.session_state.page = name
                st.rerun()
        
        st.markdown("---")
        st.markdown(f"<div style='color:{GRAY_TEXT};font-size:11px;'>v1.0 · 紫色点睛</div>", unsafe_allow_html=True)
    
    return page


# ============= 首页 =============
def render_today():
    """首页：抽菜"""
    st.markdown(f"## 🍱 今天吃什么")
    st.markdown(f"<div style='color:{GRAY_TEXT};font-size:14px;margin-bottom:16px;'>{date.today().isoformat()} · {get_today_zh()}</div>", unsafe_allow_html=True)
    
    # === 顶部 banner: 外卖额度 ===
    remaining = get_takeout_remaining()
    used = get_takeout_count_this_week()
    if remaining == 0:
        st.markdown(f"""<div class="urgent">⚠️ 本周外卖/外出已用完（{used}/{WEEKLY_TAKEOUT_LIMIT}），建议自己做</div>""", unsafe_allow_html=True)
    elif remaining == 1:
        st.markdown(f"""<div class="warning">⚠️ 本周还剩 {remaining} 次外卖/外出额度（{used}/{WEEKLY_TAKEOUT_LIMIT}）</div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""<div class="tip">📊 本周外卖/外出：{used}/{WEEKLY_TAKEOUT_LIMIT}（还剩 {remaining} 次）</div>""", unsafe_allow_html=True)
    
    # === 冰箱到期提醒 ===
    expiring = get_expiring_items()
    if expiring:
        items_text = ", ".join([f"{it['name']}({msg})" for it, _, msg in expiring[:3]])
        st.markdown(f"""<div class="warning">🧊 冰箱提醒：{items_text}</div>""", unsafe_allow_html=True)
    
    # === 品类选择 ===
    st.markdown("### 🎯 选品类")
    if 'category' not in st.session_state:
        st.session_state.category = '自己做'
    
    cats = [
        ('🍳', '自己做'),
        ('🥡', '外卖'),
        ('🛒', '小象半成品'),
        ('🍽️', '外出'),
    ]
    cols = st.columns(4)
    for i, (emoji, name) in enumerate(cats):
        with cols[i]:
            is_active = (st.session_state.category == name)
            if st.button(f"{emoji} {name}", key=f"cat_{name}", use_container_width=True, type="primary" if is_active else "secondary"):
                st.session_state.category = name
                st.rerun()
    
    # === 心情/场景选择 ===
    st.markdown("### 💭 心情/场景（多选）")
    moods_data = query("SELECT name, category FROM moods ORDER BY id")
    if 'moods_selected' not in st.session_state:
        st.session_state.moods_selected = []
    
    mood_chips = " ".join([f"<span class='chip'>{m['name']}</span>" for m in moods_data])
    st.markdown(mood_chips, unsafe_allow_html=True)
    
    cols = st.columns(min(4, len(moods_data)))
    for i, m in enumerate(moods_data):
        with cols[i % 4]:
            is_active = m['name'] in st.session_state.moods_selected
            if st.button(m['name'], key=f"mood_{m['name']}", use_container_width=True, type="primary" if is_active else "secondary"):
                if is_active:
                    st.session_state.moods_selected.remove(m['name'])
                else:
                    st.session_state.moods_selected.append(m['name'])
                st.rerun()
    
    st.markdown("---")
    
    # === 抽菜按钮 ===
    st.markdown("### 🎲 抽菜")
    if st.button("✨ 抽！✨", use_container_width=True, type="primary"):
        st.session_state.pick_result = do_pick(st.session_state.category, st.session_state.moods_selected)
    
    # === 抽菜结果 ===
    if 'pick_result' in st.session_state and st.session_state.pick_result:
        result = st.session_state.pick_result
        st.markdown("### 🍽️ 今日菜谱")
        
        if result['type'] == '自己做':
            st.markdown("**早 + 午（同款）+ 晚（减脂期）+ 梨汤**")
            
            # 早+午 同款
            st.markdown("#### 🌅 早 + 午（同款）")
            for d in result['lunch_pair']:
                st.markdown(f"""
                <div class="recipe-card-big">
                    <div style="font-size:16px;font-weight:600;">{d['name']}</div>
                    <div style="margin-top:6px;"><span class="chip chip-purple">{d['cat']}</span></div>
                </div>
                """, unsafe_allow_html=True)
            
            # 晚餐
            st.markdown("#### 🌙 晚（减脂期）")
            for d in result['dinner']:
                st.markdown(f"""
                <div class="recipe-card-big">
                    <div style="font-size:16px;font-weight:600;">{d['name']}</div>
                    <div style="margin-top:6px;"><span class="chip chip-orange">{d['cat']} · 减脂期</span></div>
                </div>
                """, unsafe_allow_html=True)
            
            # 梨汤
            if result.get('pear_soup'):
                st.markdown("#### 🍐 梨汤（工作日午餐）")
                st.markdown(f"""
                <div class="recipe-card-big">
                    <div style="font-size:16px;font-weight:600;">{result['pear_soup']}</div>
                    <div style="margin-top:6px;"><span class="chip chip-green">润肺 · 每天</span></div>
                </div>
                """, unsafe_allow_html=True)
        
        elif result['type'] in ('外卖', '外出', '小象半成品'):
            st.markdown(f"#### 🍴 {result['type']}推荐")
            for d in result['items']:
                st.markdown(f"""
                <div class="recipe-card-big">
                    <div style="font-size:16px;font-weight:600;">{d['name']}</div>
                    <div style="color:{GRAY_TEXT};font-size:13px;margin-top:4px;">{d.get('dishes', d.get('cat', ''))}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # 记录按钮
            if st.button("📝 记录我选了这个", key="record_takeout", type="primary"):
                execute(
                    "INSERT INTO takeout_log (log_date, meal, source, dish) VALUES (?, ?, ?, ?)",
                    (date.today().isoformat(), '午', result['type'], result['items'][0]['name'] if result['items'] else '')
                )
                st.success("✅ 已记录！本周额度 -1")
                st.rerun()


def do_pick(category, moods):
    """执行抽菜逻辑"""
    if category == '自己做':
        # 早+午 同款（从主菜谱）
        lunch_pair = recommend_self_cook('午')
        # 晚 减脂期
        diet = query("SELECT name FROM recipes WHERE source='减脂期' AND category IN ('肉', '海鲜') ORDER BY RANDOM() LIMIT 1")
        diet_veg = query("SELECT name FROM recipes WHERE source='减脂期' AND category='素菜' ORDER BY RANDOM() LIMIT 1")
        diet_staple = query("SELECT name FROM recipes WHERE source='减脂期' AND category='主食' ORDER BY RANDOM() LIMIT 1")
        dinner = []
        if diet: dinner.append({'name': diet[0]['name'], 'cat': '肉/海鲜'})
        if diet_veg: dinner.append({'name': diet_veg[0]['name'], 'cat': '素菜'})
        if diet_staple: dinner.append({'name': diet_staple[0]['name'], 'cat': '主食'})
        
        # 梨汤（工作日午餐）
        pear_soup = None
        if is_workday():
            pear_rows = query("SELECT name FROM lung_foods WHERE type='梨汤' ORDER BY RANDOM() LIMIT 1")
            if pear_rows:
                pear_soup = pear_rows[0]['name']
        
        return {
            'type': '自己做',
            'lunch_pair': lunch_pair,
            'dinner': dinner,
            'pear_soup': pear_soup,
        }
    elif category == '外卖':
        items = recommend_takeout('外卖')
        return {'type': '外卖', 'items': items}
    elif category == '外出':
        items = recommend_takeout('外出')
        return {'type': '外出', 'items': items}
    elif category == '小象半成品':
        items = recommend_xiaoxiang()
        return {'type': '小象半成品', 'items': items}
    return None


# ============= 发现 =============
def render_discover():
    """发现：菜库浏览"""
    st.markdown("## 🔍 发现")
    
    # 分类筛选
    if 'filter_cat' not in st.session_state:
        st.session_state.filter_cat = '全部'
    
    cats = ['全部', '肉', '海鲜', '素菜', '主食', '汤']
    cols = st.columns(len(cats))
    for i, c in enumerate(cats):
        with cols[i]:
            is_active = (st.session_state.filter_cat == c)
            if st.button(c, key=f"filter_{c}", use_container_width=True, type="primary" if is_active else "secondary"):
                st.session_state.filter_cat = c
                st.rerun()
    
    # 搜索
    search = st.text_input("🔍 搜索菜名", "")
    
    # 查询
    if st.session_state.filter_cat == '全部':
        sql = "SELECT * FROM recipes WHERE source IN ('主菜谱', '减脂期')"
    else:
        sql = f"SELECT * FROM recipes WHERE source IN ('主菜谱', '减脂期') AND category=?"
    
    if search:
        sql += " AND name LIKE ?"
        rows = query(sql + " ORDER BY source, name", (f"%{search}%",) if st.session_state.filter_cat == '全部' else (st.session_state.filter_cat, f"%{search}%"))
    else:
        rows = query(sql + " ORDER BY source, name", ())
    
    st.markdown(f"### 找到 {len(rows)} 道菜")
    
    # 网格展示
    cols = st.columns(2)
    for i, r in enumerate(rows):
        with cols[i % 2]:
            st.markdown(f"""
            <div class="recipe-card">
                <div style="font-size:15px;font-weight:600;">{r['name']}</div>
                <div style="margin-top:6px;">
                    <span class="chip chip-purple">{r['category']}</span>
                    <span class="chip">{r['source']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)


# ============= 日历 =============
def render_calendar():
    """日历：历史打卡"""
    st.markdown("## 📅 日历")
    
    # 本月范围
    today = date.today()
    first_day = today.replace(day=1)
    if first_day.month == 12:
        next_month = first_day.replace(year=first_day.year + 1, month=1)
    else:
        next_month = first_day.replace(month=first_day.month + 1)
    last_day = next_month - timedelta(days=1)
    
    # 本月 eaten 记录
    rows = query(
        "SELECT * FROM eaten WHERE eaten_date BETWEEN ? AND ? ORDER BY eaten_date DESC",
        (first_day.isoformat(), last_day.isoformat())
    )
    eaten_by_date = {}
    for r in rows:
        d = r['eaten_date']
        if d not in eaten_by_date:
            eaten_by_date[d] = []
        eaten_by_date[d].append(dict(r))
    
    st.markdown(f"### {first_day.year} 年 {first_day.month} 月")
    st.markdown(f"本月共记录 {len(rows)} 餐")
    
    # 显示本月所有吃的
    if rows:
        for r in rows[:30]:
            rating = '⭐' * r['rating'] if r['rating'] else '未评'
            st.markdown(f"""
            <div class="recipe-card">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <div style="font-size:15px;font-weight:600;">{r['dish_name']}</div>
                        <div style="margin-top:4px;">
                            <span class="chip">{r['meal']}</span>
                            <span class="chip chip-purple">{r['source'] or '自己'}</span>
                            <span class="chip">{rating}</span>
                        </div>
                        {f'<div style="color:{GRAY_TEXT};font-size:12px;margin-top:4px;">{r["tips"]}</div>' if r['tips'] else ''}
                    </div>
                    <div style="color:{GRAY_TEXT};font-size:12px;">{r['eaten_date']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(f"""<div class="tip">📝 本月还没记录。<br>从首页点 "记录我选了这个" 就能记到日历。</div>""", unsafe_allow_html=True)
    
    # 快速记录按钮
    st.markdown("---")
    st.markdown("### ➕ 快速记录")
    with st.form("quick_log"):
        dish = st.text_input("菜名")
        meal = st.selectbox("餐次", ['早', '午', '晚'])
        rating = st.slider("评分", 1, 5, 4)
        tips = st.text_area("小贴士/感想（可选）")
        if st.form_submit_button("保存", type="primary"):
            if dish:
                execute(
                    "INSERT INTO eaten (dish_name, meal, eaten_date, source, rating, tips) VALUES (?, ?, ?, ?, ?, ?)",
                    (dish, meal, date.today().isoformat(), '自做', rating, tips)
                )
                st.success(f"✅ 已记录：{dish}")
                st.rerun()


# ============= 冰箱 =============
def render_fridge():
    """冰箱：3 层 + 详细表格"""
    st.markdown("## 🧊 冰箱")
    
    # 层选择
    if 'fridge_layer' not in st.session_state:
        st.session_state.fridge_layer = 1
    
    cols = st.columns(3)
    for i in range(1, 4):
        with cols[i-1]:
            is_active = (st.session_state.fridge_layer == i)
            if st.button(f"第 {i} 层", key=f"layer_{i}", use_container_width=True, type="primary" if is_active else "secondary"):
                st.session_state.fridge_layer = i
                st.rerun()
    
    # 添加新食物
    with st.expander("➕ 添加新食物", expanded=False):
        with st.form("add_food"):
            name = st.text_input("食物名称")
            food_type = st.selectbox("类型（决定保质期）", ['蔬菜', '冷藏', '冷冻'])
            put_date = st.date_input("放入日期", value=date.today())
            if st.form_submit_button("加入冰箱", type="primary"):
                if name:
                    execute(
                        "INSERT INTO fridge (name, layer, food_type, put_date) VALUES (?, ?, ?, ?)",
                        (name, st.session_state.fridge_layer, food_type, put_date.isoformat())
                    )
                    st.success(f"✅ {name} 已加入第 {st.session_state.fridge_layer} 层")
                    st.rerun()
    
    st.markdown("---")
    
    # 显示当前层
    layer = st.session_state.fridge_layer
    items = [it for it in get_fridge_items() if it['layer'] == layer]
    
    st.markdown(f"### 第 {layer} 层（{len(items)} 件）")
    
    if not items:
        st.markdown(f"""<div class="tip">📦 第 {layer} 层还是空的<br>点上面"➕ 添加新食物"加入</div>""", unsafe_allow_html=True)
        return
    
    # 详细表格（按到期排序）
    for it in items:
        if it['expired']:
            stype_class = 'urgent'
            status = f"❌ 已过期 {-it['days_left']} 天"
            chip = 'chip-red'
        elif it['days_left'] <= 1:
            stype_class = 'warning'
            status = f"⚠️ 明天到期"
            chip = 'chip-orange'
        elif it['days_left'] <= 14 and it['food_type'] == '冷冻':
            stype_class = 'warning'
            status = f"⚠️ 还剩 {it['days_left']} 天"
            chip = 'chip-orange'
        else:
            stype_class = 'recipe-card'
            status = f"✅ 还剩 {it['days_left']} 天"
            chip = 'chip-green'
        
        st.markdown(f"""
        <div class="{stype_class}">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <div style="font-size:15px;font-weight:600;">{it['name']}</div>
                    <div style="margin-top:4px;">
                        <span class="chip {chip}">{it['food_type']}</span>
                        <span class="chip">放入: {it['put_date']}</span>
                        <span class="chip">保质期: {it['days_valid']} 天</span>
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:14px;font-weight:600;">{status}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 标记已用按钮
        if st.button(f"✅ 用掉了：{it['name']}", key=f"used_{it['id']}"):
            execute("UPDATE fridge SET used=1 WHERE id=?", (it['id'],))
            st.rerun()


# ============= 我的 =============
def render_profile():
    """我的：统计 + 设置"""
    st.markdown("## 👤 我的")
    
    # 统计
    total_eaten = query_one("SELECT COUNT(*) as cnt FROM eaten")['cnt']
    month_eaten = query_one(
        "SELECT COUNT(*) as cnt FROM eaten WHERE eaten_date >= ?",
        (date.today().replace(day=1).isoformat(),)
    )['cnt']
    week_takeout = get_takeout_count_this_week()
    fridge_total = query_one("SELECT COUNT(*) as cnt FROM fridge WHERE used=0")['cnt']
    
    cols = st.columns(2)
    with cols[0]:
        st.markdown(f"""
        <div class="recipe-card-big">
            <div style="color:{GRAY_TEXT};font-size:12px;">累计记录</div>
            <div style="font-size:32px;font-weight:700;color:{PURPLE};">{total_eaten}</div>
            <div style="color:{GRAY_TEXT};font-size:12px;">餐</div>
        </div>
        """, unsafe_allow_html=True)
    with cols[1]:
        st.markdown(f"""
        <div class="recipe-card-big">
            <div style="color:{GRAY_TEXT};font-size:12px;">本月记录</div>
            <div style="font-size:32px;font-weight:700;color:{PURPLE};">{month_eaten}</div>
            <div style="color:{GRAY_TEXT};font-size:12px;">餐</div>
        </div>
        """, unsafe_allow_html=True)
    with cols[0]:
        st.markdown(f"""
        <div class="recipe-card-big">
            <div style="color:{GRAY_TEXT};font-size:12px;">本周外卖/外出</div>
            <div style="font-size:32px;font-weight:700;color:{ORANGE};">{week_takeout}/{WEEKLY_TAKEOUT_LIMIT}</div>
            <div style="color:{GRAY_TEXT};font-size:12px;">还剩 {WEEKLY_TAKEOUT_LIMIT - week_takeout}</div>
        </div>
        """, unsafe_allow_html=True)
    with cols[1]:
        st.markdown(f"""
        <div class="recipe-card-big">
            <div style="color:{GRAY_TEXT};font-size:12px;">冰箱库存</div>
            <div style="font-size:32px;font-weight:700;color:{GREEN};">{fridge_total}</div>
            <div style="color:{GRAY_TEXT};font-size:12px;">件</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Top 5
    st.markdown("### 🏆 评分 Top 5")
    top = query("SELECT dish_name, AVG(rating) as avg_r, COUNT(*) as cnt FROM eaten WHERE rating IS NOT NULL GROUP BY dish_name ORDER BY avg_r DESC, cnt DESC LIMIT 5")
    if top:
        for i, r in enumerate(top, 1):
            stars = '⭐' * int(r['avg_r'])
            st.markdown(f"{i}. **{r['dish_name']}** {stars} ({r['cnt']} 次)")
    else:
        st.markdown(f"""<div class="tip">还没有评分数据</div>""", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 数据导出
    st.markdown("### 📤 数据导出")
    if st.button("⬇️ 导出全部数据 (JSON)", use_container_width=True):
        all_data = {
            'exported_at': datetime.now().isoformat(),
            'recipes': [dict(r) for r in query("SELECT * FROM recipes")],
            'eaten': [dict(r) for r in query("SELECT * FROM eaten")],
            'fridge': [dict(r) for r in query("SELECT * FROM fridge")],
            'takeout_log': [dict(r) for r in query("SELECT * FROM takeout_log")],
        }
        fname = f"recipes_{date.today().isoformat()}.json"
        with open(fname, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2, default=str)
        with open(fname, 'r', encoding='utf-8') as f:
            st.download_button("⬇️ 下载", f.read(), file_name=fname, mime="application/json")
        os.remove(fname)
    
    # 重置数据
    st.markdown("### ⚠️ 危险操作")
    with st.expander("🗑️ 重置所有数据（清空历史/冰箱/记录）"):
        st.warning("此操作不可逆！所有吃的记录、冰箱库存、评分都会清空，但菜谱库保留。")
        if st.button("确认重置", type="primary"):
            for t in ['eaten', 'photos', 'fridge', 'takeout_log']:
                execute(f"DELETE FROM {t}")
            st.success("✅ 数据已重置")
            st.rerun()


# ============= 主入口 =============
def main():
    st.set_page_config(
        page_title="今天吃什么",
        page_icon="🍱",
        layout="centered",
        initial_sidebar_state="collapsed",
    )
    
    # 隐藏 Streamlit 默认元素
    hide_streamlit_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        [data-testid="stToolbar"] {visibility: hidden;}
        [data-testid="stDecoration"] {visibility: hidden;}
        </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)
    st.markdown(CSS, unsafe_allow_html=True)
    
    page = render_sidebar()
    
    if page == "首页":
        render_today()
    elif page == "发现":
        render_discover()
    elif page == "日历":
        render_calendar()
    elif page == "冰箱":
        render_fridge()
    elif page == "我的":
        render_profile()


if __name__ == '__main__':
    main()
