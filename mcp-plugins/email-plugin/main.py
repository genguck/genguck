from fastmcp.server import FastMCPServer, Tool
from typing import Dict, List, Any, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.config import config
from utils.logger import logger

server = FastMCPServer(name="email-plugin", version="1.0.0")

@server.register
class EmailPlugin:
    class Meta:
        name = "email_plugin"
        description = "开发信生成与邮件发送插件"
    
    @Tool(description="生成开发信模板")
    def generate_email(self, company_name: str, contact: str = "", industry: str = "", 
                       product_info: str = "", email_type: str = "standard") -> Dict[str, str]:
        templates = {
            "standard": self._generate_standard_email,
            "personalized": self._generate_personalized_email,
            "follow_up": self._generate_follow_up_email,
            "cold": self._generate_cold_email
        }
        
        template_func = templates.get(email_type, self._generate_standard_email)
        return template_func(company_name, contact, industry, product_info)
    
    def _generate_standard_email(self, company_name: str, contact: str, industry: str, product_info: str) -> Dict[str, str]:
        subject = f"Business Opportunity for {company_name} in {industry}" if industry else f"Business Opportunity for {company_name}"
        
        body = f"""Dear {contact if contact else 'Team'},

I hope this email finds you well. My name is [Your Name], and I represent [Your Company Name], a leading provider of {product_info if product_info else 'high-quality products/services'}.

After researching {company_name}, I believe there could be excellent synergy between our companies. We have successfully served numerous clients in the {industry} sector and would welcome the opportunity to discuss how we can support your business goals.

Would you be available for a brief call next week to explore potential collaboration? Please let me know a time that works best for you.

Looking forward to hearing from you.

Best regards,
[Your Name]
[Your Title]
[Your Company Name]
[Your Contact Information]
"""
        
        return {"subject": subject, "body": body}
    
    def _generate_personalized_email(self, company_name: str, contact: str, industry: str, product_info: str) -> Dict[str, str]:
        subject = f"Personalized Solution for {company_name}"
        
        body = f"""Dear {contact if contact else 'Decision Maker'},

I've been following {company_name}'s impressive work in the {industry} sector and wanted to reach out personally.

At [Your Company Name], we specialize in {product_info if product_info else 'tailored solutions'} that have helped companies like yours achieve significant results. I'd love to share how our approach could specifically benefit {company_name}'s objectives.

Could we schedule a 15-minute call to discuss your current challenges and explore how we might collaborate?

Best regards,
[Your Name]
[Your Title]
[Your Company Name]
"""
        
        return {"subject": subject, "body": body}
    
    def _generate_follow_up_email(self, company_name: str, contact: str, industry: str, product_info: str) -> Dict[str, str]:
        subject = f"Following up on our previous communication"
        
        body = f"""Dear {contact if contact else 'Team'},

I hope you're doing well. I wanted to follow up on my previous email regarding potential collaboration between [Your Company Name] and {company_name}.

We've helped many companies in the {industry} space enhance their operations with {product_info if product_info else 'our solutions'}, and I believe we could bring similar value to your team.

If you have any questions or would like to discuss further, please don't hesitate to reach out.

Best regards,
[Your Name]
[Your Company Name]
"""
        
        return {"subject": subject, "body": body}
    
    def _generate_cold_email(self, company_name: str, contact: str, industry: str, product_info: str) -> Dict[str, str]:
        subject = f"Quick question about {industry} solutions"
        
        body = f"""Hi {contact if contact else 'There'},

I hope this message finds you well. My name is [Your Name] from [Your Company Name].

I noticed {company_name} is active in the {industry} sector and thought I'd reach out to share how we've helped similar businesses streamline their operations and drive growth.

Would you have 5 minutes to chat about your current priorities? I'd be happy to share a quick case study or answer any questions you might have.

Best,
[Your Name]
[Your Company Name]
[Phone Number]
"""
        
        return {"subject": subject, "body": body}
    
    @Tool(description="发送邮件")
    def send_email(self, to_email: str, subject: str, body: str, 
                   cc_emails: List[str] = [], bcc_emails: List[str] = [],
                   from_name: str = "Trade Agent") -> Dict[str, Any]:
        try:
            msg = MIMEMultipart()
            msg['From'] = formataddr((from_name, config.email['sender_email']))
            msg['To'] = to_email
            msg['Subject'] = subject
            
            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(config.email['smtp_server'], config.email['smtp_port'])
            server.starttls()
            server.login(config.email['smtp_username'], config.email['smtp_password'])
            
            all_recipients = [to_email] + cc_emails + bcc_emails
            server.sendmail(config.email['sender_email'], all_recipients, msg.as_string())
            server.quit()
            
            logger.info(f"邮件发送成功: {to_email}")
            return {"status": "success", "to_email": to_email, "message": "邮件发送成功"}
        except Exception as e:
            logger.error(f"邮件发送失败 {to_email}: {e}")
            return {"status": "failed", "to_email": to_email, "error": str(e)}
    
    @Tool(description="批量发送邮件")
    def batch_send_emails(self, emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for email_data in emails:
            result = self.send_email(
                to_email=email_data.get("to_email", ""),
                subject=email_data.get("subject", ""),
                body=email_data.get("body", ""),
                cc_emails=email_data.get("cc_emails", []),
                bcc_emails=email_data.get("bcc_emails", []),
                from_name=email_data.get("from_name", "Trade Agent")
            )
            results.append(result)
        return results
    
    @Tool(description="生成并发送开发信")
    def generate_and_send(self, company_name: str, to_email: str, contact: str = "", 
                         industry: str = "", product_info: str = "", 
                         email_type: str = "standard") -> Dict[str, Any]:
        email_content = self.generate_email(company_name, contact, industry, product_info, email_type)
        return self.send_email(to_email, email_content["subject"], email_content["body"])

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8005)