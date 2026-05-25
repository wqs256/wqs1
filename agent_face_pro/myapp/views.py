import json
import os
import re
import time
import cv2 as cv
try:
    import face_recognition
    FACE_AVAILABLE = True
except:
    FACE_AVAILABLE = False
import pymysql
import csv
import io
from datetime import datetime, timedelta

from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from myapp.util.ImageUtil import *
from myapp.util.RandomUtil import *
from myapp.agent import load_agent, load_llm

"""
JsonResponse:返回json数据
HttpResponse:返回http响应
render:返回页面 .html  同是还可以携带参数
redirect:重定向
"""

face_save_path = 'C:/Users/33772/Desktop/langchian/agent_face_pro (2)/agent_face_pro/myapp/static/imgs/'


# 返回人脸采集页面
def return_collect_page(request):
    return render(request, "collect_page.html")


# 返回人脸匹配页面
def return_detect_page(request):
    return render(request, "detect_page.html")


# 处理人脸信息采集
def face_collect(request):
    if request.method == 'POST':
        try:
            print("开始处理人脸采集请求...")

            video_image = cv.cvtColor(get_image_array(request), cv.COLOR_BGR2RGB)
            print("图片矩阵获取成功")

            video_location = face_recognition.face_locations(video_image)
            print(f"检测到 {len(video_location)} 个人脸")

            if len(video_location) == 0:
                return JsonResponse({
                    'status_code': 500,
                    'status_msg': '未检测到人脸，请确保正对摄像头',
                })

            video_encoding = face_recognition.face_encodings(video_image, video_location)

            file_list = os.listdir(face_save_path)
            for file_name in file_list:
                if not file_name.endswith('.jpg') and not file_name.endswith('.png'):
                    continue

                file_path = face_save_path + file_name
                dir_image = face_recognition.load_image_file(file_path)
                dir_location = face_recognition.face_locations(dir_image)


                if len(dir_location) == 0:
                    continue

                dir_encoding = face_recognition.face_encodings(dir_image, dir_location)

                if len(dir_encoding) == 0:
                    continue

                compare = face_recognition.compare_faces(dir_encoding, video_encoding[0], tolerance=0.5)

                if True in compare:
                    return JsonResponse({
                        'status_code': 500,
                        'status_msg': '已存在该人脸，请勿重复采集',
                    })

            name_id = generate_unique_random(1, 100)
            video_byte = get_image_byte(request)
            video_save_path = face_save_path + str(name_id) + '.jpg'

            print(f"图片保存成功：{video_save_path}")

            data = json.loads(request.body.decode('utf-8'))
            print(f"用户信息：{data}")
            name = data['name']
            age = data['age']
            print(f"")
            phone = data['phone']
            password = data.get('password', '')
            print(f"用户信息：{name}，{age}岁，{phone}，{password}")

            result_pwd = check_password(password)
            if result_pwd == False:
                return JsonResponse({
                    'status_code': 500,
                    'status_msg': '密码格式错误，请重新输入',
                })

            # 判断年龄范围是否有问题
            result_age = check_age(age)
            if result_age[0] == False:
                return JsonResponse({
                    'status_code': 500,
                    'status_msg': '年龄格式错误，请重新输入',
                })

            result_phone = check_phone(phone)
            if result_phone[0] == False:
                return JsonResponse({
                    'status_code': 500,
                    'status_msg': f"手机号格式错误或已存在，请检查后重试{result_phone[1]}"
                })

            result = info_insert(name_id, name, age, phone, password)
            if result:
                with open(video_save_path, 'wb') as f:
                    f.write(video_byte)
                print("用户信息插入成功")
                return JsonResponse({
                    'status_code': 200,
                    'status_msg': '采集成功',
                })
            else:
                print("用户信息插入失败")
                return JsonResponse({
                    'status_code': 500,
                    'status_msg': '数据库插入失败，请检查数据库连接',
                })
        except Exception as e:
            print(f"发生错误: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'status_code': 500,
                'status_msg': f'处理失败: {str(e)}',
            })

    return JsonResponse({
        'status_code': 405,
        'status_msg': '请求方法不允许',
    })


# 处理人脸匹配
def face_detect(request):
    if request.method == 'POST':
        try:
            # 【修复】每次请求都重新加载文件列表
            file_list = os.listdir(face_save_path)

            video_image = get_image_array(request)
            video_image = cv.cvtColor(video_image, cv.COLOR_BGR2RGB)
            video_location = face_recognition.face_locations(video_image)

            if len(video_location) == 0:
                return JsonResponse({
                    'status': 500,
                    'msg': '没有检测到人脸'
                })

            video_encoding = face_recognition.face_encodings(video_image)[0]

            for file_name in file_list:
                if not file_name.endswith('.jpg') and not file_name.endswith('.png'):
                    continue

                file_path = face_save_path + file_name
                print(f"当前文件的路径是：{file_path}")

                try:
                    dir_image = face_recognition.load_image_file(file_path)
                    dir_location = face_recognition.face_locations(dir_image)

                    if len(dir_location) == 0:
                        print(f"{file_path} 中未检测到人脸，跳过")
                        continue

                    dir_encoding = face_recognition.face_encodings(dir_image)[0]
                    compare_result = face_recognition.compare_faces([dir_encoding], video_encoding, tolerance=0.5)[0]
                    print(f"比较结果：{compare_result}")

                    if compare_result:
                        print(f"当前匹配上的文件是：{file_name}")
                        user_id = int(file_name.split('.')[0])
                        print(f"查询用户的id是：{user_id}")

                        result = info_select(user_id)
                        if result and len(result) > 0:
                            user_info = result[0]
                            return JsonResponse({
                                "status": 200,
                                "username": user_info[1],
                                "user_phone": user_info[3],
                                "msg": f"人脸匹配成功，匹配上的用户是：{user_info[1]}，年龄为{user_info[2]}岁，电话号码为：{user_info[3]}",
                            })
                        else:
                            return JsonResponse({
                                "status": 500,
                                "msg": f"匹配的图像文件是{file_name}，但数据库没有该信息"
                            })
                except Exception as e:
                    print(f"处理 {file_name} 时出错: {e}")
                    continue

            return JsonResponse({
                "status": 500,
                "msg": "没有匹配的人脸",
            })
        except Exception as e:
            print(f"人脸检测异常: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'status': 500,
                'msg': f'检测失败: {str(e)}'
            })

    return JsonResponse({
        'status': 405,
        'msg': '请求方法不对',
    })


# 数据库插入用户信息
def info_insert(id, name, age, phone, password=''):
    conn = None
    try:
        conn = pymysql.connect(
            host="localhost",
            port=3306,
            user="root",
            password="123456",
            database="gzeu_sql",
            charset="utf8"
        )
        cursor = conn.cursor()
        sql = "insert into user_info(id,user_name,user_age,user_phone,user_pwd) values (%s,%s,%s,%s,%s)"
        cursor.execute(sql, (id, name, age, phone, password))
        conn.commit()
        print("用户信息插入成功")
        return True
    except Exception as e:
        print(f"数据库错误: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


# 数据库查询用户信息
def info_select(id=None, phone=None):
    conn = None
    try:
        conn = pymysql.connect(
            host="localhost",
            port=3306,
            user="root",
            password="123456",
            database="gzeu_sql",
            charset="utf8"
        )
        cursor = conn.cursor()

        # 根据传入的参数动态构建 SQL
        if id is not None and phone is not None:
            sql = "SELECT * FROM user_info WHERE id=%s OR user_phone=%s"
            cursor.execute(sql, (id, phone))
        elif id is not None:
            sql = "SELECT * FROM user_info WHERE id=%s"
            cursor.execute(sql, (id,))
        elif phone is not None:
            sql = "SELECT * FROM user_info WHERE user_phone=%s"
            cursor.execute(sql, (phone,))
        else:
            print("警告：未提供查询参数")
            return ()

        result = cursor.fetchall()
        print(f"数据库查询结果为：{result}")
        return result
    except Exception as e:
        print(f"数据查询失败: {e}")
        return ()
    finally:
        if conn:
            conn.close()


# 检查密码 6-20位数字+英文
def check_password(pwd):
    # 【修复】返回值统一为布尔值
    if len(pwd) < 6 or len(pwd) > 20:
        return False
    has_letter = bool(re.search(r'[a-zA-Z]', pwd))
    has_digit = bool(re.search(r'\d', pwd))
    return has_letter and has_digit


# 检查年龄 范围是0-150岁
def check_age(age):
    try:
        age_int = int(age)
    except (ValueError, TypeError):
        return [False, "年龄格式错误，请输入数字"]
    if age_int < 0 or age_int > 150:
        return [False, "年龄范围应该是0-150岁"]
    return [True, ""]


# 检查电话1开头 11位 和数据库采集过的结果不重复
def check_phone(phone):
    check_digit = bool(re.search(r'^1\d{10}$', phone))
    if check_digit == False:
        return [False, "手机号以1开头，11位数字"]
    result = info_select(phone=phone)
    if len(result) == 0:
        return [True]
    return [False, "该手机号已被注册"]


def login(request):
    if request.method == 'GET':
        return render(request, "login_page.html")
    user = request.POST.get("user")
    password = request.POST.get("pwd")
    result = info_select(phone=user)
    if len(result) == 0:
        return render(request, "login_page.html", {"msg": "该用户不存在"})
    if result[0][4] != password:
        return render(request, "login_page.html", {"msg": "密码错误"})
    from django.shortcuts import redirect
    return redirect(f'/profile_page/?username={result[0][1]}&phone={result[0][3]}')


def stream_fake():
    yield "data: 我是\n\n"
    time.sleep(1)
    yield "data: 人工\n\n"
    time.sleep(1)
    yield "data: 智能\n\n"
    yield "data: [DONE]\n\n"


def chat_stream(request):
    q_msg = request.GET.get("q")
    print(f"前端发来的数据是：{q_msg}")
    return StreamingHttpResponse(stream_fake(), content_type="text/event-stream")


def stream_llm_chat(q: str):
    llm = load_llm()
    for chunk in llm.stream(q):
        yield f"data: {chunk.content}\n\n"
    yield "data: [DONE]\n\n"


def chat_stream_llm(request):
    q_msg = request.GET.get("q")
    print(f"前端发来的数据是：{q_msg}")
    response = StreamingHttpResponse(stream_llm_chat(q_msg), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["Connection"] = "keep-alive"
    response["X-Accel-Buffering"] = "no"
    return response


def is_tool_data(content):
    """判断是否是工具调用的原始数据"""
    if not isinstance(content, str):
        return False
    tool_markers = ["'type': 'text'", "'results':", "'location':", "'timezone':", "'last_update':", "'id': 'lc_"]
    return any(marker in content for marker in tool_markers)


def flatten_to_str(obj):
    """将任意嵌套结构扁平化为字符串"""
    if obj is None:
        return ""
    if isinstance(obj, str):
        return obj
    if isinstance(obj, (int, float, bool)):
        return str(obj)
    if isinstance(obj, list):
        return ''.join(flatten_to_str(item) for item in obj)
    if isinstance(obj, dict):
        # 跳过工具调用数据
        if obj.get("type") in ["tool_call", "tool", "text"]:
            return ""
        # 优先提取常见文本字段
        for key in ['content', 'text', 'value', 'output', 'result', 'message']:
            if key in obj:
                return flatten_to_str(obj[key])
        # 如果没有找到常见字段，返回空
        return ""
    return str(obj)


def clean_tool_data(content):
    """清理内容中的工具调用原始数据"""
    if content is None:
        return None
    
    # 使用 flatten_to_str 处理所有类型
    content = flatten_to_str(content)
    
    if not isinstance(content, str):
        return content
    
    import re
    
    # 如果整段内容都是工具调用数据，直接返回None
    if content.strip().startswith("[{'type': 'text'") and content.strip().endswith("}]"):
        return None
    if content.strip().startswith('[{"type": "text"') and content.strip().endswith("}]"):
        return None
    
    # 移除嵌入在文本中的工具数据块
    # 注意：text字段的值是用双引号包裹的，里面可能包含单引号
    # 匹配模式：[{'type': 'text', 'text': "...", 'id': 'lc_xxx'}]
    pattern = r"\[\{'type':\s*'text',\s*'text':\s*\"[^\"]*\"\s*,\s*'id':\s*'lc_[^']*'\}\]"
    content = re.sub(pattern, '', content, flags=re.DOTALL)
    
    # 也匹配 text 字段用单引号包裹的版本
    pattern1b = r"\[\{'type':\s*'text',\s*'text':\s*'[^']*'\s*,\s*'id':\s*'lc_[^']*'\}\]"
    content = re.sub(pattern1b, '', content, flags=re.DOTALL)
    
    # 也匹配双引号版本
    pattern2 = r'\[\{"type":\s*"text",\s*"text":\s*"[^"]*"\s*,\s*"id":\s*"lc_[^"]*"\}\]'
    content = re.sub(pattern2, '', content, flags=re.DOTALL)
    
    # 清理多余的空格
    content = re.sub(r'\s+', ' ', content).strip()
    
    return content if content else None


def extract_content(chunk):
    """从复杂的 chunk 结构中提取 content，过滤工具调用数据"""
    if chunk is None:
        return None
    
    # 1. 处理对象（如 AIMessage）
    if hasattr(chunk, "content") and chunk.content:
        content = chunk.content
        content = clean_tool_data(content)
        if not content:
            return None
        return content
    
    # 2. 处理字典
    if isinstance(chunk, dict):
        if chunk.get("type") in ["tool_call", "tool", "text"]:
            return None
        if "content" in chunk:
            content = chunk["content"]
            content = clean_tool_data(content)
            if not content:
                return None
            return content
        if "messages" in chunk:
            for msg in chunk["messages"]:
                content = extract_content(msg)
                if content:
                    return content
        if "model" in chunk:
            return extract_content(chunk["model"])
        if "update" in chunk:
            return extract_content(chunk["update"])
    
    # 3. 处理列表 - 跳过包含工具数据的项
    if isinstance(chunk, list):
        for item in chunk:
            if isinstance(item, dict) and item.get("type") in ["text", "tool", "tool_call"]:
                continue
            content = extract_content(item)
            if content:
                return content
    
    return None


# 【核心修复】异步生成器，严格遵循SSE格式
async def chat_stream_agent(q: str):
    agent = await load_agent()
    msg = {"messages": [{"role": "user", "content": q}]}
    async for event in agent.astream_events(msg, version="v2"):
        if event["event"] in ["on_chat_model_stream", "on_chain_stream"]:
            chunk = event["data"].get("chunk")
            content = extract_content(chunk)
            if content:
                yield f"data: {content}\n\n"
    yield "data: [DONE]\n\n"


# 【核心修复】异步视图 + 正确响应头
def chat_agent_page(request):
    username = request.GET.get("username", "用户")
    return render(request, "chat_agent.html", {"username": username})


async def chat_agent(request):
    q_msg = request.GET.get("q")
    print(f"前端发来的数据是：{q_msg}")

    response = StreamingHttpResponse(
        chat_stream_agent(q_msg),
        content_type="text/event-stream"
    )
    response["Cache-Control"] = "no-cache"
    response["Connection"] = "keep-alive"
    response["X-Accel-Buffering"] = "no"
    return response


# ==================== 个人助理与生活服务系统 ====================

from myapp.services import (
    add_schedule, get_schedules, delete_schedule,
    add_expense, get_expenses, delete_expense,
    translate_text,
    search_train_tickets, search_flight_tickets,
    get_user_info_by_phone
)


def assistant_page(request):
    username = request.GET.get("username", "用户")
    user_phone = request.GET.get("phone", "")
    return render(request, "assistant_page.html", {"username": username, "user_phone": user_phone})


def schedule_add(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        user_phone = data.get('user_phone', '')
        title = data.get('title', '')
        content = data.get('content', '')
        start_time = data.get('start_time', '')
        end_time = data.get('end_time', None)
        reminder_type = data.get('reminder_type', 'message')
        result = add_schedule(user_phone, title, content, start_time, end_time, reminder_type)
        return JsonResponse(result)
    return JsonResponse({'success': False, 'msg': '请求方法错误'})


def schedule_list(request):
    user_phone = request.GET.get('user_phone', '')
    days = int(request.GET.get('days', 7))
    result = get_schedules(user_phone, days)
    return JsonResponse(result)


def schedule_delete(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        user_phone = data.get('user_phone', '')
        schedule_id = data.get('id', 0)
        result = delete_schedule(user_phone, schedule_id)
        return JsonResponse(result)
    return JsonResponse({'success': False, 'msg': '请求方法错误'})


def expense_add(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        user_phone = data.get('user_phone', '')
        amount = data.get('amount', 0)
        category = data.get('category', '其他')
        description = data.get('description', '')
        expense_date = data.get('expense_date', None)
        income_type = data.get('income_type', 'expense')
        result = add_expense(user_phone, amount, category, description, expense_date, income_type)
        return JsonResponse(result)
    return JsonResponse({'success': False, 'msg': '请求方法错误'})


def expense_list(request):
    user_phone = request.GET.get('user_phone', '')
    month = request.GET.get('month', None)
    result = get_expenses(user_phone, month)
    return JsonResponse(result)

def expense_delete(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        user_phone = data.get('user_phone', '')
        expense_id = data.get('expense_id', 0)
        result = delete_expense(user_phone, expense_id)
        return JsonResponse(result)
    return JsonResponse({'success': False, 'msg': '请求方法错误'})


def translate_api(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        text = data.get('text', '')
        source_lang = data.get('source_lang', 'zh')
        target_lang = data.get('target_lang', 'en')
        user_phone = data.get('user_phone', '')
        result = translate_text(text, source_lang, target_lang, user_phone)
        return JsonResponse(result)
    return JsonResponse({'success': False, 'msg': '请求方法错误'})


def train_ticket_search(request):
    from_station = request.GET.get('from', '')
    to_station = request.GET.get('to', '')
    date = request.GET.get('date', None)
    result = search_train_tickets(from_station, to_station, date)
    return JsonResponse(result)


def flight_ticket_search(request):
    from_city = request.GET.get('from', '')
    to_city = request.GET.get('to', '')
    date = request.GET.get('date', None)
    result = search_flight_tickets(from_city, to_city, date)
    return JsonResponse(result)


async def smart_qa(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        question = data.get('question', '')
        user_phone = data.get('user_phone', '')
        try:
            from myapp.services import get_user_info_by_phone
            user_info = get_user_info_by_phone(user_phone)
            user_name = user_info.get('user', {}).get('name', '用户') if user_info.get('success') else '用户'
            
            agent = await load_agent()
            
            # 直接发送用户问题，agent 已包含系统提示词
            user_msg = f"""当前用户：{user_name}（手机号：{user_phone}）

用户问题：{question}

注意：所有操作都必须使用手机号 {user_phone}"""
            
            msg = {"messages": [{"role": "user", "content": user_msg}]}
            answer = ""
            async for event in agent.astream_events(msg, version="v2"):
                if event["event"] in ["on_chat_model_stream", "on_chain_stream"]:
                    chunk = event["data"].get("chunk")
                    content = extract_content(chunk)
                    if content and isinstance(content, str):
                        answer += content
            
            # 检查回答中是否包含图表标记
            chart_data = None
            import re
            chart_pattern = r'\[CHART:(\w+):(\w+):(\d+)\]'
            match = re.search(chart_pattern, answer)
            if match:
                chart_type = match.group(1)
                data_source = match.group(2)
                days = int(match.group(3))
                
                # 移除标记
                answer = re.sub(chart_pattern, '', answer).strip()
                
                # 获取图表数据
                if data_source == 'expense':
                    chart_response = analyze_expense_data(user_phone, days, chart_type)
                elif data_source == 'schedule':
                    chart_response = analyze_schedule_data(user_phone, days, chart_type)
                else:
                    chart_response = None
                
                if chart_response:
                    try:
                        chart_data = json.loads(chart_response.content)
                        if not chart_data.get('success'):
                            chart_data = None
                    except:
                        chart_data = None
            
            return JsonResponse({
                'success': True, 
                'answer': answer,
                'chart_data': chart_data
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'msg': f'回答失败: {str(e)}'})
    return JsonResponse({'success': False, 'msg': '请求方法错误'})


# ==================== 数据分析功能 ====================

@csrf_exempt
def data_analysis_db(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'msg': '请求方法错误'})
    
    try:
        data = json.loads(request.body.decode('utf-8'))
        user_phone = data.get('user_phone', '')
        data_source = data.get('data_source', 'expense')
        chart_type = data.get('chart_type', 'bar')
        time_range = int(data.get('time_range', 30))
        
        if data_source == 'expense':
            return analyze_expense_data(user_phone, time_range, chart_type)
        elif data_source == 'schedule':
            return analyze_schedule_data(user_phone, time_range, chart_type)
        else:
            return JsonResponse({'success': False, 'msg': '不支持的数据源'})
    except Exception as e:
        return JsonResponse({'success': False, 'msg': f'分析失败：{str(e)}'})


# 返回个人主页页面
def profile_page(request):
    username = request.GET.get('username', '用户')
    user_phone = request.GET.get('phone', '')
    return render(request, "profile_page.html", {"username": username, "user_phone": user_phone})


# 修改密码
def change_password(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'msg': '请求方法错误'})
    
    try:
        data = json.loads(request.body.decode('utf-8'))
        user_phone = data.get('user_phone', '')
        old_password = data.get('old_password', '')
        new_password = data.get('new_password', '')
        
        if not user_phone or not old_password or not new_password:
            return JsonResponse({'success': False, 'msg': '参数不完整'})
        
        # 查询用户信息
        result = info_select(phone=user_phone)
        if len(result) == 0:
            return JsonResponse({'success': False, 'msg': '用户不存在'})
        
        # 验证原密码
        if result[0][4] != old_password:
            return JsonResponse({'success': False, 'msg': '原密码错误'})
        
        # 更新密码
        conn = None
        try:
            conn = pymysql.connect(
                host="localhost",
                port=3306,
                user="root",
                password="123456",
                database="gzeu_sql",
                charset="utf8"
            )
            cursor = conn.cursor()
            sql = "UPDATE user_info SET user_pwd=%s WHERE user_phone=%s"
            cursor.execute(sql, (new_password, user_phone))
            conn.commit()
            return JsonResponse({'success': True, 'msg': '密码修改成功'})
        except Exception as e:
            return JsonResponse({'success': False, 'msg': f'数据库更新失败：{str(e)}'})
        finally:
            if conn:
                conn.close()
    except Exception as e:
        return JsonResponse({'success': False, 'msg': f'修改失败：{str(e)}'})


def analyze_expense_data(user_phone, days, chart_type):
    conn = None
    try:
        conn = pymysql.connect(
            host="localhost",
            port=3306,
            user="root",
            password="123456",
            database="gzeu_sql",
            charset="utf8"
        )
        cursor = conn.cursor()
        
        pie_chart_types = ['pie', 'funnel', 'radar', 'gauge']
        
        if chart_type in pie_chart_types:
            sql = """
                SELECT category, SUM(amount) as total 
                FROM user_expense 
                WHERE user_phone = %s 
                AND expense_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                GROUP BY category 
                ORDER BY total DESC
            """
            cursor.execute(sql, (user_phone, days))
        else:
            sql = """
                SELECT DATE(expense_date) as date, SUM(amount) as total 
                FROM user_expense 
                WHERE user_phone = %s 
                AND expense_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                GROUP BY DATE(expense_date) 
                ORDER BY date
            """
            cursor.execute(sql, (user_phone, days))
        
        results = cursor.fetchall()
        
        if not results:
            return JsonResponse({'success': False, 'msg': '暂无数据'})
        
        x_data = []
        y_data = []
        
        if chart_type in pie_chart_types:
            for row in results:
                x_data.append(str(row[0]))
                y_data.append(float(row[1]))
            title = f'近{days}天消费分类统计'
            y_label = '消费金额'
            
            total = sum(y_data)
            analysis_text = f'## 近{days}天消费分析报告\n\n'
            analysis_text += f'### 总体概况\n'
            analysis_text += f'- **总消费金额**：¥{total:.2f}\n'
            analysis_text += f'- **消费类别数**：{len(x_data)} 个\n'
            analysis_text += f'- **最高消费类别**：{x_data[0]}（¥{y_data[0]:.2f}，占比 {y_data[0]/total*100:.1f}%）\n\n'
            
            analysis_text += f'### 各类别消费详情\n'
            for i, (cat, amount) in enumerate(zip(x_data, y_data)):
                percent = amount/total*100
                analysis_text += f'{i+1}. **{cat}**：¥{amount:.2f}（{percent:.1f}%）\n'
            
            analysis_text += f'\n### 消费建议\n'
            if len(x_data) > 1:
                highest_cat = x_data[0]
                highest_amount = y_data[0]
                if highest_amount > total * 0.5:
                    analysis_text += f'- {highest_cat}消费占比较高（{highest_amount/total*100:.1f}%），建议适当控制\n'
                else:
                    analysis_text += f'- 消费分布相对均衡，{highest_cat}略高，可关注其他类别\n'
        else:
            for row in results:
                x_data.append(str(row[0]))
                y_data.append(float(row[1]))
            title = f'近{days}天消费趋势'
            y_label = '消费金额（元）'
            total = sum(y_data)
            avg = total / len(y_data) if y_data else 0
            max_day = x_data[y_data.index(max(y_data))] if y_data else '无'
            min_day = x_data[y_data.index(min(y_data))] if y_data else '无'
            
            analysis_text = f'## 近{days}天消费趋势分析\n\n'
            analysis_text += f'### 总体概况\n'
            analysis_text += f'- **总消费金额**：¥{total:.2f}\n'
            analysis_text += f'- **日均消费**：¥{avg:.2f}\n'
            analysis_text += f'- **有消费记录天数**：{len(x_data)} 天\n'
            analysis_text += f'- **最高消费日**：{max_day}（¥{max(y_data):.2f}）\n'
            analysis_text += f'- **最低消费日**：{min_day}（¥{min(y_data):.2f}）\n\n'
            
            analysis_text += f'### 每日消费详情\n'
            for date, amount in zip(x_data, y_data):
                flag = '🔴' if amount > avg * 1.5 else ('' if amount < avg * 0.5 else '')
                analysis_text += f'- {date}：¥{amount:.2f} {flag}\n'
            
            analysis_text += f'\n### 消费趋势建议\n'
            if len(y_data) >= 2:
                recent_avg = sum(y_data[-3:]) / min(3, len(y_data))
                if recent_avg > avg * 1.2:
                    analysis_text += '- 近期消费呈上升趋势，建议关注消费习惯\n'
                elif recent_avg < avg * 0.8:
                    analysis_text += '- 近期消费呈下降趋势，消费控制良好\n'
                else:
                    analysis_text += '- 消费趋势相对平稳\n'
        
        return JsonResponse({
            'success': True,
            'data': {
                'title': title,
                'x_data': x_data,
                'y_data': y_data,
                'y_label': y_label,
                'summary': analysis_text,
                'chart_type': chart_type
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'msg': f'分析失败：{str(e)}'})
    finally:
        if conn:
            conn.close()


def analyze_schedule_data(user_phone, days, chart_type):
    conn = None
    try:
        conn = pymysql.connect(
            host="localhost",
            port=3306,
            user="root",
            password="123456",
            database="gzeu_sql",
            charset="utf8"
        )
        cursor = conn.cursor()
        
        # 根据图表类型决定查询方式
        category_chart_types = ['pie', 'funnel', 'radar', 'gauge']
        
        if chart_type in category_chart_types:
            # 分类数据：按日程标题关键词分类
            sql = """
                SELECT 
                    CASE 
                        WHEN title LIKE '%%会议%%' OR title LIKE '%%开会%%' THEN '会议'
                        WHEN title LIKE '%%运动%%' OR title LIKE '%%健身%%' OR title LIKE '%%跑步%%' THEN '运动'
                        WHEN title LIKE '%%学习%%' OR title LIKE '%%课程%%' OR title LIKE '%%考试%%' THEN '学习'
                        WHEN title LIKE '%%工作%%' OR title LIKE '%%项目%%' OR title LIKE '%%任务%%' THEN '工作'
                        WHEN title LIKE '%%生活%%' OR title LIKE '%%购物%%' OR title LIKE '%%吃饭%%' THEN '生活'
                        ELSE '其他'
                    END as category,
                    COUNT(*) as count 
                FROM user_schedule 
                WHERE user_phone = %s 
                AND start_time >= DATE_SUB(NOW(), INTERVAL %s DAY)
                GROUP BY category 
                ORDER BY count DESC
            """
            cursor.execute(sql, (user_phone, days))
        else:
            # 时间序列数据：按日期统计
            sql = """
                SELECT DATE(start_time) as date, COUNT(*) as count 
                FROM user_schedule 
                WHERE user_phone = %s 
                AND start_time >= DATE_SUB(NOW(), INTERVAL %s DAY)
                GROUP BY DATE(start_time) 
                ORDER BY date
            """
            cursor.execute(sql, (user_phone, days))
        
        results = cursor.fetchall()
        
        if not results:
            return JsonResponse({'success': False, 'msg': '暂无数据'})
        
        x_data = []
        y_data = []
        
        if chart_type in category_chart_types:
            # 分类数据
            for row in results:
                x_data.append(str(row[0]))
                y_data.append(int(row[1]))
            title = f'近{days}天日程分类统计'
            y_label = '日程数量'
            total = sum(y_data)
            
            analysis_text = f'## 近{days}天日程分析报告\n\n'
            analysis_text += f'### 总体概况\n'
            analysis_text += f'- **总日程数**：{total} 个\n'
            analysis_text += f'- **日程类别数**：{len(x_data)} 个\n'
            analysis_text += f'- **最多类别**：{x_data[0]}（{y_data[0]} 个，占比 {y_data[0]/total*100:.1f}%）\n\n'
            
            analysis_text += f'### 各类别日程详情\n'
            for i, (cat, count) in enumerate(zip(x_data, y_data)):
                percent = count/total*100
                analysis_text += f'{i+1}. **{cat}**：{count} 个（{percent:.1f}%）\n'
            
            analysis_text += f'\n### 日程分布建议\n'
            if len(x_data) > 1:
                highest_cat = x_data[0]
                highest_count = y_data[0]
                if highest_count > total * 0.5:
                    analysis_text += f'- {highest_cat}类日程占比较高（{highest_count/total*100:.1f}%），建议合理分配时间\n'
                else:
                    analysis_text += f'- 日程分布相对均衡，{highest_cat}略多，可关注其他类别\n'
        else:
            # 时间序列数据
            for row in results:
                x_data.append(str(row[0]))
                y_data.append(int(row[1]))
            total = sum(y_data)
            avg = total / len(y_data) if y_data else 0
            title = f'近{days}天日程安排统计'
            y_label = '日程数量'
            max_day = x_data[y_data.index(max(y_data))] if y_data else '无'
            min_day = x_data[y_data.index(min(y_data))] if y_data else '无'
            
            analysis_text = f'## 近{days}天日程趋势分析\n\n'
            analysis_text += f'### 总体概况\n'
            analysis_text += f'- **总日程数**：{total} 个\n'
            analysis_text += f'- **日均日程**：{avg:.1f} 个\n'
            analysis_text += f'- **有日程天数**：{len(x_data)} 天\n'
            analysis_text += f'- **最忙日**：{max_day}（{max(y_data)} 个日程）\n'
            analysis_text += f'- **最闲日**：{min_day}（{min(y_data)} 个日程）\n\n'
            
            analysis_text += f'### 每日日程详情\n'
            for date, count in zip(x_data, y_data):
                flag = '🔴' if count > avg * 1.5 else ('' if count < avg * 0.5 else '')
                analysis_text += f'- {date}：{count} 个日程 {flag}\n'
            
            analysis_text += f'\n### 日程趋势建议\n'
            if len(y_data) >= 2:
                recent_avg = sum(y_data[-3:]) / min(3, len(y_data))
                if recent_avg > avg * 1.2:
                    analysis_text += '- 近期日程呈增加趋势，注意合理安排时间\n'
                elif recent_avg < avg * 0.8:
                    analysis_text += '- 近期日程呈减少趋势，可适当增加活动\n'
                else:
                    analysis_text += '- 日程安排相对平稳\n'
        
        return JsonResponse({
            'success': True,
            'data': {
                'title': title,
                'x_data': x_data,
                'y_data': y_data,
                'y_label': y_label,
                'summary': analysis_text,
                'chart_type': chart_type
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'msg': f'分析失败：{str(e)}'})
    finally:
        if conn:
            conn.close()


@csrf_exempt
def data_analysis_upload(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'msg': '请求方法错误'})
    
    try:
        if 'file' not in request.FILES:
            return JsonResponse({'success': False, 'msg': '未找到上传的文件'})
        
        uploaded_file = request.FILES['file']
        file_name = uploaded_file.name
        file_ext = os.path.splitext(file_name)[1].lower()
        
        if file_ext not in ['.csv', '.xlsx', '.xls']:
            return JsonResponse({'success': False, 'msg': '不支持的文件格式，请上传 CSV 或 Excel 文件'})
        
        upload_dir = os.path.join(settings.BASE_DIR, 'myapp', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        save_path = os.path.join(upload_dir, f'{timestamp}_{file_name}')
        
        with open(save_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        
        columns = []
        preview = []
        total_rows = 0
        
        if file_ext == '.csv':
            with open(save_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                columns = reader.fieldnames if reader.fieldnames else []
                for i, row in enumerate(reader):
                    if i < 5:
                        preview.append(row)
                    total_rows += 1
        else:
            try:
                import openpyxl
                wb = openpyxl.load_workbook(save_path, read_only=True)
                ws = wb.active
                columns = [cell.value for cell in next(ws.iter_rows(min_row=1, max_row=1))]
                for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True)):
                    if i < 5:
                        row_dict = {}
                        for j, col in enumerate(columns):
                            if j < len(row):
                                row_dict[col] = row[j]
                            else:
                                row_dict[col] = ''
                        preview.append(row_dict)
                    total_rows += 1
                wb.close()
            except ImportError:
                return JsonResponse({
                    'success': False, 
                    'msg': '处理 Excel 文件需要安装 openpyxl，请运行：pip install openpyxl',
                    'file_path': save_path,
                    'columns': [],
                    'preview': [],
                    'total_rows': 0
                })
        
        return JsonResponse({
            'success': True,
            'file_path': save_path,
            'columns': columns,
            'preview': preview,
            'total_rows': total_rows
        })
    except Exception as e:
        return JsonResponse({'success': False, 'msg': f'文件解析失败：{str(e)}'})


@csrf_exempt
def data_analysis_file(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'msg': '请求方法错误'})
    
    try:
        data = json.loads(request.body.decode('utf-8'))
        file_path = data.get('file_path', '')
        x_field = data.get('x_field', '')
        y_field = data.get('y_field', '')
        chart_type = data.get('chart_type', 'bar')
        
        if not os.path.exists(file_path):
            return JsonResponse({'success': False, 'msg': '文件不存在'})
        
        file_ext = os.path.splitext(file_path)[1].lower()
        x_data = []
        y_data = []
        
        if file_ext == '.csv':
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    x_val = row.get(x_field, '')
                    y_val = row.get(y_field, '0')
                    try:
                        y_val = float(y_val)
                    except:
                        y_val = 0
                    x_data.append(str(x_val))
                    y_data.append(y_val)
        else:
            try:
                import openpyxl
                wb = openpyxl.load_workbook(file_path, read_only=True)
                ws = wb.active
                rows = list(ws.iter_rows(values_only=True))
                if rows:
                    headers = rows[0]
                    x_idx = headers.index(x_field) if x_field in headers else -1
                    y_idx = headers.index(y_field) if y_field in headers else -1
                    
                    if x_idx >= 0 and y_idx >= 0:
                        for row in rows[1:]:
                            x_val = row[x_idx] if x_idx < len(row) else ''
                            y_val = row[y_idx] if y_idx < len(row) else 0
                            try:
                                y_val = float(y_val)
                            except:
                                y_val = 0
                            x_data.append(str(x_val))
                            y_data.append(y_val)
                wb.close()
            except ImportError:
                return JsonResponse({'success': False, 'msg': '需要安装 openpyxl：pip install openpyxl'})
        
        if not x_data:
            return JsonResponse({'success': False, 'msg': '未找到有效数据'})
        
        if chart_type == 'pie':
            title = f'{y_field} 分类统计'
            y_label = y_field
            total = sum(y_data)
            
            analysis_text = f'## {y_field} 分类分析报告\n\n'
            analysis_text += f'### 总体概况\n'
            analysis_text += f'- **总数据量**：{total:.2f}\n'
            analysis_text += f'- **分类数量**：{len(x_data)} 个\n'
            
            sorted_data = sorted(zip(x_data, y_data), key=lambda x: x[1], reverse=True)
            if sorted_data:
                top_cat = sorted_data[0][0]
                top_val = sorted_data[0][1]
                analysis_text += f'- **最高类别**：{top_cat}（{top_val:.2f}，占比 {top_val/total*100:.1f}%）\n\n'
                
                analysis_text += f'### 各类别详情\n'
                for i, (cat, val) in enumerate(sorted_data):
                    percent = val/total*100
                    analysis_text += f'{i+1}. **{cat}**：{val:.2f}（{percent:.1f}%）\n'
                
                analysis_text += f'\n### 分析建议\n'
                if len(sorted_data) > 1:
                    if sorted_data[0][1] > total * 0.5:
                        analysis_text += f'- {sorted_data[0][0]}占比较高，建议重点关注\n'
                    else:
                        analysis_text += f'- 数据分布相对均衡\n'
        else:
            title = f'{x_field} - {y_field} 分析'
            y_label = y_field
            total = sum(y_data)
            avg = total / len(y_data) if y_data else 0
            max_val = max(y_data) if y_data else 0
            min_val = min(y_data) if y_data else 0
            max_idx = y_data.index(max_val) if y_data else 0
            min_idx = y_data.index(min_val) if y_data else 0
            
            analysis_text = f'## {x_field} - {y_field} 趋势分析报告\n\n'
            analysis_text += f'### 总体概况\n'
            analysis_text += f'- **总数据量**：{total:.2f}\n'
            analysis_text += f'- **平均值**：{avg:.2f}\n'
            analysis_text += f'- **最大值**：{max_val:.2f}（{x_data[max_idx]}）\n'
            analysis_text += f'- **最小值**：{min_val:.2f}（{x_data[min_idx]}）\n'
            analysis_text += f'- **数据条数**：{len(x_data)} 条\n\n'
            
            analysis_text += f'### 数据详情\n'
            for x_val, y_val in zip(x_data[:10], y_data[:10]):
                flag = '🔴' if y_val > avg * 1.5 else ('' if y_val < avg * 0.5 else '')
                analysis_text += f'- {x_val}：{y_val:.2f} {flag}\n'
            if len(x_data) > 10:
                analysis_text += f'- ...（共 {len(x_data)} 条数据）\n'
            
            analysis_text += f'\n### 趋势分析\n'
            if len(y_data) >= 2:
                recent_avg = sum(y_data[-3:]) / min(3, len(y_data))
                if recent_avg > avg * 1.2:
                    analysis_text += '- 近期数据呈上升趋势\n'
                elif recent_avg < avg * 0.8:
                    analysis_text += '- 近期数据呈下降趋势\n'
                else:
                    analysis_text += '- 数据趋势相对平稳\n'
        
        return JsonResponse({
            'success': True,
            'data': {
                'title': title,
                'x_data': x_data,
                'y_data': y_data,
                'y_label': y_label,
                'summary': analysis_text
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'msg': f'分析失败：{str(e)}'})