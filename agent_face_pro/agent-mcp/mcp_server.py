# 引入mcp服务需要的工具类
from fastmcp import FastMCP
import requests

#创建服务器对象
mcp_server=FastMCP("标题：自己使用的",instructions="描述：自己使用的")

@mcp_server.tool
#根据姓名查询年龄
def get_age(name:str):
    """
    这个函数是根据姓名查询年龄的工具
    参数：
        name：字符串
    返回值：
        用户的年龄
    """
    # data={"张三":23,"李四":24,"王五":25,"赵六":26}
    print(f"查询用户年龄的工具函数被调用了")
    data=[{"name":"张三","age":23},
          {"name":"李四","age":24},
          {"name":"王五","age":25},
          {"name":"赵六","age":26}]
    for item in data:
        if name==item["name"]:
            return f"用户姓名是{name}，年龄是{item['age']}"
    else:
        return "没有这个用户"

@mcp_server.tool
#根据城市名查询天气
def get_weather(city:str):
    """
    这个函数是根据城市名查询天气的工具
    参数：
        city：字符串
    返回值：
        天气情况
    """
    print(f"查询天气的工具函数被调用了")
    # data=[{"city":"成都","weather":"晴天"},
    #       {"city":"上海","weather":"阴天"},
    #       {"city":"广州","weather":"雨天"},
    #       {"city":"深圳","weather":"多云天"}]
    # for item in data:
    #     if item["city"] in city:
    #         return f"用户所在的城市是{city}，天气情况是{item["weather"]}"
    # else:
    #     return f"没有这个城市相关信息"
    url = f"https://api.seniverse.com/v3/weather/now.json?key=SjghS28FoSYkm3t8M&location={city}&language=zh-Hans&unit=c"
    res=requests.get(url)
    return str(res.json())


if __name__ == '__main__':
    # 还需要配置协议
    mcp_server.run(transport="streamable-http",port=8081)