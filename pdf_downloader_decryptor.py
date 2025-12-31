#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF下载和解密工具
支持从zengzhi.ipmph.com下载加密PDF并自动解密
"""

import requests
import base64
import os
import re
import sys
from PyPDF2 import PdfReader, PdfWriter

try:
    from Crypto.Cipher import AES
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False
    print("错误: 需要安装 pycryptodome")
    print("请运行: pip install pycryptodome")
    sys.exit(1)


class PDFDownloaderDecryptor:
    """PDF下载和解密类"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://zengzhi.ipmph.com/',
        }
        self.default_ukey = "1030110301123456"  # 实际使用的uKey
        self.default_iv = "1234567890123456"
    
    def extract_pdf_id_from_url(self, url):
        """从URL中提取PDF ID"""
        try:
            if '/pdf/' in url:
                match = re.search(r'/pdf/([a-f0-9]{32})', url)
                if match:
                    return match.group(1)
            
            hex_matches = re.findall(r'([a-f0-9]{32})', url)
            for pdf_id in hex_matches:
                if len(pdf_id) == 32 and pdf_id.islower():
                    return pdf_id
            return None
        except:
            return None
    
    def decrypt_with_cryptojs_logic(self, openkey_b64, ukey=None):
        """使用CryptoJS逻辑解密openKey获取PDF密码"""
        try:
            key = (ukey or self.default_ukey).encode('utf-8')
            iv_bytes = self.default_iv.encode('utf-8')
            encrypted_data = base64.b64decode(openkey_b64)
            cipher = AES.new(key, AES.MODE_CBC, iv_bytes)
            decrypted = cipher.decrypt(encrypted_data).rstrip(b'\x00')
            password = ''.join(c for c in decrypted.decode('utf-8', errors='ignore') if c.isprintable())
            return password if password else None
        except Exception as e:
            print(f"  解密失败: {e}")
            return None
    
    def get_pdf_keys(self, pdf_id):
        """获取PDF的密钥（openKey和uKey）"""
        print(f"获取PDF密钥 (ID: {pdf_id})...")
        
        key_js_url = f"https://bzyxz.ipmph.com/pdf/{pdf_id}/{pdf_id}.js"
        openkey = None
        
        try:
            response = requests.get(key_js_url, headers=self.headers, timeout=30)
            if response.status_code == 200:
                match = re.search(r'openKey\s*[:=]\s*["\']([^"\']+)["\']', response.text)
                if match:
                    openkey = match.group(1)
                    print(f"  [成功] 找到 openKey: {openkey}")
                else:
                    print("  [失败] 未找到 openKey")
            else:
                print(f"  [失败] 下载密钥JS文件失败: {response.status_code}")
        except Exception as e:
            print(f"  [错误] {e}")
        
        ukey = self.default_ukey
        print(f"  [成功] 找到 uKey: {ukey}")
        
        return openkey, ukey
    
    def download_pdf(self, pdf_id, output_name=None):
        """
        下载PDF文件
        
        Args:
            pdf_id: PDF的ID
            output_name: 输出文件名，如果为None则自动生成
        
        Returns:
            下载的PDF文件路径，失败返回None
        """
        print(f"下载PDF (ID: {pdf_id})...")
        
        pdf_url = f"https://bzyxz.ipmph.com/pdf/{pdf_id}/0_{pdf_id}.pdf"
        temp_filename = f"temp_{pdf_id[:8]}.pdf"
        
        try:
            response = requests.get(pdf_url, headers=self.headers, stream=True, timeout=30)
            if response.status_code == 200:
                with open(temp_filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                file_size = os.path.getsize(temp_filename)
                print(f"  [成功] 下载完成 ({file_size / 1024:.2f} KB)")
            else:
                print(f"  [失败] 下载失败 ({response.status_code})")
                return None
        except Exception as e:
            print(f"  [错误] {e}")
            return None
        
        # 重命名文件
        if output_name is None:
            output_name = f"PDF_{pdf_id[:8]}.pdf"
        
        if os.path.exists(output_name):
            os.remove(output_name)
        os.rename(temp_filename, output_name)
        print(f"  [成功] 保存为: {output_name}")
        return output_name
    
    def decrypt_pdf(self, pdf_path, password):
        """解密PDF文件"""
        if not os.path.exists(pdf_path):
            print(f"错误: 找不到PDF文件: {pdf_path}")
            return None
        
        print(f"解密PDF: {pdf_path}")
        
        try:
            reader = PdfReader(pdf_path)
            if not reader.is_encrypted:
                print("  [提示] PDF未加密，无需解密")
                return pdf_path
            
            print(f"  尝试密码: '{password}'", end=' ... ')
            if not reader.decrypt(password):
                print("失败")
                return None
            
            print("成功")
            output_path = f"{os.path.splitext(pdf_path)[0]}_已解密.pdf"
            
            writer = PdfWriter()
            for page in reader.pages:
                writer.add_page(page)
            if reader.metadata:
                writer.add_metadata(reader.metadata)
            
            with open(output_path, 'wb') as f:
                writer.write(f)
            
            file_size = os.path.getsize(output_path)
            print(f"  [成功] 解密后的PDF已保存: {output_path}")
            print(f"  [成功] 文件大小: {file_size / 1024:.2f} KB")
            return output_path
        except Exception as e:
            print(f"  [错误] {e}")
            return None
    
    def process_pdf(self, pdf_id, pdf_name=None):
        """
        完整的PDF处理流程：下载 -> 获取密钥 -> 解密
        
        Args:
            pdf_id: PDF的ID
            pdf_name: PDF文件名（可选）
        
        Returns:
            解密后的PDF文件路径，失败返回None
        """
        # 1. 获取密钥
        openkey, ukey = self.get_pdf_keys(pdf_id)
        if not openkey:
            print("\n[失败] 无法获取openKey，无法继续")
            return None
        
        print()
        
        # 2. 解密密码
        print("破解PDF密码...")
        password = self.decrypt_with_cryptojs_logic(openkey, ukey)
        if not password:
            password = self.decrypt_with_cryptojs_logic(openkey, "1234567890123456")
        if not password:
            print("  [失败] 无法破解密码")
            return None
        print(f"  [成功] 破解出的密码: '{password}'")
        print()
        
        # 3. 下载PDF
        pdf_path = self.download_pdf(pdf_id, pdf_name)
        if not pdf_path:
            return None
        
        print()
        
        # 4. 解密PDF
        decrypted_path = self.decrypt_pdf(pdf_path, password)
        return decrypted_path


def main():
    """主函数"""
    print("=" * 70)
    print("PDF下载和解密工具")
    print("=" * 70)
    
    decryptor = PDFDownloaderDecryptor()
    
    while True:
        try:
            user_input = input("请输入PDF链接或PDF ID: ").strip()
            
            if user_input.lower() in ['q', 'quit', 'exit', '退出']:
                print("\n程序已退出。")
                break
            
            if not user_input:
                continue
            
            # 获取PDF文件名（可选）
            pdf_name = None
            name_input = input("请输入PDF文件名（直接回车使用默认名称）: ").strip()
            if name_input:
                pdf_name = name_input if name_input.endswith('.pdf') else f"{name_input}.pdf"
            
            # 判断输入是URL还是PDF ID
            if user_input.startswith('http://') or user_input.startswith('https://'):
                pdf_id = decryptor.extract_pdf_id_from_url(user_input)
                if not pdf_id:
                    print("\n[失败] 无法从URL中提取PDF ID，请直接输入PDF ID")
                    continue
            else:
                pdf_id = user_input
                if len(pdf_id) != 32 or not all(c in '0123456789abcdef' for c in pdf_id.lower()):
                    print(f"\n[警告] PDF ID格式不正确，请检查后重新输入")
                    continue
            
            # 处理PDF
            print()
            result = decryptor.process_pdf(pdf_id, pdf_name)
            
            if result:
                print("=" * 70)
                print("[成功] 处理完成！")
                print("=" * 70 + '\n')
            else:
                print("\n" + "=" * 70)
                print("[失败] 处理失败")
                print("=" * 70)
            
        except KeyboardInterrupt:
            print("\n\n程序已退出。")
            break
        except Exception as e:
            print(f"\n[错误] {e}")
            continue


if __name__ == "__main__":
    main()
