# Qzone_cleaner

# QQ 空间留言板批量删除工具

这是一个用于批量删除 QQ 空间留言板留言的 Python 脚本。

## 功能特点

- 使用 Selenium 自动化登录 QQ 空间
- 批量获取留言板留言并删除
- 支持手动处理图片验证码，避免登录卡死
- 内置防死循环机制，检测连续重复删除
- 可配置批量删除数量

## 环境要求

- Python 3.7+
- Chrome 浏览器

## 依赖安装

```bash
pip install selenium requests pymongo webdriver-manager
```

## 使用方法

1. 修改脚本中的配置：

```python
qq = 'your_qq_number'        # 你的 QQ 号
password = 'your_password'   # 你的 QQ 密码
host = 'localhost'           # MongoDB 主机
port = 27017                 # MongoDB 端口
db = 'QQ'                    # 数据库名
```

2. 运行脚本：

```bash
python message_board_clean.py
```

3. 按照提示操作：
   - 浏览器会自动打开 QQ 空间登录页面
   - 手动输入密码（或扫码登录）
   - 如遇图片验证码，手动完成验证
   - 返回终端按两次 Enter 键开始删除

## 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `batch_size` | 10 | 每批删除的留言数量 |
| `max_rounds` | 10000 | 最大删除轮数 |

## 注意事项

- 本工具仅用于删除自己 QQ 空间留言板的内容
- 登录时可能需要处理图片验证码
- 建议在删除前备份重要留言
- 频繁操作可能触发 QQ 风控机制
- 删除操作不可逆，请谨慎使用

