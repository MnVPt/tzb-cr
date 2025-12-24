"""
多高校统战部新闻爬取工具 - Streamlit应用
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from io import BytesIO
from datetime import datetime
from scrapers import scrape_all_universities, UNIVERSITIES


def convert_to_excel(news_list):
    """将新闻列表转换为Excel文件"""
    df = pd.DataFrame(news_list)
    # 重命名列
    df = df.rename(columns={
        "source": "来源",
        "title": "新闻标题",
        "date": "发布日期",
        "url": "原文链接"
    })
    # 调整列顺序
    df = df[["来源", "新闻标题", "发布日期", "原文链接"]]
    
    # 创建Excel文件
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='统战新闻')
        
        # 获取工作表
        workbook = writer.book
        worksheet = writer.sheets['统战新闻']
        
        # 设置列宽
        worksheet.set_column('A:A', 18)  # 来源
        worksheet.set_column('B:B', 60)  # 新闻标题
        worksheet.set_column('C:C', 12)  # 发布日期
        worksheet.set_column('D:D', 50)  # 原文链接
        
        # 设置表头格式
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#1e3a5f',
            'font_color': 'white',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })
        
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
    
    return output.getvalue()

# 页面配置
st.set_page_config(
    page_title="高校统战部新闻爬取工具",
    page_icon="📰",
    layout="wide"
)

# 自定义CSS样式
st.markdown("""
<style>
    /* 主标题样式 */
    .main-title {
        text-align: center;
        color: #1e3a5f;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        font-family: 'Source Han Sans CN', 'PingFang SC', 'Microsoft YaHei', sans-serif;
    }
    
    .sub-title {
        text-align: center;
        color: #5a6c7d;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    
    /* 按钮容器居中 */
    .button-container {
        display: flex;
        justify-content: center;
        margin: 2rem 0;
    }
    
    /* 新闻表格样式 */
    .news-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 1.5rem;
        font-size: 0.95rem;
    }
    
    .news-table th {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        color: white;
        padding: 12px 16px;
        text-align: left;
        font-weight: 600;
    }
    
    .news-table td {
        padding: 12px 16px;
        border-bottom: 1px solid #e8eef3;
    }
    
    .news-table tr:hover {
        background-color: #f5f9fc;
    }
    
    .news-table a {
        color: #1e3a5f;
        text-decoration: none;
        transition: color 0.2s;
    }
    
    .news-table a:hover {
        color: #3d7cb8;
        text-decoration: underline;
    }
    
    .source-tag {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 0.85rem;
        font-weight: 500;
    }
    
    .source-fudan { background-color: #e3f2fd; color: #1565c0; }
    .source-sjtu { background-color: #fce4ec; color: #c62828; }
    .source-tongji { background-color: #e8f5e9; color: #2e7d32; }
    
    .date-text {
        color: #78909c;
        font-size: 0.9rem;
    }
    
    /* 统计信息样式 */
    .stats-container {
        display: flex;
        justify-content: center;
        gap: 2rem;
        margin: 1.5rem 0;
        flex-wrap: wrap;
    }
    
    .stat-item {
        text-align: center;
        padding: 1rem 2rem;
        background: #f8fafc;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: 700;
        color: #1e3a5f;
    }
    
    .stat-label {
        font-size: 0.9rem;
        color: #64748b;
    }
</style>
""", unsafe_allow_html=True)

# 页面标题
st.markdown('<h1 class="main-title">🏫 高校统战部新闻爬取工具</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">一键获取各高校统战部最新动态</p>', unsafe_allow_html=True)

# 显示已配置的高校
with st.expander("📋 已配置高校列表", expanded=False):
    cols = st.columns(3)
    for i, (name, config) in enumerate(UNIVERSITIES.items()):
        with cols[i % 3]:
            st.markdown(f"**{name}**")
            st.caption(config["url"])

# 爬取按钮（居中）
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    fetch_button = st.button("🔍 爬取新闻", use_container_width=True, type="primary")

# 会话状态存储
if "news_data" not in st.session_state:
    st.session_state.news_data = []
if "errors" not in st.session_state:
    st.session_state.errors = []
if "fetched" not in st.session_state:
    st.session_state.fetched = False

# 爬取逻辑
if fetch_button:
    with st.spinner("正在爬取各高校统战部新闻，请稍候..."):
        news, errors = scrape_all_universities()
        st.session_state.news_data = news
        st.session_state.errors = errors
        st.session_state.fetched = True

# 显示结果
if st.session_state.fetched:
    # 显示错误信息
    if st.session_state.errors:
        st.warning("⚠️ " + " | ".join(st.session_state.errors))
    
    news = st.session_state.news_data
    
    if news:
        # 统计信息
        source_counts = {}
        for item in news:
            source = item["source"]
            source_counts[source] = source_counts.get(source, 0) + 1
        
        st.markdown(f"""
        <div class="stats-container">
            <div class="stat-item">
                <div class="stat-number">{len(news)}</div>
                <div class="stat-label">新闻总数</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{len(source_counts)}</div>
                <div class="stat-label">数据来源</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 下载按钮
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            excel_data = convert_to_excel(news)
            filename = f"统战新闻_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            st.download_button(
                label="📥 导出Excel文件",
                data=excel_data,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        # 构建新闻表格HTML
        def get_source_class(source):
            if "复旦" in source:
                return "source-fudan"
            elif "交通" in source:
                return "source-sjtu"
            elif "同济" in source:
                return "source-tongji"
            elif "华东师范" in source:
                return "source-ecnu"
            elif "上海师范" in source:
                return "source-shnu"
            elif "社会主义学院" in source:
                return "source-shsy"
            return "source-default"
        
        table_html = """
        <table class="news-table">
            <thead>
                <tr>
                    <th style="width: 120px;">来源</th>
                    <th>新闻标题</th>
                    <th style="width: 120px;">发布日期</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for item in news:
            source_class = get_source_class(item["source"])
            table_html += f"""
                <tr>
                    <td><span class="source-tag {source_class}">{item['source']}</span></td>
                    <td><a href="{item['url']}" target="_blank" rel="noopener noreferrer">{item['title']}</a></td>
                    <td class="date-text">{item['date']}</td>
                </tr>
            """
        
        table_html += """
            </tbody>
        </table>
        """
        
        # 使用 components.html 渲染可点击的表格
        # 计算表格高度：每行约50px + 表头60px + padding
        table_height = min(len(news) * 50 + 100, 800)
        
        full_html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Source Han Sans CN', 'PingFang SC', 'Microsoft YaHei', sans-serif;
                    margin: 0;
                    padding: 0;
                }}
                .news-table {{
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 14px;
                }}
                .news-table th {{
                    background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
                    color: white;
                    padding: 12px 16px;
                    text-align: left;
                    font-weight: 600;
                    position: sticky;
                    top: 0;
                }}
                .news-table td {{
                    padding: 12px 16px;
                    border-bottom: 1px solid #e8eef3;
                }}
                .news-table tr:hover {{
                    background-color: #f5f9fc;
                }}
                .news-table a {{
                    color: #1e3a5f;
                    text-decoration: none;
                }}
                .news-table a:hover {{
                    color: #3d7cb8;
                    text-decoration: underline;
                }}
                .source-tag {{
                    display: inline-block;
                    padding: 4px 10px;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: 500;
                    white-space: nowrap;
                }}
                .source-fudan {{ background-color: #e3f2fd; color: #1565c0; }}
                .source-sjtu {{ background-color: #fce4ec; color: #c62828; }}
                .source-tongji {{ background-color: #e8f5e9; color: #2e7d32; }}
                .source-ecnu {{ background-color: #fff3e0; color: #e65100; }}
                .source-shnu {{ background-color: #f3e5f5; color: #7b1fa2; }}
                .source-shsy {{ background-color: #ffebee; color: #b71c1c; }}
                .source-default {{ background-color: #eceff1; color: #455a64; }}
                .date-text {{
                    color: #78909c;
                    font-size: 13px;
                    white-space: nowrap;
                }}
            </style>
        </head>
        <body>
            {table_html}
        </body>
        </html>
        """
        components.html(full_html, height=table_height, scrolling=True)
    else:
        st.info("未获取到新闻数据，请检查网络连接或稍后重试。")
else:
    # 初始提示
    st.markdown("""
    <div style="text-align: center; padding: 3rem; color: #64748b;">
        <p style="font-size: 1.1rem;">点击上方按钮开始爬取新闻</p>
        <p style="font-size: 0.9rem; margin-top: 0.5rem;">支持复旦大学、上海交通大学、同济大学、华东师范大学、上海师范大学、上海市社会主义学院</p>
    </div>
    """, unsafe_allow_html=True)

# 页脚
st.markdown("---")
st.markdown(
    '<p style="text-align: center; color: #94a3b8; font-size: 0.85rem;">高校统战部新闻爬取工具 MVP v1.0</p>',
    unsafe_allow_html=True
)

