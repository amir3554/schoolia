import os, boto3
from botocore.exceptions import ClientError
from schoolia import settings
import random
import uuid

BUCKET = settings.AWS_STORAGE_BUCKET_NAME
REGION = settings.AWS_S3_REGION_NAME
UPLOAD_S3_FOLDER = settings.UPLOAD_S3_FOLDER

s3_client = boto3.client(
    "s3",
    region_name=REGION,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )

def upload_fileobj_to_s3(file_obj, key=None, content_type=None):

    _, ext = os.path.splitext(file_obj.name)
    new_filename = f"{uuid.uuid4().hex}{ext}"


    key = f"{UPLOAD_S3_FOLDER}{new_filename}"

    extra = {"ContentType": content_type} if content_type else {}

    if hasattr(file_obj, "seek"):
        try:
            file_obj.seek(0)
        except Exception:
            pass

    if hasattr(file_obj, "open"):
        try:
            file_obj.open()
        except Exception:
            pass

    # رفع الملف
    s3_client.upload_fileobj(file_obj, BUCKET, key, ExtraArgs=extra)

    return key

def public_url(key):
    """
    يبني رابط URL صحيح من المفتاح
    """
    return f"https://{BUCKET}.s3.{REGION}.amazonaws.com/{key}"

