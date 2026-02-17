import os
import subprocess
from datetime import datetime
import boto3
from botocore.exceptions import NoCredentialsError

def backup_postgres():
    """
    Dumps the PostgreSQL database and uploads it to S3 (optional).
    """
    db_name = os.getenv("POSTGRES_DB", "xocoadb")
    db_user = os.getenv("POSTGRES_USER", "xocoa")
    db_pass = os.getenv("POSTGRES_PASSWORD", "xocoa")
    db_host = os.getenv("DB_HOST", "db")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{db_name}_{timestamp}.sql.gz"
    filepath = f"/tmp/{filename}"

    print(f"📦 Starting backup of {db_name}...")
    
    # Run pg_dump
    try:
        env = os.environ.copy()
        env["PGPASSWORD"] = db_pass
        cmd = f"pg_dump -h {db_host} -U {db_user} {db_name} | gzip > {filepath}"
        subprocess.run(cmd, shell=True, check=True, env=env)
        print(f"✅ Backup created: {filepath}")
    except subprocess.CalledProcessError as e:
        print(f"❌ pg_dump failed: {e}")
        return

    # Upload to S3 if configured
    s3_bucket = os.getenv("S3_BACKUP_BUCKET")
    if s3_bucket:
        try:
            s3 = boto3.client('s3')
            s3.upload_file(filepath, s3_bucket, filename)
            print(f"☁️ Uploaded to S3: s3://{s3_bucket}/{filename}")
        except Exception as e:
            print(f"❌ S3 upload failed: {e}")
    else:
        print("ℹ️ S3_BACKUP_BUCKET not set, keeping local copy only.")

    # Cleanup local copy if uploaded, or keep last N?
    # For now, we'll leave it in /tmp or a dedicated volume.

if __name__ == "__main__":
    backup_postgres()
