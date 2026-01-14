#!/usr/bin/env python3
"""
Email 地址生成工具
根據學號規則自動生成對應的 email 地址
"""

import re
from typing import Optional


class EmailGenerator:
    """根據學號生成 email 地址的工具類"""
    
    @staticmethod
    def generate_email_from_student_id(student_id: str) -> Optional[str]:
        """
        根據學號生成對應的 email 地址
        
        規則：
        - 大學部 Undergraduate: 4開頭 -> s{student_id}@mail.nchu.edu.tw
        - 研究所 Graduate: 7開頭 -> g{student_id}@mail.nchu.edu.tw  
        - 博士班 PHD: 8開頭 -> d{student_id}@mail.nchu.edu.tw
        - 在職專班 Executive Master: 5開頭 -> w{student_id}@mail.nchu.edu.tw
        - 進修部 Night Division: 3開頭 -> n{student_id}@mail.nchu.edu.tw
        
        Args:
            student_id (str): 學號
            
        Returns:
            Optional[str]: 生成的 email 地址，如果學號格式不符合規則則返回 None
        """
        if not student_id or not isinstance(student_id, str):
            return None
            
        # 移除可能的前綴字母和空白字符
        clean_id = student_id.strip().upper()
        
        # 如果學號已經有前綴字母，先移除
        if clean_id and clean_id[0].isalpha():
            clean_id = clean_id[1:]
        
        # 檢查是否為純數字且長度合理（至少6位數字）
        if not clean_id.isdigit() or len(clean_id) < 6:
            return None
            
        # 根據第一位數字決定前綴和 email 格式
        first_digit = clean_id[0]
        
        prefix_mapping = {
            '4': 's',  # 大學部 Undergraduate
            '7': 'g',  # 研究所 Graduate  
            '8': 'd',  # 博士班 PHD
            '5': 'w',  # 在職專班 Executive Master
            '3': 'n',  # 進修部 Night Division
            '6': 's',  # 大學部 Undergraduate (其他格式)
            '9': 's',  # 大學部 Undergraduate (其他格式)
            '1': 's',  # 大學部 Undergraduate (其他格式)
            '2': 's',  # 大學部 Undergraduate (其他格式)
            '0': 's'   # 大學部 Undergraduate (測試數據格式)
        }
        
        if first_digit not in prefix_mapping:
            return None
            
        prefix = prefix_mapping[first_digit]
        email = f"{prefix}{clean_id}@mail.nchu.edu.tw"
        
        return email
    
    @staticmethod
    def get_student_type_from_id(student_id: str) -> Optional[str]:
        """
        根據學號判斷學生類型
        
        Args:
            student_id (str): 學號
            
        Returns:
            Optional[str]: 學生類型描述
        """
        if not student_id or not isinstance(student_id, str):
            return None
            
        # 移除可能的前綴字母和空白字符
        clean_id = student_id.strip().upper()
        if clean_id and clean_id[0].isalpha():
            clean_id = clean_id[1:]
            
        if not clean_id.isdigit() or len(clean_id) < 6:
            return None
            
        first_digit = clean_id[0]
        
        type_mapping = {
            '4': '大學部 Undergraduate',
            '7': '研究所 Graduate',
            '8': '博士班 PHD', 
            '5': '在職專班 Executive Master',
            '3': '進修部 Night Division',
            '6': '大學部 Undergraduate',
            '9': '大學部 Undergraduate',
            '1': '大學部 Undergraduate',
            '2': '大學部 Undergraduate',
            '0': '大學部 Undergraduate'
        }
        
        return type_mapping.get(first_digit)
    
    @staticmethod
    def batch_generate_emails(student_ids: list) -> dict:
        """
        批量生成 email 地址
        
        Args:
            student_ids (list): 學號列表
            
        Returns:
            dict: {student_id: email} 的映射字典
        """
        result = {}
        
        for student_id in student_ids:
            email = EmailGenerator.generate_email_from_student_id(student_id)
            if email:
                result[student_id] = email
                
        return result
    
    @staticmethod
    def validate_generated_email(email: str) -> bool:
        """
        驗證生成的 email 格式是否正確
        
        Args:
            email (str): email 地址
            
        Returns:
            bool: 是否為有效的 email 格式
        """
        if not email:
            return False
            
        # 檢查是否符合預期的格式（至少6位數字）
        pattern = r'^[sgdwn]\d{6,}@mail\.nchu\.edu\.tw$'
        return bool(re.match(pattern, email))


# 測試函數
def test_email_generator():
    """測試 email 生成功能"""
    test_cases = [
        ("4101027415", "s4101027415@mail.nchu.edu.tw", "大學部 Undergraduate"),
        ("7101027415", "g7101027415@mail.nchu.edu.tw", "研究所 Graduate"),
        ("8101027415", "d8101027415@mail.nchu.edu.tw", "博士班 PHD"),
        ("5101027415", "w5101027415@mail.nchu.edu.tw", "在職專班 Executive Master"),
        ("3101027415", "n3101027415@mail.nchu.edu.tw", "進修部 Night Division"),
        ("s4101027415", "s4101027415@mail.nchu.edu.tw", "大學部 Undergraduate"),  # 已有前綴
        ("G7101027415", "g7101027415@mail.nchu.edu.tw", "研究所 Graduate"),  # 大寫前綴
        ("9101027415", None, None),  # 不支援的開頭數字
        ("abc", None, None),  # 無效格式
        ("", None, None),  # 空字串
    ]
    
    print("=== Email Generator 測試 ===")
    
    for student_id, expected_email, expected_type in test_cases:
        generated_email = EmailGenerator.generate_email_from_student_id(student_id)
        student_type = EmailGenerator.get_student_type_from_id(student_id)
        
        email_match = generated_email == expected_email
        type_match = student_type == expected_type
        
        status = "✅" if (email_match and type_match) else "❌"
        
        print(f"{status} 學號: {student_id}")
        print(f"   生成 Email: {generated_email}")
        print(f"   預期 Email: {expected_email}")
        print(f"   學生類型: {student_type}")
        print(f"   預期類型: {expected_type}")
        print()
    
    # 測試批量生成
    print("=== 批量生成測試 ===")
    test_ids = ["4101027415", "7101027416", "8101027417", "5101027418", "3101027419"]
    batch_result = EmailGenerator.batch_generate_emails(test_ids)
    
    for student_id, email in batch_result.items():
        print(f"學號: {student_id} -> Email: {email}")
    
    # 測試 email 驗證
    print("\n=== Email 驗證測試 ===")
    test_emails = [
        ("s4101027415@mail.nchu.edu.tw", True),
        ("g7101027415@mail.nchu.edu.tw", True),
        ("invalid@gmail.com", False),
        ("s123@mail.nchu.edu.tw", False),  # 學號太短
        ("x4101027415@mail.nchu.edu.tw", False),  # 錯誤前綴
    ]
    
    for email, expected in test_emails:
        result = EmailGenerator.validate_generated_email(email)
        status = "✅" if result == expected else "❌"
        print(f"{status} {email} -> {result} (預期: {expected})")


if __name__ == "__main__":
    test_email_generator() 