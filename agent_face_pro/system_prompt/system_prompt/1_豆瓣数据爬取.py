import requests
import pandas as pd
import pymysql
import time #多次爬要用这个

def douban_data(start,limit):
    #  请求url
    url=f"https://movie.douban.com/j/chart/top_list?type=5&interval_id=100%3A90&action=&start={start}&limit={limit}"
    #定义请求头
    headers={"user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0"}
    # 发起get请求 得到响应
    response=requests.get(url,headers=headers)
    # 判断是否请求成功 状态码 200
    status=response.status_code
    print(status)
    #  获取数据 json():字典或者列表  text: 字符串 content: 字节
    # data=response.text
    # print(data)
    # data1=response.content
    # print(data1)
    data=response.json()
    # print(data,len(data))
    #创建一个空列表 装查询到的电影信息
    list_data=[]
    # 拿电影名称、评论数、评分
    for movie in data:
        movie_name=movie["title"]
        movie_score=movie["score"]
        movie_count=movie["vote_count"]
        print(f"电影名称：{movie_name} 评分：{movie_score} 评论数：{movie_count}")
        list_data.append([movie_name,movie_score,movie_count])
    # print(list_data)
    #把二维列表数据转换成dataframe
    df=pd.DataFrame(list_data,columns=["电影名称","评分","评论数"])
    print(df)
    #保存数据为csv文件
    df.to_csv("./doudan_action.csv",index=False)

if __name__ == '__main__':
    douban_data(1,10)