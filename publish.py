#!/usr/bin/env python3

import os
import sys
import re
import subprocess
from pathlib import Path
from dotenv import load_dotenv
import boto3

# Load environment variables
load_dotenv()

ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
BUCKET_NAME = os.getenv("R2_BUCKET_NAME")

COLLECTIONS = ["presence", "pattern", "light", "made-things", "generated"]

def upload_to_r2(image_path, filename):
    s3 = boto3.client(
        "s3",
        endpoint_url=f"https://{ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=os.getenv("CLOUDFLARE_R2_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("CLOUDFLARE_R2_SECRET_ACCESS_KEY"),
        region_name="auto"
    )
    print(f"Uploading {filename} to R2...")
    s3.upload_file(
        image_path,
        BUCKET_NAME,
        filename,
        ExtraArgs={"ContentType": "image/jpeg"}
    )
    print(f"✓ Uploaded to R2: {filename}")

def update_collection(collection, filename, title, caption):
    collection_path = Path(f"archive/{collection}/index.md")
    
    if not collection_path.exists():
        print(f"✗ Collection not found: {collection}")
        sys.exit(1)

    content = collection_path.read_text()
    
    new_entry = f"  - file: {filename}\n    title: {title}\n    caption: {caption}\n"
    
    # Insert before the closing --- or at end of photos list
    content = content.rstrip()
    content += f"\n  - file: {filename}\n    title: {title}\n    caption: {caption}\n"
    
    collection_path.write_text(content)
    print(f"✓ Updated {collection}/index.md")

def git_push(filename, collection):
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", f"Add {filename} to {collection}"], check=True)
    subprocess.run(["git", "push"], check=True)
    print("✓ Pushed to GitHub")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        prog='publish',
        description='Publish a photo to brianbochicchio.com'
    )
    parser.add_argument('image', help='Path to image file')
    parser.add_argument('--collection', required=True, choices=COLLECTIONS, help='Target collection')
    parser.add_argument('--title', required=True, help='Image title')
    parser.add_argument('--caption', required=True, help='Image caption')
    parser.add_argument('--filename', help='Override R2 filename (default: original filename)')
    
    args = parser.parse_args()
    
    if not Path(args.image).exists():
        print(f"✗ Image not found: {args.image}")
        sys.exit(1)

    filename = args.filename or Path(args.image).name

    print(f"\n📷 brianbochicchio.com publish tool\n")
    print(f"→ Image:      {filename}")
    print(f"→ Collection: {args.collection}")
    print(f"→ Title:      {args.title}")
    print(f"→ Caption:    {args.caption}")
    
    confirm = input("\nProceed? (y/n): ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        sys.exit(0)

    upload_to_r2(args.image, filename)
    update_collection(args.collection, filename, args.title, args.caption)
    git_push(filename, args.collection)
    
    print("\n✓ Done. Site will rebuild in ~60 seconds.")

if __name__ == "__main__":
    main()