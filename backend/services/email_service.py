"""
邮件服务封装。

支持两种模式：
1. Mock 模式（开发/测试）：仅打印日志，不发送真实邮件
2. 生产模式：使用 SMTP 发送真实邮件

配置项（环境变量）：
- SMTP_HOST: SMTP 服务器地址
- SMTP_PORT: SMTP 端口（默认 465）
- SMTP_USER: SMTP 用户名
- SMTP_PASSWORD: SMTP 密码
- SMTP_FROM: 发件人地址
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime


class EmailService:
    """
    邮件服务封装类。
    
    生产环境需配置 SMTP 服务：
    1. 开通企业邮箱或使用第三方邮件服务
    2. 配置 SMTP 服务器信息
    3. 配置环境变量
    """
    
    @staticmethod
    def _is_production():
        """
        判断是否为生产环境。
        
        当配置了 SMTP 凭证时，视为生产环境。
        """
        return bool(os.environ.get('SMTP_HOST') and 
                   os.environ.get('SMTP_USER') and 
                   os.environ.get('SMTP_PASSWORD'))
    
    @staticmethod
    def send_email(to_email, subject, body, attachment=None, attachment_filename=None):
        """
        发送邮件。

        参数：
        - to_email: 收件人邮箱
        - subject: 邮件主题
        - body: 邮件正文
        - attachment: 附件内容（字节）
        - attachment_filename: 附件文件名

        返回：
        - bool: 是否发送成功
        """
        if EmailService._is_production():
            return EmailService._send_smtp(to_email, subject, body, attachment, attachment_filename)
        else:
            return EmailService._send_mock(to_email, subject, body, attachment, attachment_filename)
    
    @staticmethod
    def _send_mock(to_email, subject, body, attachment=None, attachment_filename=None):
        """
        Mock 发送（开发/测试环境）。
        
        仅打印日志，模拟发送成功。
        """
        print(f"[EMAIL MOCK] 发送邮件到: {to_email}")
        print(f"[EMAIL MOCK] 主题: {subject}")
        print(f"[EMAIL MOCK] 正文: {body[:100]}...")
        if attachment:
            print(f"[EMAIL MOCK] 附件: {attachment_filename} ({len(attachment)} bytes)")
        return True
    
    @staticmethod
    def _send_smtp(to_email, subject, body, attachment=None, attachment_filename=None):
        """
        SMTP 发送（生产环境）。
        """
        try:
            smtp_host = os.environ.get('SMTP_HOST')
            smtp_port = int(os.environ.get('SMTP_PORT', 465))
            smtp_user = os.environ.get('SMTP_USER')
            smtp_password = os.environ.get('SMTP_PASSWORD')
            smtp_from = os.environ.get('SMTP_FROM', smtp_user)
            
            msg = MIMEMultipart()
            msg['From'] = smtp_from
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            if attachment and attachment_filename:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment)
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename="{attachment_filename}"'
                )
                msg.attach(part)
            
            with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_from, to_email, msg.as_string())
            
            print(f"[EMAIL] 邮件发送成功: {to_email}")
            return True
            
        except Exception as e:
            print(f"[EMAIL ERROR] 发送失败: {e}")
            return False
    
    @staticmethod
    def send_participant_export(to_email, activity_name, csv_content):
        """
        发送报名名单导出邮件。

        参数：
        - to_email: 收件人邮箱
        - activity_name: 活动名称
        - csv_content: CSV 内容（字符串）

        返回：
        - bool: 是否发送成功
        """
        subject = f"【活动帮手】报名名单导出 - {activity_name}"
        body = f"""您好！

您请求导出的活动报名名单已生成，请查看附件。

活动名称：{activity_name}
导出时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

如有问题，请回复此邮件。

活动帮手团队
"""
        attachment = csv_content.encode('utf-8-sig')
        filename = f"报名名单_{activity_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return EmailService.send_email(to_email, subject, body, attachment, filename)
