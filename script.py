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

# --- Load environment variables from .env ---
load_dotenv()
access_token = os.getenv("MASTODON_ACCESS_TOKEN")
openai_key = os.getenv("OPENAI_API_KEY")

# --- Simple check ---
if not access_token or not openai_key:
    raise ValueError("Environment variables MASTODON_ACCESS_TOKEN and OPENAI_API_KEY must be set")

# --- Mastodon configuration ---
# Replace 'mastodon.instance' with your Mastodon instance URL, e.g., 'https://mastodon.social'
mastodon = Mastodon(
    access_token=access_token,
    api_base_url='mastodon.instance'
)

# --- OpenAI configuration ---
client = OpenAI(api_key=openai_key)
MODEL = "gpt-4o-mini"
DETAIL_LEVEL = "low"  # "low" = cheaper, "high" = more detailed

# --- Functions ---
def encode_image_from_url(image_url):
    """Download an image from a URL and encode it as base64"""
    response = requests.get(image_url)
    response.raise_for_status()
    return base64.b64encode(response.content).decode("utf-8")

def analyze_image_with_gpt(image_url):
    """Analyze an image using GPT-4o-mini and return an alt-text description"""
    print(f"Analyzing image {image_url} with GPT-4o-mini...")
    image_data = encode_image_from_url(image_url)

    response = client.responses.create(
        model=MODEL,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "Describe this image in clear and concise alt-text."},
                    {"type": "input_image", "image_url": f"data:image/jpeg;base64,{image_data}", "detail": DETAIL_LEVEL}
                ]
            }
        ]
    )

    description = response.output[0].content[0].text.strip()
    usage = response.usage
    cost_input = usage.input_tokens * 0.15 / 1_000_000
    cost_output = usage.output_tokens * 0.60 / 1_000_000
    total_cost = cost_input + cost_output

    print(f"Generated description: {description}")
    print(f"Estimated cost: ~${total_cost:.6f} (input: {usage.input_tokens} tok, output: {usage.output_tokens} tok)")
    return description

def reupload_image(image_data, image_url, analysis):
    """Re-upload an image to Mastodon with the generated alt-text"""
    mime_type = guess_type(image_url)[0] or 'application/octet-stream'
    new_media = mastodon.media_post(BytesIO(base64.b64decode(image_data)), mime_type=mime_type, description=analysis)
    return new_media['id']

def update_post_with_new_images(post_id, new_media_ids):
    """Update an existing post with new media that has alt-text"""
    original_post = mastodon.status(post_id)
    original_text = BeautifulSoup(original_post['content'], 'html.parser').get_text()
    headers = {'Authorization': f'Bearer {access_token}'}
    data = {'status': original_text, 'media_ids[]': new_media_ids}
    put_url = f'{mastodon.api_base_url}/api/v1/statuses/{post_id}'
    response = requests.put(put_url, headers=headers, data=data)
    return response

def fetch_and_analyze_images():
    """Fetch recent posts, analyze images without alt-text, and update the posts"""
    user_account = mastodon.account_verify_credentials()
    user_id = user_account['id']
    print("Fetching posts...")
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
                    print(f"Error analyzing or re-uploading image: {e}")
            else:
                print("Image already has alt-text or is not an image.")

        if new_media_ids:
            print(f"Updating post ID: {post['id']} with new media.")
            response = update_post_with_new_images(post['id'], new_media_ids)
            if response.status_code == 200:
                print("Post successfully updated.")
            else:
                print(f"Failed to update post. Response: {response.status_code}, {response.text}")

# --- Main loop ---
if __name__ == "__main__":
    try:
        while True:
            fetch_and_analyze_images()
            time.sleep(60)  # wait 60 seconds before the next execution
    except KeyboardInterrupt:
        print("\nScript stopped by user.")
    except Exception as e:
        print(f"Critical error: {e}")
