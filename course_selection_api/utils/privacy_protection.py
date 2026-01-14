"""
個資保護工具函數
用於對敏感資訊進行遮罩處理
"""

def mask_student_id(student_id: str) -> str:
    """
    學號遮罩：保留前2後3，其他改成*
    例如：1234567890 -> 12****890
    """
    if not student_id or len(student_id) < 5:
        return student_id
    
    if len(student_id) <= 5:
        # 如果學號長度小於等於5，只保留前2後1
        return student_id[:2] + "*" * (len(student_id) - 3) + student_id[-1:]
    else:
        # 保留前2後3
        return student_id[:2] + "*" * (len(student_id) - 5) + student_id[-3:]


def mask_chinese_name(name: str) -> str:
    """
    中文姓名遮罩：
    - 三個字：中間的字改成O，例如：王小明 -> 王O明
    - 兩個字：最後一個字改成O，例如：李華 -> 李O
    - 四個字以上：保留第一個和最後一個字，中間改成O，例如：歐陽小明 -> 歐O明
    """
    if not name:
        return name
    
    # 移除空白字符
    name = name.strip()
    
    if len(name) == 1:
        return name
    elif len(name) == 2:
        return name[0] + "O"
    elif len(name) == 3:
        return name[0] + "O" + name[2]
    else:
        # 四個字以上，保留第一個和最後一個字
        return name[0] + "O" * (len(name) - 2) + name[-1]


def mask_english_name(name: str) -> str:
    """
    英文姓名遮罩：
    - 保留姓氏的第一個字母和名字的第一個字母
    - 其他字母改成*
    例如：John Smith -> J*** S****
    例如：Mary Johnson -> M*** J******
    """
    if not name:
        return name
    
    # 移除多餘空格並分割
    parts = name.strip().split()
    
    if not parts:
        return name
    
    masked_parts = []
    for part in parts:
        if len(part) <= 1:
            masked_parts.append(part)
        else:
            # 保留第一個字母，其他改成*
            masked_parts.append(part[0] + "*" * (len(part) - 1))
    
    return " ".join(masked_parts)


def mask_id_number(id_number: str) -> str:
    """
    身份證字號遮罩：保留前2後2，中間改成*
    例如：A123456789 -> A1****89
    """
    if not id_number or len(id_number) < 4:
        return id_number
    
    if len(id_number) <= 4:
        return id_number[:1] + "*" * (len(id_number) - 2) + id_number[-1:]
    else:
        return id_number[:2] + "*" * (len(id_number) - 4) + id_number[-2:]


def mask_phone(phone: str) -> str:
    """
    手機號碼遮罩：保留前3後2，中間改成*
    例如：0912345678 -> 091***78
    """
    if not phone or len(phone) < 5:
        return phone
    
    if len(phone) <= 5:
        return phone[:2] + "*" * (len(phone) - 3) + phone[-1:]
    else:
        return phone[:3] + "*" * (len(phone) - 5) + phone[-2:]


def mask_address(address: str) -> str:
    """
    地址遮罩：只保留前面的縣市區，詳細地址改成***
    例如：臺中市西屯區大墩十九街172號2樓 -> 臺中市西屯區***
    """
    if not address:
        return address
    
    # 尋找區、鄉、鎮的位置（排除直轄市中的「市」字）
    for i, char in enumerate(address):
        if char in ['區', '鄉', '鎮'] and i > 0:
            # 保留到區/鄉/鎮，後面改成***
            return address[:i+1] + "***"
    
    # 如果是直轄市，尋找第二個「市」字後的區
    if '市' in address:
        first_city_index = address.find('市')
        if first_city_index != -1:
            remaining = address[first_city_index + 1:]
            for i, char in enumerate(remaining):
                if char in ['區', '鄉', '鎮']:
                    # 保留到區/鄉/鎮，後面改成***
                    return address[:first_city_index + 1 + i + 1] + "***"
            # 如果沒找到區，保留到第一個市字
            return address[:first_city_index + 1] + "***"
    
    # 如果沒找到，保留前3個字符
    if len(address) > 3:
        return address[:3] + "***"
    else:
        return address


def mask_email(email: str) -> str:
    """
    電子郵件遮罩：保留第一個字符和@後面的部分，中間改成***
    例如：john.doe@example.com -> j***@example.com
    """
    if not email or '@' not in email:
        return email
    
    local, domain = email.split('@', 1)
    if len(local) <= 1:
        return email
    else:
        return local[0] + "***@" + domain


def apply_privacy_mask(data: dict) -> dict:
    """
    對資料字典應用個資遮罩
    """
    masked_data = data.copy()
    
    # 學號遮罩
    if 'student_id' in masked_data and masked_data['student_id']:
        masked_data['student_id'] = mask_student_id(str(masked_data['student_id']))
    
    if 'oracle_student_id' in masked_data and masked_data['oracle_student_id']:
        masked_data['oracle_student_id'] = mask_student_id(str(masked_data['oracle_student_id']))
    
    # 姓名遮罩
    if 'name' in masked_data and masked_data['name']:
        # 判斷是中文還是英文名字
        if any('\u4e00' <= char <= '\u9fff' for char in masked_data['name']):
            # 包含中文字符，使用中文遮罩
            masked_data['name'] = mask_chinese_name(masked_data['name'])
        else:
            # 不包含中文字符，使用英文遮罩
            masked_data['name'] = mask_english_name(masked_data['name'])
    
    # 中文姓名遮罩
    if 'chinese_name' in masked_data and masked_data['chinese_name']:
        masked_data['chinese_name'] = mask_chinese_name(masked_data['chinese_name'])
    
    # 英文姓名遮罩
    if 'english_name' in masked_data and masked_data['english_name']:
        masked_data['english_name'] = mask_english_name(masked_data['english_name'])
    
    # 以下欄位已從前端 API 回應中移除，只在 Excel 匯出時使用
    # 身份證字號遮罩
    if 'id_number' in masked_data and masked_data['id_number']:
        masked_data['id_number'] = mask_id_number(masked_data['id_number'])
    
    # 手機號碼遮罩
    if 'phone' in masked_data and masked_data['phone']:
        masked_data['phone'] = mask_phone(masked_data['phone'])
    
    # 地址遮罩
    if 'address' in masked_data and masked_data['address']:
        masked_data['address'] = mask_address(masked_data['address'])
    
    # 電子郵件遮罩
    if 'email' in masked_data and masked_data['email']:
        masked_data['email'] = mask_email(masked_data['email'])
    
    return masked_data 