import os, hashlib
from django.utils.text import slugify

UPLOAD_DIR = "uploads"  # عدّلها لما تريد

def short_upload_path(instance, filename, max_len=100):
    #حساب المساحة المتاحة للاسم بعد المجلد والشرطة المائلة والامتداد
    name, ext = os.path.splitext(filename)
    safe = slugify(name) or "file"
    # اضافة جزء هاش لضمان التفرد حتى بعد التقصير
    digest = hashlib.sha1(safe.encode()).hexdigest()[:8]
    base = f"{safe}-{digest}"

    # حساب الحد المتاح للاسم داخل المسار الكامل
    # مثال: "uploads/<base><ext>" => طول ثابت = len("uploads/") + len(ext)
    fixed = len(UPLOAD_DIR) + 1 + len(ext)
    avail_for_base = max_len - fixed
    base = base[:max(1, avail_for_base)]  # لا تدعها صفر

    return f"{UPLOAD_DIR}/{base}{ext}"
