import requests
from bs4 import BeautifulSoup
import time
import pymysql


def crawl_chinanews():
    """爬取中国新闻网新闻数据"""

    # 目标URL - 滚动新闻（已失效，改用新浪新闻）
    url = "https://news.sina.com.cn/"

    # 设置请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Connection': 'keep-alive'
    }

    try:
        print(f"正在访问: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'

        if response.status_code != 200:
            print(f"请求失败，状态码: {response.status_code}")
            return []

        # 解析页面
        soup = BeautifulSoup(response.text, 'html.parser')

        # 提取新闻信息（根据新浪新闻的HTML结构调整选择器）
        news_list = []

        # 尝试多种选择器来提取新闻
        news_items = soup.select('.news-item, .list_009 li, .blkContainerSblkCon li, a[href*="news.sina"]')

        print(f"找到 {len(news_items)} 条新闻链接")

        for item in news_items[:30]:  # 只取前30条
            try:
                title = ''
                link = ''

                # 如果当前元素是a标签
                if item.name == 'a':
                    title = item.get_text(strip=True)
                    link = item.get('href', '')
                else:
                    # 否则查找其中的a标签
                    title_elem = item.select_one('a')
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        link = title_elem.get('href', '')

                # 清理标题和链接
                if title and len(title) > 5:  # 过滤太短的标题
                    # 确保链接是完整的
                    if link and not link.startswith('http'):
                        if link.startswith('//'):
                            link = 'https:' + link
                        elif link.startswith('/'):
                            link = 'https://news.sina.com.cn' + link

                    # 只保留新浪新闻的链接
                    if 'sina.com.cn' in link or 'sina.cn' in link:
                        news_list.append({
                            'title': title[:200],  # 限制标题长度
                            'link': link,
                            'pub_time': time.strftime('%Y-%m-%d %H:%M', time.localtime()),
                            'category': '综合'
                        })

            except Exception as e:
                print(f"处理新闻时出错: {e}")
                continue

        # 去重（基于标题）
        seen_titles = set()
        unique_news = []
        for news in news_list:
            if news['title'] not in seen_titles:
                seen_titles.add(news['title'])
                unique_news.append(news)

        print(f"成功提取 {len(unique_news)} 条唯一新闻")
        return unique_news

    except Exception as e:
        print(f"爬取失败: {e}")
        return []


def save_news_to_database(news_list):
    """将新闻数据保存到数据库"""
    try:
        conn = pymysql.connect(
            host='localhost',
            port=3306,
            user='root',
            password='123456',  # 改成你的密码
            database='gzeu_sql',
            charset='utf8mb4'
        )

        cursor = conn.cursor()

        # 创建新闻表
        create_table_sql = """
            CREATE TABLE IF NOT EXISTS news_info (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(200),
                category VARCHAR(50),
                pub_time VARCHAR(50),
                link VARCHAR(500),
                created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_link (link)
            )
        """
        cursor.execute(create_table_sql)

        # 插入数据（使用INSERT IGNORE避免重复）
        insert_sql = """
            INSERT IGNORE INTO news_info (title, category, pub_time, link)
            VALUES (%s, %s, %s, %s)
        """

        success_count = 0
        for news in news_list:
            try:
                data = (
                    news['title'],
                    news['category'],
                    news['pub_time'],
                    news['link']
                )
                cursor.execute(insert_sql, data)
                if cursor.rowcount > 0:
                    success_count += 1
            except Exception as e:
                print(f"插入失败: {e}")
                continue

        conn.commit()
        print(f"成功插入 {success_count} 条新闻数据")

    except Exception as e:
        print(f"数据库操作失败: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


if __name__ == '__main__':
    # 爬取新闻
    print("=" * 60)
    print("开始爬取新闻数据...")
    print("=" * 60)
    news_list = crawl_chinanews()

    # 显示结果
    if news_list:
        print("\n" + "=" * 60)
        print("爬取到的前10条新闻:")
        print("=" * 60)
        for i, news in enumerate(news_list[:10], 1):
            print(f"{i}. {news['title']}")
            print(f"   分类: {news['category']} | 时间: {news['pub_time']}")
            print(f"   链接: {news['link']}")
            print("-" * 60)

        # 保存到数据库
        print("\n" + "=" * 60)
        print("保存数据到数据库...")
        print("=" * 60)
        save_news_to_database(news_list)
    else:
        print("\n未获取到任何新闻数据")
