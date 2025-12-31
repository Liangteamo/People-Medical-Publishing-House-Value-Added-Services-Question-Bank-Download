# 人民卫生出版社图书增值服务的题目加密PDF下载和解密工具

用于从 `zengzhi.ipmph.com` 下载加密PDF并自动解密的工具。

## 具体操作步骤
具体操作步骤查看附件 <<具体操作步骤.pdf>>

## 功能

- 自动下载PDF文件（支持多页PDF）
- 自动获取PDF密钥（openKey和uKey）
- 使用AES-CBC解密算法自动解密PDF密码
- 自动解密并保存PDF文件

## 依赖

```bash
pip install requests PyPDF2 pycryptodome base64
```

## 使用方法

### 方式1: 输入PDF链接（如果链接直接包含PDF ID）

```bash
python pdf_downloader_decryptor.py "https://bzyxz.ipmph.com/pdf/98561d71103244e3a7caebdfd674c3ba/..."
```

程序会自动从URL中提取PDF ID（仅当URL直接包含PDF ID时）。

### 方式2: 直接输入PDF ID（推荐）

```bash
python pdf_downloader_decryptor.py <pdf_id> [pdf_name]
```

### 参数说明

- `url或pdf_id`: PDF预览链接或PDF的ID（必需）
- `total_pages`: PDF总页数（可选，默认为1）
- `pdf_name`: 输出文件名（可选，默认自动生成）

### 示例

```bash
# 方式1: 输入PDF链接（如果链接包含PDF ID）
python pdf_downloader_decryptor.py "https://bzyxz.ipmph.com/pdf/98561d71103244e3a7caebdfd674c3ba/..."

# 方式2: 直接输入PDF ID（推荐）
python pdf_downloader_decryptor.py 98561d71103244e3a7caebdfd674c3ba

# 方式3: 指定输出文件名
python pdf_downloader_decryptor.py 94d8a6c0300b40c3a79e5d09fe5d58d7 "第一章_细胞组织的适应和损伤.pdf"
```

### 如何获取PDF ID

1. 在浏览器中打开PDF预览页面
2. 按F12打开开发者工具
3. 切换到Network（网络）标签
4. 刷新页面或等待页面加载
5. 查找以下任一请求：
   - 包含 `/pdf/` 的请求，PDF ID在URL中（如：`https://bzyxz.ipmph.com/pdf/98561d71103244e3a7caebdfd674c3ba/...`）
   - `priv_resourceDetail` API请求，查看响应中的`resourcePath`
   - 密钥JS文件请求: `{pdf_id}.js`
6. PDF ID通常是32位小写十六进制字符串（如：`98561d71103244e3a7caebdfd674c3ba`）

## 工作原理

1. **获取密钥**：
   - 从 `https://bzyxz.ipmph.com/pdf/{pdf_id}/{pdf_id}.js` 获取 `openKey`
   - 从 `config.js` 获取 `uKey`（默认使用 `1030110301123456`）

2. **解密密码**：
   - 使用AES-CBC算法解密 `openKey`
   - 密钥：`uKey`
   - IV：`1234567890123456`
   - 填充：ZeroPadding

3. **下载PDF**：
   - 下载所有页面（格式：`{page}_{pdf_id}.pdf`）
   - 自动合并多页PDF

4. **解密PDF**：
   - 使用解密出的密码解密PDF
   - 保存为 `{原文件名}_已解密.pdf`

## 技术细节

解密算法对应JavaScript代码：

```javascript
function Decrypt(word, keyStr) {
  let key = CryptoJS.enc.Utf8.parse(keyStr || "1234567890123456");
  let iv = CryptoJS.enc.Utf8.parse("1234567890123456");
  let base64 = CryptoJS.enc.Base64.parse(word);
  let src = CryptoJS.enc.Base64.stringify(base64);
  let decrypt = CryptoJS.AES.decrypt(src, key, {
    iv: iv,
    mode: CryptoJS.mode.CBC,
    padding: CryptoJS.pad.ZeroPadding,
  });
  return decrypt.toString(CryptoJS.enc.Utf8);
}
```

## 注意事项

- 需要有效的登录状态才能访问PDF资源
- PDF ID可以从浏览器网络请求中获取
- 如果PDF未加密，程序会提示并直接保存

## 文件说明

- `pdf_downloader_decryptor.py`: 主程序
- `README.md`: 本说明文件



