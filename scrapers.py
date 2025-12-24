"""
多高校统战部新闻爬虫模块
支持复旦大学、上海交通大学、同济大学
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional
import re

# 请求超时时间（秒）
REQUEST_TIMEOUT = 5

# 请求头，模拟浏览器访问
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# 高校配置
UNIVERSITIES = {
    "复旦大学": {
        "url": "https://www.tzb.fudan.edu.cn/20423/list.htm",
        "base_url": "https://www.tzb.fudan.edu.cn",
        "parser": "fudan"
    },
    "上海交通大学": {
        "url": "https://tzb.sjtu.edu.cn/news",
        "base_url": "https://tzb.sjtu.edu.cn",
        "parser": "sjtu"
    },
    "同济大学": {
        "url": "https://tzb.tongji.edu.cn/syxw/list.htm",
        "base_url": "https://tzb.tongji.edu.cn",
        "parser": "tongji"
    },
    "华东师范大学": {
        "url": "https://tzb.ecnu.edu.cn/tzxw/list.htm",
        "base_url": "https://tzb.ecnu.edu.cn",
        "parser": "ecnu"
    },
    "上海师范大学": {
        "url": "https://tzb.shnu.edu.cn/zhyw/list.htm",
        "base_url": "https://tzb.shnu.edu.cn",
        "parser": "shnu"
    },
    "上海市社会主义学院": {
        "url": "https://www.shsy.org.cn/node933/shsy/tzll/gzdt/index.html",
        "base_url": "https://www.shsy.org.cn",
        "parser": "shsy"
    }
}


def fetch_page(url: str) -> Optional[str]:
    """获取网页内容"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        return response.text
    except Exception as e:
        print(f"获取页面失败 {url}: {e}")
        return None


def is_valid_news(title: str, url: str, date_text: str) -> bool:
    """判断是否为有效的新闻条目"""
    # 过滤掉太短的标题
    if len(title) < 6:
        return False
    
    # 过滤掉导航类链接
    nav_keywords = [
        "首页", "更多", "详情", "查看", "点击", "下载", "登录", "注册",
        "部门概况", "统战团体", "民主党派", "参政议政", "理论园地", "服务指南",
        "复旦统战", "两会专题", "交大首页", "智慧统战", "中国人大网", "中国政协网",
        "中央统战部", "上海统一战线", "民革", "民盟", "民建", "民进", "农工党", 
        "致公党", "九三学社", "台盟", "侨联", "欧美同学会", "知联会", "台联", "民族联"
    ]
    
    # 如果标题完全匹配导航关键词，过滤掉
    if title in nav_keywords:
        return False
    
    # 如果标题很短且是导航关键词的一部分
    for kw in nav_keywords:
        if title == kw or (len(title) < 10 and kw in title):
            return False
    
    # 过滤掉外部链接（非本站新闻页面）
    if "list.htm" in url and "/c" not in url:
        return False
    
    # 必须有日期才认为是新闻
    if not date_text:
        return False
    
    return True


def parse_fudan(html: str, base_url: str) -> List[Dict]:
    """
    解析复旦大学统战部新闻列表
    网页结构：新闻列表在 <ul> 中，每条新闻为 <li>，包含 <a> 标签和日期
    """
    news_list = []
    soup = BeautifulSoup(html, "lxml")
    
    # 查找新闻列表项 - 更精确的选择器
    news_items = soup.select("ul.news_list li, ul.wp_article_list li, div.news_list li")
    
    if not news_items:
        # 备选：查找包含日期的 li
        news_items = []
        for li in soup.find_all("li"):
            text = li.get_text()
            if re.search(r"\d{4}[-/]\d{1,2}[-/]\d{1,2}", text):
                news_items.append(li)
    
    for item in news_items:
        try:
            # 查找标题链接
            link = item.find("a")
            if not link or not link.get("href"):
                continue
            
            title = link.get_text(strip=True)
            href = link.get("href", "")
            url = urljoin(base_url, href)
            
            # 查找日期
            date_text = ""
            # 方法1：查找 span 中的日期
            date_span = item.find("span", class_=re.compile(r"date|time|Article_PublishDate"))
            if date_span:
                date_text = date_span.get_text(strip=True)
            else:
                # 方法2：从整个 li 文本中提取日期
                item_text = item.get_text()
                date_match = re.search(r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})", item_text)
                if date_match:
                    date_text = date_match.group(1).replace("/", "-")
            
            # 验证是否为有效新闻
            if is_valid_news(title, url, date_text):
                news_list.append({
                    "source": "复旦大学",
                    "title": title,
                    "date": date_text,
                    "url": url
                })
        except Exception:
            continue
    
    return news_list


def parse_sjtu(html: str, base_url: str) -> List[Dict]:
    """
    解析上海交通大学统战部新闻列表
    交大网站新闻链接格式为 /post/xxx
    """
    news_list = []
    soup = BeautifulSoup(html, "lxml")
    
    # 查找所有包含 /post/ 的链接（这是交大新闻的特征）
    news_links = soup.find_all("a", href=lambda x: x and "/post/" in x)
    
    for link in news_links:
        try:
            href = link.get("href", "")
            url = urljoin(base_url, href)
            
            # 获取标题文本
            title = link.get_text(strip=True)
            
            # 从标题或父元素中提取日期
            date_text = ""
            # 先尝试从标题中提取日期
            date_match = re.search(r"(\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2})", title)
            if date_match:
                date_text = date_match.group(1).replace(".", "-").replace("/", "-")
                # 从标题中去掉日期部分
                title = re.sub(r"^\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2}\s*", "", title)
            else:
                # 从父元素中查找日期
                parent = link.find_parent()
                if parent:
                    parent_text = parent.get_text()
                    date_match = re.search(r"(\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2})", parent_text)
                    if date_match:
                        date_text = date_match.group(1).replace(".", "-").replace("/", "-")
            
            # 清理标题
            title = title.strip()
            
            # 验证是否为有效新闻
            if title and len(title) >= 6 and date_text:
                news_list.append({
                    "source": "上海交通大学",
                    "title": title,
                    "date": date_text,
                    "url": url
                })
        except Exception:
            continue
    
    return news_list


def parse_tongji(html: str, base_url: str) -> List[Dict]:
    """
    解析同济大学统战部新闻列表
    网页结构类似复旦，使用 list.htm 格式
    """
    news_list = []
    soup = BeautifulSoup(html, "lxml")
    
    # 查找新闻列表项 - 更精确的选择器
    news_items = soup.select("ul.news_list li, ul.wp_article_list li, div.news_list li")
    
    if not news_items:
        # 备选：查找包含日期的 li
        news_items = []
        for li in soup.find_all("li"):
            text = li.get_text()
            if re.search(r"\d{4}[-/]\d{1,2}[-/]\d{1,2}", text):
                news_items.append(li)
    
    for item in news_items:
        try:
            link = item.find("a")
            if not link or not link.get("href"):
                continue
            
            title = link.get_text(strip=True)
            href = link.get("href", "")
            url = urljoin(base_url, href)
            
            # 查找日期
            date_text = ""
            date_span = item.find("span", class_=re.compile(r"date|time|Article_PublishDate"))
            if date_span:
                date_text = date_span.get_text(strip=True)
            else:
                item_text = item.get_text()
                date_match = re.search(r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})", item_text)
                if date_match:
                    date_text = date_match.group(1).replace("/", "-")
            
            # 验证是否为有效新闻
            if is_valid_news(title, url, date_text):
                news_list.append({
                    "source": "同济大学",
                    "title": title,
                    "date": date_text,
                    "url": url
                })
        except Exception:
            continue
    
    return news_list


def parse_ecnu(html: str, base_url: str) -> List[Dict]:
    """
    解析华东师范大学统战部新闻列表
    网页结构类似复旦，使用 list.htm 格式
    """
    news_list = []
    soup = BeautifulSoup(html, "lxml")
    
    # 查找新闻列表项
    news_items = soup.select("ul.news_list li, ul.wp_article_list li, div.news_list li")
    
    if not news_items:
        news_items = []
        for li in soup.find_all("li"):
            text = li.get_text()
            if re.search(r"\d{4}[-/]\d{1,2}[-/]\d{1,2}", text):
                news_items.append(li)
    
    for item in news_items:
        try:
            link = item.find("a")
            if not link or not link.get("href"):
                continue
            
            title = link.get_text(strip=True)
            href = link.get("href", "")
            url = urljoin(base_url, href)
            
            # 查找日期
            date_text = ""
            date_span = item.find("span", class_=re.compile(r"date|time|Article_PublishDate"))
            if date_span:
                date_text = date_span.get_text(strip=True)
            else:
                item_text = item.get_text()
                date_match = re.search(r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})", item_text)
                if date_match:
                    date_text = date_match.group(1).replace("/", "-")
            
            if is_valid_news(title, url, date_text):
                news_list.append({
                    "source": "华东师范大学",
                    "title": title,
                    "date": date_text,
                    "url": url
                })
        except Exception:
            continue
    
    return news_list


def parse_shnu(html: str, base_url: str) -> List[Dict]:
    """
    解析上海师范大学统战部新闻列表
    网页结构类似复旦，使用 list.htm 格式
    """
    news_list = []
    soup = BeautifulSoup(html, "lxml")
    
    # 查找新闻列表项
    news_items = soup.select("ul.news_list li, ul.wp_article_list li, div.news_list li")
    
    if not news_items:
        news_items = []
        for li in soup.find_all("li"):
            text = li.get_text()
            if re.search(r"\d{4}[-/]\d{1,2}[-/]\d{1,2}", text):
                news_items.append(li)
    
    for item in news_items:
        try:
            link = item.find("a")
            if not link or not link.get("href"):
                continue
            
            title = link.get_text(strip=True)
            href = link.get("href", "")
            url = urljoin(base_url, href)
            
            # 查找日期
            date_text = ""
            date_span = item.find("span", class_=re.compile(r"date|time|Article_PublishDate"))
            if date_span:
                date_text = date_span.get_text(strip=True)
            else:
                item_text = item.get_text()
                date_match = re.search(r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})", item_text)
                if date_match:
                    date_text = date_match.group(1).replace("/", "-")
            
            if is_valid_news(title, url, date_text):
                news_list.append({
                    "source": "上海师范大学",
                    "title": title,
                    "date": date_text,
                    "url": url
                })
        except Exception:
            continue
    
    return news_list


def parse_shsy(html: str, base_url: str) -> List[Dict]:
    """
    解析上海市社会主义学院新闻列表
    该网站使用 JS 变量存储新闻数据，需要特殊处理
    """
    news_list = []
    
    # 尝试直接获取 JSON 数据
    try:
        json_url = "https://www.shsy.org.cn/json/gzdt.js"
        response = requests.get(json_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.encoding = 'utf-8'
        js_content = response.text
        
        # 提取 JSON 数组
        # 格式: var gzdtList = [...]
        match = re.search(r'var\s+gzdtList\s*=\s*(\[.*\])', js_content, re.DOTALL)
        if match:
            import json
            json_str = match.group(1)
            data = json.loads(json_str)
            
            for item in data:
                try:
                    title = item.get("messagetitle", "").strip()
                    date_text = item.get("messagedate", "").strip()
                    msg_url = item.get("messageurl", "").strip()
                    
                    # 构建完整URL
                    # 注意：详情页URL的正确格式是 https://www.shsy.org.cn/detailpage/xxx.html
                    if msg_url.startswith("http"):
                        url = msg_url
                    elif msg_url.startswith("detailpage/"):
                        url = "https://www.shsy.org.cn/" + msg_url
                    elif msg_url:
                        url = urljoin("https://www.shsy.org.cn/", msg_url)
                    else:
                        continue
                    
                    if title and len(title) >= 2 and date_text:
                        news_list.append({
                            "source": "上海市社会主义学院",
                            "title": title,
                            "date": date_text,
                            "url": url
                        })
                except Exception:
                    continue
    except Exception as e:
        print(f"解析上海市社会主义学院失败: {e}")
    
    return news_list


# 解析器映射
PARSERS = {
    "fudan": parse_fudan,
    "sjtu": parse_sjtu,
    "tongji": parse_tongji,
    "ecnu": parse_ecnu,
    "shnu": parse_shnu,
    "shsy": parse_shsy,
}


def scrape_university(name: str, config: Dict) -> tuple[str, List[Dict], Optional[str]]:
    """
    爬取单个高校的新闻
    返回: (高校名, 新闻列表, 错误信息)
    """
    try:
        html = fetch_page(config["url"])
        if html is None:
            return (name, [], f"{name}网站访问超时或失败")
        
        parser = PARSERS.get(config["parser"])
        if parser is None:
            return (name, [], f"{name}解析器未找到")
        
        news = parser(html, config["base_url"])
        return (name, news, None)
    except Exception as e:
        return (name, [], f"{name}爬取异常: {str(e)}")


def scrape_all_universities() -> tuple[List[Dict], List[str]]:
    """
    并发爬取所有高校的新闻
    返回: (所有新闻列表, 错误信息列表)
    """
    all_news = []
    errors = []
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(scrape_university, name, config): name
            for name, config in UNIVERSITIES.items()
        }
        
        for future in as_completed(futures):
            name, news, error = future.result()
            if error:
                errors.append(error)
            all_news.extend(news)
    
    # 按日期倒序排序（最新在前）
    def parse_date(item):
        date_str = item.get("date", "")
        if date_str:
            try:
                # 统一日期格式为 YYYY-MM-DD
                date_str = date_str.replace("/", "-")
                return date_str
            except Exception:
                pass
        return "0000-00-00"
    
    all_news.sort(key=parse_date, reverse=True)
    
    return all_news, errors


if __name__ == "__main__":
    # 测试爬虫
    news, errors = scrape_all_universities()
    print(f"共获取 {len(news)} 条新闻")
    if errors:
        print(f"错误: {errors}")
    for item in news[:5]:
        print(f"[{item['source']}] {item['date']} - {item['title']}")

