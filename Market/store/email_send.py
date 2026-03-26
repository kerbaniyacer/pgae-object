import resend
import os
import random
import string
from datetime import datetime
 
# ضع الـ API key هنا أو في متغير بيئي
resend.api_key = os.environ.get("RESEND_API_KEY", "re_6dKqKhbJ_DW8j5etZ9QBMnjuiDja9Vj8J")
 
SITE_NAME = "سوق"
SITE_URL = "http://127.0.0.1:8000"
FROM_EMAIL = "onboarding@resend.dev"
 
 
# ============================================================
# 1. رسالة رمز التحقق (OTP)
# ============================================================
def send_otp_to_email(to_email: str, otp_code: str, username: str = ""):
    html = f"""
    <div dir="rtl" style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 10px;">
        <h2 style="color: #2d6a4f; text-align: center;">{SITE_NAME}</h2>
        <hr style="border: 1px solid #e0e0e0;">
        <h3 style="color: #333;">مرحباً {username} 👋</h3>
        <p style="color: #555;">استخدم رمز التحقق التالي لإتمام العملية:</p>
        <div style="text-align: center; margin: 30px 0;">
            <span style="font-size: 36px; font-weight: bold; letter-spacing: 10px; color: #2d6a4f; background: #f0f7f4; padding: 15px 30px; border-radius: 10px;">
                {otp_code}
            </span>
        </div>
        <p style="color: #888; font-size: 13px;">⏳ هذا الرمز صالح لمدة <strong>10 دقائق</strong> فقط.</p>
        <p style="color: #888; font-size: 13px;">⚠️ إذا لم تطلب هذا الرمز، تجاهل هذه الرسالة.</p>
        <hr style="border: 1px solid #e0e0e0;">
        <p style="color: #aaa; font-size: 12px; text-align: center;">© {datetime.now().year} {SITE_NAME} - جميع الحقوق محفوظة</p>
    </div>
    """
    return resend.Emails.send({
        "from": FROM_EMAIL,
        "to": to_email,
        "subject": f"🔐 رمز التحقق الخاص بك - {SITE_NAME}",
        "html": html
    })
 
 
# ============================================================
# 2. رسالة تأكيد التسجيل
# ============================================================
def send_registration_confirmation(to_email: str, username: str):
    html = f"""
    <div dir="rtl" style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 10px;">
        <h2 style="color: #2d6a4f; text-align: center;">{SITE_NAME}</h2>
        <hr style="border: 1px solid #e0e0e0;">
        <h3 style="color: #333;">🎉 أهلاً وسهلاً {username}!</h3>
        <p style="color: #555;">يسعدنا انضمامك إلى منصة <strong>{SITE_NAME}</strong>. تم إنشاء حسابك بنجاح.</p>
        <div style="background: #f0f7f4; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <p style="margin: 5px 0; color: #555;">✅ اسم المستخدم: <strong>{username}</strong></p>
            <p style="margin: 5px 0; color: #555;">✅ البريد الإلكتروني: <strong>{to_email}</strong></p>
            <p style="margin: 5px 0; color: #555;">✅ تاريخ التسجيل: <strong>{datetime.now().strftime('%Y-%m-%d %H:%M')}</strong></p>
        </div>
        <div style="text-align: center; margin: 25px 0;">
            <a href="{SITE_URL}/login/" style="background: #2d6a4f; color: white; padding: 12px 30px; border-radius: 8px; text-decoration: none; font-size: 16px;">
                ابدأ التسوق الآن ←
            </a>
        </div>
        <hr style="border: 1px solid #e0e0e0;">
        <p style="color: #aaa; font-size: 12px; text-align: center;">© {datetime.now().year} {SITE_NAME} - جميع الحقوق محفوظة</p>
    </div>
    """
    return resend.Emails.send({
        "from": FROM_EMAIL,
        "to": to_email,
        "subject": f"🎉 مرحباً بك في {SITE_NAME} - تم إنشاء حسابك بنجاح",
        "html": html
    })
 
 
# ============================================================
# 3. رسالة تأكيد البريد الإلكتروني
# ============================================================
def send_email_verification(to_email: str, username: str, verification_link: str):
    html = f"""
    <div dir="rtl" style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 10px;">
        <h2 style="color: #2d6a4f; text-align: center;">{SITE_NAME}</h2>
        <hr style="border: 1px solid #e0e0e0;">
        <h3 style="color: #333;">مرحباً {username} 👋</h3>
        <p style="color: #555;">شكراً لتسجيلك! يرجى تأكيد بريدك الإلكتروني بالنقر على الزر أدناه:</p>
        <div style="text-align: center; margin: 25px 0;">
            <a href="{verification_link}" style="background: #2d6a4f; color: white; padding: 12px 30px; border-radius: 8px; text-decoration: none; font-size: 16px;">
                ✅ تأكيد البريد الإلكتروني
            </a>
        </div>
        <p style="color: #888; font-size: 13px;">أو انسخ هذا الرابط في متصفحك:</p>
        <p style="color: #2d6a4f; font-size: 12px; word-break: break-all;">{verification_link}</p>
        <p style="color: #888; font-size: 13px;">⏳ هذا الرابط صالح لمدة <strong>24 ساعة</strong>.</p>
        <p style="color: #888; font-size: 13px;">⚠️ إذا لم تنشئ هذا الحساب، تجاهل هذه الرسالة.</p>
        <hr style="border: 1px solid #e0e0e0;">
        <p style="color: #aaa; font-size: 12px; text-align: center;">© {datetime.now().year} {SITE_NAME} - جميع الحقوق محفوظة</p>
    </div>
    """
    return resend.Emails.send({
        "from": FROM_EMAIL,
        "to": to_email,
        "subject": f"✅ تأكيد بريدك الإلكتروني - {SITE_NAME}",
        "html": html
    })
 
 
# ============================================================
# 4. رسالة إعادة تعيين كلمة المرور
# ============================================================
def send_password_reset(to_email: str, username: str, reset_link: str):
    html = f"""
    <div dir="rtl" style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 10px;">
        <h2 style="color: #2d6a4f; text-align: center;">{SITE_NAME}</h2>
        <hr style="border: 1px solid #e0e0e0;">
        <h3 style="color: #333;">مرحباً {username} 👋</h3>
        <p style="color: #555;">تلقينا طلباً لإعادة تعيين كلمة المرور الخاصة بحسابك.</p>
        <div style="text-align: center; margin: 25px 0;">
            <a href="{reset_link}" style="background: #c0392b; color: white; padding: 12px 30px; border-radius: 8px; text-decoration: none; font-size: 16px;">
                🔑 إعادة تعيين كلمة المرور
            </a>
        </div>
        <p style="color: #888; font-size: 13px;">⏳ هذا الرابط صالح لمدة <strong>1 ساعة</strong> فقط.</p>
        <p style="color: #888; font-size: 13px;">⚠️ إذا لم تطلب إعادة التعيين، تجاهل هذه الرسالة. حسابك بأمان.</p>
        <hr style="border: 1px solid #e0e0e0;">
        <p style="color: #aaa; font-size: 12px; text-align: center;">© {datetime.now().year} {SITE_NAME} - جميع الحقوق محفوظة</p>
    </div>
    """
    return resend.Emails.send({
        "from": FROM_EMAIL,
        "to": to_email,
        "subject": f"🔑 إعادة تعيين كلمة المرور - {SITE_NAME}",
        "html": html
    })
 
 
# ============================================================
# 5. رسالة تأكيد الطلب
# ============================================================
def send_order_confirmation(to_email: str, username: str, order_id: str, total: str, items: list):
    items_html = "".join([
        f"<tr><td style='padding:8px;border-bottom:1px solid #eee;'>{item['name']}</td>"
        f"<td style='padding:8px;border-bottom:1px solid #eee;text-align:center;'>{item['qty']}</td>"
        f"<td style='padding:8px;border-bottom:1px solid #eee;text-align:left;'>{item['price']} دج</td></tr>"
        for item in items
    ])
    html = f"""
    <div dir="rtl" style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 10px;">
        <h2 style="color: #2d6a4f; text-align: center;">{SITE_NAME}</h2>
        <hr style="border: 1px solid #e0e0e0;">
        <h3 style="color: #333;">شكراً لطلبك {username}! 🛍️</h3>
        <p style="color: #555;">تم استلام طلبك بنجاح. سنقوم بمعالجته في أقرب وقت.</p>
        <div style="background: #f0f7f4; padding: 10px 15px; border-radius: 8px; margin: 15px 0;">
            <p style="margin: 5px 0;">📦 رقم الطلب: <strong>#{order_id}</strong></p>
            <p style="margin: 5px 0;">📅 التاريخ: <strong>{datetime.now().strftime('%Y-%m-%d %H:%M')}</strong></p>
        </div>
        <table style="width:100%; border-collapse:collapse; margin: 15px 0;">
            <thead>
                <tr style="background:#2d6a4f; color:white;">
                    <th style="padding:10px; text-align:right;">المنتج</th>
                    <th style="padding:10px; text-align:center;">الكمية</th>
                    <th style="padding:10px; text-align:left;">السعر</th>
                </tr>
            </thead>
            <tbody>{items_html}</tbody>
            <tfoot>
                <tr>
                    <td colspan="2" style="padding:10px; font-weight:bold; text-align:right;">المجموع الكلي:</td>
                    <td style="padding:10px; font-weight:bold; color:#2d6a4f;">{total} دج</td>
                </tr>
            </tfoot>
        </table>
        <div style="text-align: center; margin: 20px 0;">
            <a href="{SITE_URL}/orders/" style="background: #2d6a4f; color: white; padding: 12px 30px; border-radius: 8px; text-decoration: none;">
                تتبع طلبك ←
            </a>
        </div>
        <hr style="border: 1px solid #e0e0e0;">
        <p style="color: #aaa; font-size: 12px; text-align: center;">© {datetime.now().year} {SITE_NAME} - جميع الحقوق محفوظة</p>
    </div>
    """
    return resend.Emails.send({
        "from": FROM_EMAIL,
        "to": to_email,
        "subject": f"🛍️ تأكيد طلبك #{order_id} - {SITE_NAME}",
        "html": html
    })
 
 
# ============================================================
# 6. رسالة تغيير كلمة المرور بنجاح
# ============================================================
def send_password_changed(to_email: str, username: str):
    html = f"""
    <div dir="rtl" style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 10px;">
        <h2 style="color: #2d6a4f; text-align: center;">{SITE_NAME}</h2>
        <hr style="border: 1px solid #e0e0e0;">
        <h3 style="color: #333;">مرحباً {username} 👋</h3>
        <p style="color: #555;">تم تغيير كلمة المرور الخاصة بحسابك بنجاح.</p>
        <div style="background: #fff3cd; padding: 15px; border-radius: 8px; border-right: 4px solid #ffc107; margin: 15px 0;">
            <p style="color: #856404; margin: 0;">⚠️ إذا لم تقم بهذا التغيير، يرجى التواصل معنا فوراً أو إعادة تعيين كلمة المرور.</p>
        </div>
        <div style="text-align: center; margin: 20px 0;">
            <a href="{SITE_URL}/change-password/" style="background: #c0392b; color: white; padding: 12px 30px; border-radius: 8px; text-decoration: none;">
                🔑 تغيير كلمة المرور مجدداً
            </a>
        </div>
        <hr style="border: 1px solid #e0e0e0;">
        <p style="color: #aaa; font-size: 12px; text-align: center;">© {datetime.now().year} {SITE_NAME} - جميع الحقوق محفوظة</p>
    </div>
    """
    return resend.Emails.send({
        "from": FROM_EMAIL,
        "to": to_email,
        "subject": f"🔐 تم تغيير كلمة المرور - {SITE_NAME}",
        "html": html
    })
 
 
# ============================================================
# مولّد رمز OTP عشوائي
# ============================================================
def generate_otp(length: int = 6) -> str:
    return ''.join(random.choices(string.digits, k=length))
 
 
# ============================================================
# تجربة الإرسال
# ============================================================
if __name__ == "__main__":
    TEST_EMAIL = "keryacer@gmail.com"
 
    print("1. إرسال رمز التحقق...")
    otp = generate_otp()
    r = send_otp_email(TEST_EMAIL, otp, "أحمد")
    print(f"   ✅ تم - ID: {r['id']} | الرمز: {otp}")
 
    print("2. إرسال تأكيد التسجيل...")
    r = send_registration_confirmation(TEST_EMAIL, "أحمد")
    print(f"   ✅ تم - ID: {r['id']}")
 
    print("3. إرسال تأكيد البريد الإلكتروني...")
    r = send_email_verification(TEST_EMAIL, "أحمد", f"{SITE_URL}/verify/?token=abc123")
    print(f"   ✅ تم - ID: {r['id']}")
 
    print("4. إرسال إعادة تعيين كلمة المرور...")
    r = send_password_reset(TEST_EMAIL, "أحمد", f"{SITE_URL}/reset/?token=xyz789")
    print(f"   ✅ تم - ID: {r['id']}")
 
    print("5. إرسال تأكيد الطلب...")
    r = send_order_confirmation(TEST_EMAIL, "أحمد", "1042", "4500", [
        {"name": "قميص قطني", "qty": 2, "price": 1500},
        {"name": "حذاء رياضي", "qty": 1, "price": 1500},
    ])
    print(f"   ✅ تم - ID: {r['id']}")
 
    print("6. إرسال تغيير كلمة المرور...")
    r = send_password_changed(TEST_EMAIL, "أحمد")
    print(f"   ✅ تم - ID: {r['id']}")
 