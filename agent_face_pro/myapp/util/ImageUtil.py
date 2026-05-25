import json
import base64
import io
from PIL import Image
import numpy as np

def get_image_byte(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        image_data = data.get('code')
        if not image_data:
            raise ValueError("未找到图片数据")
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        image_bytes = base64.b64decode(image_data)
        return image_bytes
    except Exception as e:
        print(f"获取图片字节失败: {e}")
        raise

def get_image_array(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        image_data = data.get('code')
        if not image_data:
            raise ValueError("未找到图片数据")
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        image_bytes = base64.b64decode(image_data)
        img = Image.open(io.BytesIO(image_bytes))
        img = np.array(img)
        return img
    except Exception as e:
        print(f"获取图片数组失败: {e}")
        raise
