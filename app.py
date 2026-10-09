"""
今天吃什么 - 个人美食记忆系统
Streamlit Web App MVP
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

# ============= 配色（紫色点睛） =============
PURPLE = '#7C5FB6'
PURPLE_DARK = '#5A3D8F'
PURPLE_LIGHT = '#EDE3F5'
PURPLE_BG = '#F8F4FC'
GRAY_BG = '#FAFAFA'
GRAY_TEXT = '#6B6B6B'
GRAY_LINE = '#EEEEEE'
RED = '#E53935'

# ============= CSS 样式 =============
CSS = f"""
<style>
/* 全局 */
.stApp {{ background: {GRAY_BG}; }}

/* 隐藏默认元素 */
#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}

/* 侧边栏 */
[data-testid="stSidebar"] {{
    background: white;
    border-right: 1px solid {GRAY_LINE};
}}

/* 主标题区 */
h1 {{ color: #1A1A1A; font-weight: 600; }}
h2 {{ color: #1A1A1A; font-weight: 500; }}
h3 {{ color: #1A1A1A; font-weight: 500; }}

/* 紫色点睛按钮 */
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
}}

/* Primary 按钮（紫色） */
.stButton > button[kind="primary"] {{
    background: {PURPLE};
    color: white;
    border: none;
}}
.stButton > button[kind="primary"]:hover {{
    background: {PURPLE_DARK};
    color: white;
}}

/* 卡片 */
.recipe-card {{
    background: white;
    border-radius: 16px;
    padding: 20px;
    margin: 12px 0;
    border: 1px solid {GRAY_LINE};
    transition: all 0.2s;
}}
.recipe-card:hover {{
    border-color: {PURPLE};
    box-shadow: 0 2px 12px rgba(124, 95, 182, 0.08);
}}

/* 数据 banner */
.stat-banner {{
    background: {PURPLE_BG};
    border-radius: 16px;
    padding: 16px 20px;
    margin: 12px 0;
}}
.stat-num {{
    color: {PURPLE};
    font-size: 24px;
    font-weight: 600;
}}
.stat-label {{
    color: {GRAY_TEXT};
    font-size: 13px;
}}

/* 标签 chip */
.chip {{
    display: inline-block;
    padding: 4px 12px;
    background: {PURPLE_LIGHT};
    color: {PURPLE_DARK};
    border-radius: 12px;
    font-size: 12px;
    margin: 2px 4px;
}}
.chip-gray {{
    display: inline-block;
    padding: 4px 12px;
    background: #F0F0F0;
    color: {GRAY_TEXT};
    border-radius: 12px;
    font-size: 12px;
    margin: 2px 4px;
}}

/* 评分 */
.rating {{
    color: {PURPLE};
    font-size: 18px;
    letter-spacing: 2px;
}}

/* Tab */
.stTabs [data-baseweb="tab-list"] {{
    gap: 8px;
    background: transparent;
}}
.stTabs [data-baseweb="tab"] {{
    background: white;
    border-radius: 16px;
    padding: 8px 16px;
    border: 1px solid {GRAY_LINE};
}}
.stTabs [aria-selected="true"] {{
    background: {PURPLE} !important;
    color: white !important;
    border-color: {PURPLE} !important;
}}

/* 输入框 */
.stTextInput input, .stTextArea textarea, .stSelectbox div {{
    border-radius: 12px !important;
}}

/* 空状态 */
.empty-state {{
    text-align: center;
    padding: 60px 20px;
    color: {GRAY_TEXT};
}}
.empty-state .emoji {{
    font-size: 48px;
    margin-bottom: 12px;
}}

/* 圆角大按钮 */
.big-button {{
    background: {PURPLE};
    color: white;
    border-radius: 24px;
    padding: 16px 32px;
    font-size: 18px;
    font-weight: 500;
    text-align: center;
    cursor: pointer;
    border: none;
    width: 100%;
    margin: 12px 0;
}}

/* 时间线 */
.timeline-item {{
    border-left: 2px solid {PURPLE_LIGHT};
    padding: 8px 0 8px 16px;
    margin: 8px 0;
    position: relative;
}}
.timeline-item::before {{
    content: '';
    width: 8px;
    height: 8px;
    background: {PURPLE};
    border-radius: 50%;
    position: absolute;
    left: -5px;
    top: 14px;
}}

/* 小贴士 */
.tip-box {{
    background: {PURPLE_BG};
    border-left: 3px solid {PURPLE};
    padding: 12px 16px;
    border-radius: 8px;
    margin: 8px 0;
    color: #1A1A1A;
    font-size: 14px;
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


def execute(sql, params=()):
    conn = get_db()
    cur = conn.execute(sql, params)
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return last_id


# ============= 推荐算法 =============
def get_current_season():
    """根据当前月份返回季节"""
    m = datetime.now().month
    if m in (3, 4, 5): return '春'
    if m in (6, 7, 8): return '夏'
    if m in (9, 10, 11): return '秋'
    return '冬'


def get_current_fruits():
    """当前时令水果"""
    m = datetime.now().month
    fruits = query("SELECT name, season FROM fruits")
    out = []
    for f in fruits:
        s = f['season']
        if s == '全年':
            out.append(f['name'])
            continue
        # 解析 "1-3 月" / "11-1 月" / "5-6 月"
        try:
            parts = s.replace(' 月', '').split('-')
            if len(parts) == 2:
                a, b = int(parts[0]), int(parts[1])
                if a <= b:
                    if a <= m <= b:
                        out.append(f['name'])
                else:  # 跨年，如 11-1
                    if m >= a or m <= b:
                        out.append(f['name'])
        except:
            pass
    return out


def recommend_dishes(meal='早', n=1, exclude_ids=None, mood=None, season=None):
    """推荐菜：基础随机 + 排除已吃 + 加权"""
    exclude_ids = exclude_ids or []
    
    # 取所有主菜谱
    candidates = query("""
        SELECT * FROM recipes 
        WHERE source = '主菜谱' AND id NOT IN ({})
        ORDER BY id
    """.format(','.join('?' * len(exclude_ids)) if exclude_ids else '0'),
        exclude_ids if exclude_ids else []
    )
    
    if not candidates:
        return []
    
    # 加权打分
    today = date.today()
    scored = []
    for c in candidates:
        score = 1.0
        # 评分加权
        if c['avg_rating'] and c['avg_rating'] >= 4.0:
            score += 2
        elif c['avg_rating'] and c['avg_rating'] <= 2.0:
            score -= 3
        # 最近吃过降权
        if c['last_eaten']:
            try:
                last = datetime.strptime(c['last_eaten'], '%Y-%m-%d').date()
                days = (today - last).days
                if days < 3:
                    score -= 10
                elif days < 7:
                    score -= 3
            except:
                pass
        # 心情加权
        if mood == '累' and c['duration'] and c['duration'] <= 30:
            score += 3
        if mood == '招待' and c['category'] in ('肉', '海鲜'):
            score += 2
        # 早午晚粗略
        if meal == '早' and c['category'] in ('素菜', '主食'):
            score += 0.5
        if meal == '晚' and c['category'] == '汤':
            score += 1
        scored.append((score, c))
    
    # 排序后随机抽
    scored.sort(key=lambda x: -x[0])
    top = scored[:max(n*3, 20)]  # 候选池
    random.shuffle(top)
    return [c for _, c in top[:n]]


# ============= 页面渲染 =============
def render_sidebar():
    """侧边栏导航"""
    with st.sidebar:
        st.markdown("### 🍱 今天吃什么")
        st.caption("你的个人美食记忆")
        st.markdown("---")
        
        page = st.radio(
            "导航",
            ["今日", "出菜", "历史", "菜库", "统计"],
            label_visibility="collapsed"
        )
        st.markdown("---")
        
        # 时令水果
        fruits_now = get_current_fruits()
        if fruits_now:
            st.markdown("**当季水果**")
            for f in fruits_now[:8]:
                st.markdown(f'<span class="chip">{f}</span>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.caption(f"📅 {datetime.now().strftime('%Y年%m月%d日')}")
        st.caption(f"🍂 {get_current_season()}季")
    return page


def render_today():
    """今日页：出菜 + 已抽"""
    st.markdown("## 今天吃什么？")
    st.caption(f"{datetime.now().strftime('%Y年%m月%d日 %A')}")
    
    # 今日 banner
    today_count = query("""
        SELECT COUNT(*) as c FROM eaten WHERE date = ?
    """, (date.today().isoformat(),))[0]['c']
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="stat-banner">
          <div class="stat-num">{today_count}</div>
          <div class="stat-label">今日已记录</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        total_recipes = query("SELECT COUNT(*) as c FROM recipes WHERE source='主菜谱'")[0]['c']
        st.markdown(f"""
        <div class="stat-banner">
          <div class="stat-num">{total_recipes}</div>
          <div class="stat-label">主菜谱</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        total_eaten = query("SELECT COUNT(*) as c FROM eaten")[0]['c']
        st.markdown(f"""
        <div class="stat-banner">
          <div class="stat-num">{total_eaten}</div>
          <div class="stat-label">累计打卡</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("")
    
    # 大圆按钮
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🎲 抽一组早午晚", type="primary", use_container_width=True):
            st.session_state['today_dishes'] = {
                '早': recommend_dishes('早', 1),
                '午': recommend_dishes('午', 1),
                '晚': recommend_dishes('晚', 1),
            }
            st.rerun()
    
    # 显示今日菜
    if 'today_dishes' not in st.session_state:
        st.session_state['today_dishes'] = None
    
    today_dishes = st.session_state.get('today_dishes')
    if not today_dishes:
        st.markdown("""
        <div class="empty-state">
          <div class="emoji">🍽️</div>
          <p>还没出菜？点上方按钮抽一组</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    meals = ['早', '午', '晚']
    meal_emoji = {'早': '🥐', '午': '🍱', '晚': '🍲'}
    
    for meal in meals:
        dishes = today_dishes.get(meal, [])
        if not dishes:
            continue
        d = dishes[0]
        st.markdown(f"### {meal_emoji[meal]} {meal}餐")
        
        with st.container():
            st.markdown(f"""
            <div class="recipe-card">
              <h3 style="margin-top:0">{d['name']}</h3>
              <p>
                <span class="chip">{d['category']}</span>
                <span class="chip-gray">👥 2人</span>
              </p>
              {f'<p class="rating">{"★" * int(d["avg_rating"]) if d["avg_rating"] else "☆☆☆☆☆"}</p>' if d['avg_rating'] else ''}
              <p style="color:{GRAY_TEXT};font-size:13px">
                累计吃过 <b>{d['total_eaten']}</b> 次
                {f' · 上次 {d["last_eaten"]}' if d['last_eaten'] else ''}
              </p>
            </div>
            """, unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns([1, 1, 2])
            with c1:
                if st.button("🔄 换一道", key=f"reroll_{meal}"):
                    new = recommend_dishes(meal, 1, exclude_ids=[d['id']])
                    if new:
                        st.session_state['today_dishes'][meal] = new
                        st.rerun()
            with c2:
                if st.button("📋 详情", key=f"detail_{meal}"):
                    st.session_state['view_recipe_id'] = d['id']
                    st.session_state['page'] = '菜库'
                    st.rerun()
            with c3:
                if st.button(f"✅ 记录 {meal}餐吃这道", key=f"eat_{meal}", type="primary"):
                    execute("""
                        INSERT INTO eaten (recipe_id, date, meal) VALUES (?, ?, ?)
                    """, (d['id'], date.today().isoformat(), meal))
                    execute("""
                        UPDATE recipes SET total_eaten = total_eaten + 1, last_eaten = ? WHERE id = ?
                    """, (date.today().isoformat(), d['id']))
                    st.success(f"已记录 {meal}餐：{d['name']}")
                    st.rerun()


def render_pick():
    """出菜页：场景筛选 + 加权"""
    st.markdown("## 换个新菜")
    
    # 心情 + 场景
    st.markdown("### 心情")
    mood_cols = st.columns(5)
    moods = ['累', '开心', '招待', '加班', '想家']
    if 'mood' not in st.session_state:
        st.session_state['mood'] = '全部'
    for i, m in enumerate(moods):
        with mood_cols[i]:
            if st.button(m, key=f"mood_{m}", 
                         type="primary" if st.session_state.mood == m else "secondary"):
                st.session_state.mood = m
                st.rerun()
    if st.session_state.mood == '全部':
        st.session_state.mood = None
    
    # 菜系筛���
    st.markdown("### 菜系")
    cats = query("SELECT DISTINCT category FROM recipes WHERE source='主菜谱' AND category IS NOT NULL")
    cat_list = ['全部'] + [c['category'] for c in cats]
    cat_cols = st.columns(len(cat_list))
    if 'cat' not in st.session_state:
        st.session_state.cat = '全部'
    for i, c in enumerate(cat_list):
        with cat_cols[i]:
            if st.button(c, key=f"cat_{c}",
                         type="primary" if st.session_state.cat == c else "secondary"):
                st.session_state.cat = c
                st.rerun()
    
    # 出菜
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        n = st.slider("抽几道？", 1, 10, 5)
        if st.button("✨ 开始推荐", type="primary", use_container_width=True):
            where = "source = '主菜谱'"
            params = []
            if st.session_state.cat != '全部':
                where += " AND category = ?"
                params.append(st.session_state.cat)
            candidates = query(f"SELECT * FROM recipes WHERE {where}", params)
            
            # 简单加权
            if st.session_state.mood == '累':
                candidates = [c for c in candidates if not c['duration'] or c['duration'] <= 30]
            
            random.shuffle(candidates)
            st.session_state['pick_result'] = candidates[:n]
            st.rerun()
    
    # 显示结果
    if 'pick_result' in st.session_state and st.session_state.pick_result:
        st.markdown("### 推荐给你")
        for d in st.session_state.pick_result:
            with st.container():
                st.markdown(f"""
                <div class="recipe-card">
                  <h3 style="margin-top:0">{d['name']}</h3>
                  <p>
                    <span class="chip">{d['category']}</span>
                    {f'<span class="chip">⏰ {d["duration"]}min</span>' if d['duration'] else ''}
                  </p>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"📋 看 {d['name']} 详情", key=f"pick_detail_{d['id']}"):
                    st.session_state['view_recipe_id'] = d['id']
                    st.session_state['page'] = '菜库'
                    st.rerun()


def render_history():
    """历史页：日历 + 打卡"""
    st.markdown("## 我们吃了什么")
    
    # 今日打卡
    st.markdown("### 今日")
    today_records = query("""
        SELECT e.*, r.name as recipe_name, r.category 
        FROM eaten e JOIN recipes r ON e.recipe_id = r.id 
        WHERE e.date = ?
    """, (date.today().isoformat(),))
    
    meals = ['早', '午', '晚']
    for meal in meals:
        eaten = [t for t in today_records if t['meal'] == meal]
        if eaten:
            e = eaten[0]
            rating_str = "★" * (e['rating'] or 0) if e['rating'] else ''
            st.markdown(f"""
            <div class="recipe-card">
              <h4>✅ {meal}餐：{e['recipe_name']}</h4>
              <p class="rating">{rating_str}</p>
              {f'<div class="tip-box">💡 {e["tips"]}</div>' if e['tips'] else ''}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="recipe-card">
              <h4>⏳ {meal}餐：还没记录</h4>
              <p style="color:{GRAY_TEXT}">去"今日"页抽一道吃</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 最近 7 天
    st.markdown("### 最近 7 天")
    week_ago = (date.today() - timedelta(days=7)).isoformat()
    recent = query("""
        SELECT e.*, r.name as recipe_name 
        FROM eaten e JOIN recipes r ON e.recipe_id = r.id 
        WHERE e.date >= ? ORDER BY e.date DESC, e.meal
    """, (week_ago,))
    
    if recent:
        # 按日期分组
        from collections import defaultdict
        by_date = defaultdict(list)
        for r in recent:
            by_date[r['date']].append(r)
        for d, items in list(by_date.items())[:7]:
            with st.expander(f"📅 {d} ({len(items)} 道)"):
                for it in items:
                    st.markdown(f"- **{it['meal']}餐**：{it['recipe_name']} {'★' * (it['rating'] or 0) if it['rating'] else ''}")
                    if it['tips']:
                        st.caption(f"  💡 {it['tips']}")
    else:
        st.markdown("""
        <div class="empty-state">
          <div class="emoji">📅</div>
          <p>最近 7 天还没有记录</p>
        </div>
        """, unsafe_allow_html=True)


def render_library():
    """菜库页：菜谱列表 + 详情 + 吃完记录"""
    # 详情模式
    if 'view_recipe_id' in st.session_state and st.session_state.view_recipe_id:
        render_recipe_detail(st.session_state.view_recipe_id)
        return
    
    st.markdown("## 菜谱库")
    
    # 统计
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        n_main = query("SELECT COUNT(*) as c FROM recipes WHERE source='主菜谱'")[0]['c']
        st.markdown(f'<div class="stat-num">{n_main}</div><div class="stat-label">主菜谱</div>', unsafe_allow_html=True)
    with col2:
        n_xianovo = query("SELECT COUNT(*) as c FROM recipes WHERE source='小象超市'")[0]['c']
        st.markdown(f'<div class="stat-num">{n_xianovo}</div><div class="stat-label">小象超市</div>', unsafe_allow_html=True)
    with col3:
        n_eaten = query("SELECT COUNT(*) as c FROM recipes WHERE total_eaten > 0")[0]['c']
        st.markdown(f'<div class="stat-num">{n_eaten}</div><div class="stat-label">吃过的</div>', unsafe_allow_html=True)
    with col4:
        n_total_eaten = query("SELECT COUNT(*) as c FROM eaten")[0]['c']
        st.markdown(f'<div class="stat-num">{n_total_eaten}</div><div class="stat-label">总打卡</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 搜索
    search = st.text_input("🔍 搜菜名 / 主料", "")
    
    # 来源筛选
    src = st.selectbox("来源", ["全部", "主菜谱", "小象超市", "外卖"])
    
    # 分类筛选
    cats = query("SELECT DISTINCT category FROM recipes WHERE category IS NOT NULL ORDER BY category")
    cat_list = ['全部'] + [c['category'] for c in cats]
    cat = st.selectbox("分类", cat_list)
    
    # 查询
    where = "1=1"
    params = []
    if search:
        where += " AND name LIKE ?"
        params.append(f"%{search}%")
    if src != "全部":
        where += " AND source = ?"
        params.append(src)
    if cat != "全部":
        where += " AND category = ?"
        params.append(cat)
    
    recipes = query(f"SELECT * FROM recipes WHERE {where} ORDER BY total_eaten DESC, name LIMIT 200", params)
    
    st.caption(f"共 {len(recipes)} 道")
    
    # 列表
    for d in recipes:
        with st.container():
            eaten_str = f'<span class="chip">吃过 {d["total_eaten"]} 次</span>' if d['total_eaten'] else ''
            rating_str = f'<span class="rating">{"★" * int(d["avg_rating"]) if d["avg_rating"] else ""}</span>' if d['avg_rating'] else ''
            
            st.markdown(f"""
            <div class="recipe-card">
              <div style="display:flex;justify-content:space-between;align-items:center">
                <h4 style="margin:0">{d['name']}</h4>
                {rating_str}
              </div>
              <p style="margin:8px 0">
                <span class="chip">{d['source']}</span>
                {f'<span class="chip">{d["category"]}</span>' if d['category'] else ''}
                {eaten_str}
                {f'<span class="chip-gray">上次 {d["last_eaten"]}</span>' if d['last_eaten'] else ''}
              </p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"📋 详情", key=f"lib_detail_{d['id']}"):
                st.session_state['view_recipe_id'] = d['id']
                st.rerun()


def render_recipe_detail(recipe_id):
    """菜详情页（核心）"""
    r = query("SELECT * FROM recipes WHERE id = ?", (recipe_id,))[0]
    
    # 返回
    if st.button("← 返回菜库"):
        st.session_state.view_recipe_id = None
        st.rerun()
    
    # 标题
    st.markdown(f"""
    <h1 style="margin-bottom:8px">{r['name']}</h1>
    <p>
      <span class="chip">{r['source']}</span>
      {f'<span class="chip">{r["category"]}</span>' if r['category'] else ''}
    </p>
    """, unsafe_allow_html=True)
    
    # 统计
    st.markdown(f"""
    <div class="stat-banner">
      <div style="display:flex;justify-content:space-around">
        <div>
          <div class="stat-num">{r['total_eaten']}</div>
          <div class="stat-label">累计吃过</div>
        </div>
        <div>
          <div class="stat-num">{f"{r['avg_rating']:.1f}" if r['avg_rating'] else "-"}</div>
          <div class="stat-label">平均评分</div>
        </div>
        <div>
          <div class="stat-num">{f"⭐{int(r['avg_rating'])}" if r['avg_rating'] else "未评分"}</div>
          <div class="stat-label">推荐度</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("")
    
    # 做这道
    if st.button("✅ 今日做这道", type="primary", use_container_width=True):
        execute("""
            INSERT INTO eaten (recipe_id, date, meal) VALUES (?, ?, ?)
        """, (r['id'], date.today().isoformat(), '午'))
        execute("""
            UPDATE recipes SET total_eaten = total_eaten + 1, last_eaten = ? WHERE id = ?
        """, (date.today().isoformat(), r['id']))
        st.success(f"已记录：{r['name']}，记得吃完来打分和拍照！")
        st.rerun()
    
    st.markdown("---")
    
    # 吃完记录表单
    st.markdown("### 📝 吃完记录")
    
    eaten_today = query("""
        SELECT id, meal, rating, tips, photo_path 
        FROM eaten 
        WHERE recipe_id = ? AND date = ? 
        ORDER BY id DESC LIMIT 1
    """, (r['id'], date.today().isoformat()))
    
    if eaten_today:
        et = eaten_today[0]
        st.info(f"今日已记录（{et['meal']}餐）")
        
        col1, col2 = st.columns(2)
        with col1:
            rating = st.select_slider("⭐ 评分", options=[1, 2, 3, 4, 5], value=et['rating'] or 3, key="detail_rating")
        with col2:
            mood = st.selectbox("💭 心情", ['累', '开心', '招待', '加班', '想家', '其他'], key="detail_mood")
        
        tips = st.text_area("💡 今天的 tips / 改进", value=et['tips'] or "", key="detail_tips",
                            placeholder="比如：煎老了下次小火 / 加粉丝也好吃 / 忘了放蚝油")
        
        # 照片上传
        photo = st.file_uploader("📷 上传照片（可选）", type=['jpg', 'jpeg', 'png'], key="detail_photo")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("保存记录", type="primary"):
                photo_path = et['photo_path']
                if photo:
                    # 保存照片
                    fname = f"{r['id']}_{date.today().isoformat()}_{datetime.now().strftime('%H%M%S')}.jpg"
                    save_path = PHOTOS_DIR / fname
                    with open(save_path, 'wb') as f:
                        f.write(photo.read())
                    photo_path = str(save_path)
                
                # 更新 eaten 记录
                execute("""
                    UPDATE eaten SET rating=?, tips=?, mood=?, photo_path=? WHERE id=?
                """, (rating, tips, mood, photo_path, et['id']))
                
                # 更新 recipe 统计
                avg_row = query("SELECT AVG(rating) as a, COUNT(*) as c FROM eaten WHERE recipe_id=? AND rating IS NOT NULL", (r['id'],))[0]
                execute("UPDATE recipes SET avg_rating=? WHERE id=?", (avg_row['a'], r['id']))
                
                st.success("已保存！")
                st.rerun()
        with col2:
            if et['photo_path'] and os.path.exists(et['photo_path']):
                st.image(et['photo_path'], caption="上次照片", width=200)
    
    st.markdown("---")
    
    # 吃法时间线
    st.markdown("### 📅 吃法时间线（你的历史）")
    history = query("""
        SELECT * FROM eaten WHERE recipe_id = ? AND tips IS NOT NULL 
        ORDER BY date DESC LIMIT 20
    """, (r['id'],))
    
    if history:
        for h in history:
            st.markdown(f"""
            <div class="timeline-item">
              <b>{h['date']} {h['meal']}餐</b>
              <span class="rating">{"★" * (h['rating'] or 0)}</span>
              {f'<div class="tip-box">💡 {h["tips"]}</div>' if h['tips'] else ''}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.caption("还没有 tips，做几次就有经验了")
    
    st.markdown("---")
    
    # 收藏 / 跳过
    col1, col2 = st.columns(2)
    with col1:
        if st.button("❤️ 收藏", use_container_width=True):
            execute("UPDATE recipes SET favorite=1 WHERE id=?", (r['id'],))
            st.success("已收藏")
            st.rerun()
    with col2:
        if st.button("👎 跳过", use_container_width=True):
            execute("UPDATE recipes SET skipped=1 WHERE id=?", (r['id'],))
            st.success("已标记跳过")
            st.rerun()


def render_stats():
    """统计页：所有数据"""
    st.markdown("## 📊 你的美食记忆")
    
    # 总数据
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 累计")
        n_days = query("SELECT COUNT(DISTINCT date) as c FROM eaten")[0]['c']
        n_eaten = query("SELECT COUNT(*) as c FROM eaten")[0]['c']
        n_recipes = query("SELECT COUNT(DISTINCT recipe_id) as c FROM eaten")[0]['c']
        st.markdown(f"打卡 **{n_days}** 天")
        st.markdown(f"吃过 **{n_eaten}** 道")
        st.markdown(f"解锁 **{n_recipes}** 种菜")
    
    with col2:
        st.markdown("### 本月")
        first_day = date.today().replace(day=1).isoformat()
        m_days = query("SELECT COUNT(DISTINCT date) as c FROM eaten WHERE date >= ?", (first_day,))[0]['c']
        m_eaten = query("SELECT COUNT(*) as c FROM eaten WHERE date >= ?", (first_day,))[0]['c']
        st.markdown(f"打卡 **{m_days}** 天")
        st.markdown(f"吃过 **{m_eaten}** 道")
    
    st.markdown("---")
    
    # 你的 top 5
    st.markdown("### 🏆 你的 Top 5")
    top = query("""
        SELECT name, total_eaten, avg_rating 
        FROM recipes 
        WHERE total_eaten > 0
        ORDER BY total_eaten DESC LIMIT 5
    """)
    
    if top:
        for i, t in enumerate(top, 1):
            st.markdown(f"""
            <div class="recipe-card">
              <h4>#{i} {t['name']}</h4>
              <p>吃过 <b>{t['total_eaten']}</b> 次 · 平均 ★{f"{t['avg_rating']:.1f}" if t['avg_rating'] else '-'} </p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.caption("还没有记录，去「今日」抽菜吃吧！")
    
    st.markdown("---")
    
    # 数据导出
    st.markdown("### 📦 数据管理")
    if st.button("导出全部数据为 JSON", use_container_width=True):
        all_data = {
            'recipes': [dict(r) for r in query("SELECT * FROM recipes")],
            'eaten': [dict(e) for e in query("SELECT * FROM eaten")],
            'exported_at': datetime.now().isoformat(),
        }
        fname = f"recipes_{date.today().isoformat()}.json"
        with open(fname, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2, default=str)
        with open(fname, 'r', encoding='utf-8') as f:
            st.download_button("⬇️ 下载", f.read(), file_name=fname, mime="application/json")
        os.remove(fname)


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
    
    if 'page' in st.session_state:
        page = st.session_state.page
    
    if page == "今日":
        render_today()
    elif page == "出菜":
        render_pick()
    elif page == "历史":
        render_history()
    elif page == "菜库":
        render_library()
    elif page == "统计":
        render_stats()


if __name__ == '__main__':
    main()
