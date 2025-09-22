import os
import base64
import requests
from io import BytesIO
from mimetypes import guess_type
from mastodon import Mastodon
from bs4 import BeautifulSoup
import time
from openai import OpenAI
from dotenv import load_dotenv

# --- Load environment variables from .env and override existing ones ---
load_dotenv(override=True)  # force dotenv to overwrite existing environment variables

access_token = os.getenv("MASTODON_ACCESS_TOKEN")
openai_key = os.getenv("OPENAI_API_KEY")
mastodon_base_url = os.getenv("MASTODON_BASE_URL")

# --- Simple validation ---
if not access_token or not openai_key or not mastodon_base_url:
    raise ValueError("MASTODON_ACCESS_TOKEN, OPENAI_API_KEY, and MASTODON_BASE_URL must be set in .env")

# --- Mastodon configuration ---
mastodon = Mastodon(
    access_token=access_token,
    api_base_url=mastodon_base_url
)

# --- OpenAI configuration ---
client = OpenAI(api_key=openai_key)
MODEL = "gpt-4o-mini"
DETAIL_LEVEL = "low"  # "low" = cheaper, "high" = more detailed

# --- Helper functions ---
def encode_image_from_url(image_url):
    response = requests.get(image_url)
    response.raise_for_status()
    return base64.b64encode(response.content).decode("utf-8")

def analyze_image_with_gpt(image_url):
    print(f"Analyzing image {image_url} with GPT-4o-mini...")

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this image in clear and concise alt-text."},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        ],
    )

    description = response.choices[0].message.content.strip()
    print(f"Generated description: {description}")
    return description

def reupload_image(image_data, image_url, analysis):
    mime_type = guess_type(image_url)[0] or 'application/octet-stream'
    new_media = mastodon.media_post(BytesIO(base64.b64decode(image_data)), mime_type=mime_type, description=analysis)
    return new_media['id']

def update_post_with_new_images(post_id, new_media_ids):
    original_post = mastodon.status(post_id)
    original_text = BeautifulSoup(original_post['content'], 'html.parser').get_text()
    headers = {'Authorization': f'Bearer {access_token}'}  # Token from .env
    data = {'status': original_text, 'media_ids[]': new_media_ids}
    put_url = f'{mastodon.api_base_url}/api/v1/statuses/{post_id}'
    response = requests.put(put_url, headers=headers, data=data)
    return response

def fetch_and_analyze_images():
    user_account = mastodon.account_verify_credentials()
    user_id = user_account['id']
    print("Fetching recent posts...")
    posts = mastodon.account_statuses(user_id, limit=20)

    for post in posts:
        new_media_ids = []
        for attachment in post.get('media_attachments', []):
            if attachment['type'] == 'image' and (not attachment['description'] or not attachment['description'].strip()):
                print(f"Image found in post: {attachment['url']}")
                try:
                    analysis = analyze_image_with_gpt(attachment['url'])
                    base64_image = encode_image_from_url(attachment['url'])
                    new_media_id = reupload_image(base64_image, attachment['url'], analysis)
                    new_media_ids.append(new_media_id)
                except Exception as e:
                    print(f"Error analyzing or re-uploading: {e}")
            else:
                print("Image already has alt-text or is not an image.")

        if new_media_ids:
            print(f"Updating post ID: {post['id']} with new images.")
            response = update_post_with_new_images(post['id'], new_media_ids)
            if response.status_code == 200:
                print("Post updated successfully.")
            else:
                print(f"Failed to update post. Response: {response.status_code}, {response.text}")

# --- Main loop ---
if __name__ == "__main__":
    try:
        while True:
            fetch_and_analyze_images()
            time.sleep(60)  # wait 60 seconds before next run
    except KeyboardInterrupt:
        print("\nScript stopped by user.")
    except Exception as e:
        print(f"Critical error: {e}")
