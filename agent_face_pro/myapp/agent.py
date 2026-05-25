from openai import OpenAI
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.tools import tool
import asyncio
import requests
from langchain_mcp_adapters.client import MultiServerMCPClient

#把相对路径改成绝对路径
#获取当前路径
current_path = os.path.dirname(__file__)
#print(current_path)

#路径拼接
env_path=os.path.join(current_path,".env")
#print(env_path)

load_dotenv(dotenv_path=env_path)

#1.获取环境变量
api_key=os.getenv("DEEPSEEK_API_KEY")
base_url=os.getenv("DEEPSEEK_BASE_URL")
model=os.getenv("DEEPSEEK_MODEL")

def load_system_prompt():
    prompt_path = os.path.join(current_path, "agent_prompt.md")
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"加载提示词失败: {e}，使用默认提示词")
        return "你是一个聪明的助手，请使用工具回答我的问题。"

# 导入服务函数
from myapp.services import (
    add_schedule as svc_add_schedule,
    get_schedules as svc_get_schedules,
    delete_schedule as svc_delete_schedule,
    add_expense as svc_add_expense,
    get_expenses as svc_get_expenses,
    translate_text as svc_translate_text,
    search_train_tickets as svc_search_train_tickets,
    search_flight_tickets as svc_search_flight_tickets,
    get_db_connection,
)
import pymysql

@tool
def add_schedule(user_phone: str, title: str, content: str, start_time: str, end_time: str = None, reminder_type: str = 'message') -> str:
    """添加用户日程。参数：user_phone(用户手机号), title(日程标题), content(日程内容), start_time(开始时间，格式YYYY-MM-DD HH:MM), end_time(结束时间，可选), reminder_type(提醒方式，默认message)"""
    result = svc_add_schedule(user_phone, title, content, start_time, end_time, reminder_type)
    if result.get('success'):
        return f"日程添加成功：{title}"
    return f"日程添加失败：{result.get('msg', '未知错误')}"

@tool
def get_schedules(user_phone: str, days: int = 7) -> str:
    """查询用户未来日程。参数：user_phone(用户手机号), days(查询天数，默认7天)"""
    result = svc_get_schedules(user_phone, days)
    if result.get('success'):
        schedules = result.get('schedules', [])
        if not schedules:
            return "暂无日程安排"
        output = f"未来{days}天日程安排：\n"
        for s in schedules:
            output += f"- {s['title']}：{s['start_time']} ~ {s['end_time'] or '未设置'}\n"
        return output
    return f"查询失败：{result.get('msg', '未知错误')}"

@tool
def delete_schedule(user_phone: str, schedule_id: int) -> str:
    """删除用户日程。参数：user_phone(用户手机号), schedule_id(日程ID)"""
    result = svc_delete_schedule(user_phone, schedule_id)
    if result.get('success'):
        return "日程删除成功"
    return f"删除失败：{result.get('msg', '未知错误')}"

@tool
def add_expense(user_phone: str, amount: float, category: str, description: str, expense_date: str = None) -> str:
    """添加消费记录。参数：user_phone(用户手机号), amount(金额), category(分类，如餐饮/交通/购物), description(描述), expense_date(消费日期，格式YYYY-MM-DD，可选)"""
    result = svc_add_expense(user_phone, amount, category, description, expense_date)
    if result.get('success'):
        return f"记账成功：{category} {amount}元"
    return f"记账失败：{result.get('msg', '未知错误')}"

@tool
def get_expenses(user_phone: str, month: str = None) -> str:
    """查询用户消费记录。参数：user_phone(用户手机号), month(月份，格式YYYY-MM，可选，不传则查询最近50条)"""
    result = svc_get_expenses(user_phone, month)
    if result.get('success'):
        expenses = result.get('expenses', [])
        total = result.get('total', 0)
        category_stats = result.get('category_stats', {})
        if not expenses:
            return "暂无消费记录"
        output = f"消费记录（总计：{total}元）：\n"
        output += "分类统计：\n"
        for cat, amt in category_stats.items():
            output += f"- {cat}：{amt}元\n"
        output += "最近消费：\n"
        for e in expenses[:10]:
            output += f"- {e['expense_date']} {e['category']} {e['amount']}元 {e['description']}\n"
        return output
    return f"查询失败：{result.get('msg', '未知错误')}"

@tool
def translate_text_tool(text: str, source_lang: str = 'zh', target_lang: str = 'en', user_phone: str = '') -> str:
    """翻译文本。参数：text(待翻译文本), source_lang(源语言代码：zh/en/ja/ko/fr/de), target_lang(目标语言代码), user_phone(用户手机号，可选)"""
    result = svc_translate_text(text, source_lang, target_lang, user_phone)
    if result.get('success'):
        return f"翻译结果：{result.get('translated', '')}"
    return f"翻译失败：{result.get('msg', '未知错误')}"

@tool
def search_train_tickets_tool(from_station: str, to_station: str, date: str = None) -> str:
    """查询火车票。参数：from_station(出发站), to_station(到达站), date(日期，格式YYYY-MM-DD，可选)"""
    result = svc_search_train_tickets(from_station, to_station, date)
    if result.get('success'):
        tickets = result.get('tickets', [])
        if not tickets:
            return f"未查询到 {from_station} 到 {to_station} 的车次信息"
        output = f"查询到 {len(tickets)} 趟列车：\n"
        for t in tickets:
            output += f"车次：{t['train_no']} {t['from']}→{t['to']} {t['start_time']}-{t['arrive_time']} 历时{t['duration']}\n"
            for seat in t.get('seat_types', []):
                output += f"  {seat['type']}：{seat['price']}元 ({seat['available']})\n"
        return output
    return f"查询失败：{result.get('msg', '未知错误')}"

@tool
def search_flight_tickets_tool(from_city: str, to_city: str, date: str = None) -> str:
    """查询机票。参数：from_city(出发城市), to_city(到达城市), date(日期，格式YYYY-MM-DD，可选)"""
    result = svc_search_flight_tickets(from_city, to_city, date)
    if result.get('success'):
        flights = result.get('flights', [])
        if not flights:
            return f"未查询到 {from_city} 到 {to_city} 的航班信息"
        output = f"查询到 {len(flights)} 个航班：\n"
        for f in flights:
            output += f"航班：{f.get('flight_no', '')} {f.get('airline', '')} {f.get('start_time', '')}-{f.get('arrive_time', '')} 历时{f.get('duration', '')}\n"
            output += f"  价格：{f.get('price', '')}元\n"
        return output
    return f"查询失败：{result.get('msg', '未知错误')}"

@tool
def get_database(sql: str) -> str:
    """执行数据库查询（只读）。参数：sql(SQL查询语句，只能使用SELECT)。注意：查询用户数据时必须包含user_phone条件。"""
    # 安全检查：只允许SELECT语句
    sql_upper = sql.strip().upper()
    if not sql_upper.startswith('SELECT'):
        return "错误：只允许执行SELECT查询语句"
    
    # 禁止危险操作
    dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE']
    for keyword in dangerous_keywords:
        if keyword in sql_upper:
            return f"错误：禁止使用 {keyword} 操作"
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(sql)
        
        # 获取列名
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        
        if not rows:
            return "查询结果为空"
        
        # 格式化为表格
        output = f"查询结果（共{len(rows)}条）：\n"
        output += " | ".join(columns) + "\n"
        output += "-" * 50 + "\n"
        for row in rows[:50]:  # 限制最多返回50条
            output += " | ".join([str(v) for v in row]) + "\n"
        
        if len(rows) > 50:
            output += f"\n... 还有 {len(rows) - 50} 条数据未显示"
        
        return output
    except Exception as e:
        return f"数据库查询失败：{str(e)}"
    finally:
        if conn:
            conn.close()
# client=OpenAI(
#     api_key=api_key,
#     base_url=base_url,
# )
#
# #3.使用模型进行推理
# completion=client.chat.completions.create(
#     model=model,
#     messages=[{"role":"system","content":"你是一个智能助手，请回答我的问题。"},
#               {"role":"user","content":"你是谁？"}]
# )
#
# #推理结果
# result = completion.choices[-1].message.content
# print(result)



def load_llm():
    #创建模型对象
    llm=ChatOpenAI(model=model,api_key=api_key,base_url=base_url)
    return llm

#创建MCP客户端对象
mcp_client=MultiServerMCPClient({
    "my_mcp_server":{# 服务名，想怎么取就怎么取
        "url":"http://127.0.0.1:8081/mcp",# 自定义MCP服务（天气、年龄等工具）
        "transport":"streamable-http"# 固定写法，指定传输协议
    },
    "my_12306_mcp_server":{
        "url":"http://127.0.0.1:8082/mcp",# 12306的mcp服务地址（火车票工具）
        "transport":"streamable-http"# 12306的mcp服务地址
    }
})

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
    url = f"https://api.seniverse.com/v3/weather/now.json?key=SbeLLdVlSHkjahorO&location={city}&language=zh-Hans&unit=c"
    res=requests.get(url)
    return res.json()

#查询汽车尾号限行
# def get_car_limit(city: str) -> str:
#     """
#     查询城市今日机动车尾号限行信息
#     参数: city (城市名, 如: 贵阳)
#     返回: 限行结果或错误信息
#     """
#     print("查询汽车尾号限行工具函数被调用")
#
#     # 你的心知天气API Key
#     API_KEY = "S7rF024-FAtNVkx1q"  # 换成你自己的
#     url = "https://api.seniverse.com/v3/life/driving_restriction.json"
#
#     params = {
#         "key": API_KEY,
#         "location": city  # 支持: 北京/天津/哈尔滨/成都/杭州/贵阳/长春/兰州
#     }
#
#     try:
#         res = requests.get(url, params=params, timeout=10)
#         data = res.json()
#
#         # ❌ 错误处理：权限/Key错误
#         if data.get("status_code") == "AP010002":
#             return f"⚠️ 权限错误：你的API Key未开通「尾号限行」接口，请在心知控制台开通"
#         if data.get("status_code"):
#             return f"⚠️ API错误：{data.get('status')} ({data.get('status_code')})"
#
#         # ✅ 成功解析
#         if "results" in data and len(data["results"]) > 0:
#             restriction = data["results"][0]["restriction"]
#             return (
#                 f"{city}今日限行\n"
#                 f"尾号：{restriction.get('number', '无')}\n"
#                 f"区域：{restriction.get('area', '全城')}\n"
#                 f"时间：{restriction.get('time', '工作日')}"
#             )
#         return f"{city} 暂无限行数据"
#
#     except Exception as e:
#         return f"⚠️ 请求失败：{str(e)}"



async def load_agent():
    llm=load_llm()
    mcp_tools=await mcp_client.get_tools()
    
    # 自定义工具列表
    custom_tools = [
        add_schedule,
        get_schedules,
        delete_schedule,
        add_expense,
        get_expenses,
        translate_text_tool,
        search_train_tickets_tool,
        search_flight_tickets_tool,
        get_database,
    ]
    
    # 合并 MCP 工具和自定义工具
    all_tools = mcp_tools + custom_tools
    
    system_prompt = load_system_prompt()
    agent=create_agent(model=llm,tools=all_tools,system_prompt=system_prompt)
    return agent

if __name__ == '__main__':
    # llm=load_llm()
    # # #使用模型对象进行预测
    # # result=llm.invoke("你是谁？")
    # # print(result.content)
    #
    # #使用大模型进行流式推理（每次都生成一个词 得到生成器对象 迭代这个对象得到每个词token）
    # res_stream=llm.stream("你是谁？")
    # for chunk in res_stream:
    #     print(chunk.content,end="")

    async def test():
        agent =await load_agent()
        # msg={"messages":[{"role":"user","content":"你是谁？"}]}
        msg = {"messages": [{"role": "user", "content": "从贵阳去成都的路线？"}]}
        # msg = {"messages": [{"role": "user", "content": "贵阳今天那些机动车尾号限行？"}]}
        result = await agent.ainvoke(msg)
        print(result["messages"][-1].content)
    #test()
    asyncio.run(test())

    # res=get_age("李四")
    # print(res)
    # res=get_car("贵阳")
    # print(res)
