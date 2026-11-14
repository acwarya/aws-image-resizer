import io
import os
import urllib.parse

import boto3
from PIL import Image, ImageOps

s3 = boto3.client("s3")
DEST = os.environ["DEST_BUCKET"]
SIZE = (256, 256)


def handler(event, context):
    for rec in event["Records"]:
        bucket = rec["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(rec["s3"]["object"]["key"])

        body = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
        img = Image.open(io.BytesIO(body))
        fmt = img.format
        img = ImageOps.exif_transpose(img)  # fix phone-photo rotation
        img.thumbnail(SIZE)

        buf = io.BytesIO()
        img.save(buf, fmt)
        buf.seek(0)

        s3.put_object(
            Bucket=DEST,
            Key=f"thumb-{key}",
            Body=buf,
            ContentType=Image.MIME[fmt],
        )
        print(f"Resized {key} -> {DEST}/thumb-{key}")
