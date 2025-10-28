import os
import base64
import requests
from io import BytesIO
from mimetypes import guess_type
from mastodon import Mastodon
from bs4 import BeautifulSoup, NavigableString
import time
from openai import OpenAI
from dotenv import load_dotenv

# --- Load environment variables ---
load_dotenv(override=True)

access_token = os.getenv("MASTODON_ACCESS_TOKEN")
openai_key = os.getenv("OPENAI_API_KEY")
mastodon_base_url = os.getenv("MASTODON_BASE_URL")
lang = os.getenv("ALT_TEXT_LANG", "en")  # Default language: English

# --- Basic validation ---
if not access_token or not openai_key or not mastodon_base_url:
    raise ValueError("MASTODON_ACCESS_TOKEN, OPENAI_API_KEY, and MASTODON_BASE_URL must be set in .env")

print("Detected alt-text language:", lang)

# --- Mastodon setup ---
mastodon = Mastodon(
    access_token=access_token,
    api_base_url=mastodon_base_url
)

# --- OpenAI setup ---
client = OpenAI(api_key=openai_key)
MODEL = "gpt-4o-mini"

# --- Text helpers ---
def html_to_text_preserving_blocks(html: str) -> str:
    """
    Fallback for instances without /api/v1/statuses/:id/source.
    - <p> and <div> become paragraphs separated by blank lines
    - <br> becomes a single line break
    """
    soup = BeautifulSoup(html or "", "html.parser")

    def node_text_with_br(n):
        out = []
        for elem in n.descendants:
            if getattr(elem, "name", None) == "br":
                out.append("\n")
            elif isinstance(elem, NavigableString):
                out.append(str(elem))
        return "".join(out)

    blocks = []
    block_nodes = soup.find_all(["p", "div"])
    if block_nodes:
        for b in block_nodes:
            t = node_text_with_br(b).strip("\n")
            if t:
                blocks.append(t)
        return ("\n\n").join(blocks).strip()

    for br in soup.find_all("br"):
        br.replace_with("\n")
    return soup.get_text().strip()

def get_original_text(post_id: str, original_post) -> str:
    """
    Try to fetch the exact text the user wrote via /api/v1/statuses/:id/source.
    If not supported, fall back to reconstructing text from rendered HTML.
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{mastodon.api_base_url}/api/v1/statuses/{post_id}/source"
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            src = r.json()
            text = src.get("text")
            if text is not None:
                return text
    except Exception:
        pass

    return html_to_text_preserving_blocks(original_post.get("content", ""))

# --- Image & alt-text generation ---
def encode_image_from_url(image_url):
    """Download and encode image to base64."""
    response = requests.get(image_url)
    response.raise_for_status()
    return base64.b64encode(response.content).decode("utf-8")

def analyze_image_with_gpt(image_url):
    """Generate an alt-text description using GPT-4o-mini."""
    print(f"Analyzing image {image_url} with GPT-4o-mini...")

    if lang.lower().startswith("fr"):
        prompt = (
            "Décris cette image en français uniquement, "
            "de manière claire, concise et adaptée pour un texte alternatif (alt-text). "
            "N’utilise pas l’anglais."
        )
    else:
        prompt = "Describe this image in clear, concise English suitable for alt-text. Avoid verbose language."

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        ],
    )

    description = response.choices[0].message.content.strip()
    print(f"Generated description ({lang}): {description}")
    return description

def reupload_image(image_data, image_url, analysis):
    """Re-upload image to Mastodon with the generated alt-text."""
    mime_type = guess_type(image_url)[0] or 'application/octet-stream'
    new_media = mastodon.media_post(
        BytesIO(base64.b64decode(image_data)),
        mime_type=mime_type,
        description=analysis
    )
    return new_media['id']

def update_post_with_new_images(post_id, new_media_ids):
    """Update post with new media while preserving its metadata."""
    original_post = mastodon.status(post_id)

    # Fetch exact original text (preserving newlines)
    text_source = get_original_text(post_id, original_post)

    headers = {"Authorization": f"Bearer {access_token}"}
    data = {
        "status": text_source,
        "media_ids[]": new_media_ids,
        "sensitive": str(original_post.get("sensitive", False)).lower(),
        "spoiler_text": original_post.get("spoiler_text", ""),
        "visibility": original_post.get("visibility", "public"),
        "language": original_post.get("language", lang)
    }

    put_url = f"{mastodon.api_base_url}/api/v1/statuses/{post_id}"
    response = requests.put(put_url, headers=headers, data=data)
    return response

def fetch_and_analyze_images():
    """Fetch recent posts and add alt-texts to images that don't have one."""
    user_account = mastodon.account_verify_credentials()
    user_id = user_account['id']
    print("Fetching recent posts...")
    posts = mastodon.account_statuses(user_id, limit=20)

    for post in posts:
        new_media_ids = []
        for attachment in post.get('media_attachments', []):
            if attachment['type'] == 'image' and (not attachment['description'] or not attachment['description'].strip()):
                print(f"Found image in post: {attachment['url']}")
                try:
                    analysis = analyze_image_with_gpt(attachment['url'])
                    base64_image = encode_image_from_url(attachment['url'])
                    new_media_id = reupload_image(base64_image, attachment['url'], analysis)
                    new_media_ids.append(new_media_id)
                except Exception as e:
                    print(f"Error analyzing or re-uploading image: {e}")
            else:
                print("Image already has alt-text or is not relevant.")

        if new_media_ids:
            print(f"Updating post ID {post['id']} with new images...")
            response = update_post_with_new_images(post['id'], new_media_ids)
            if response.status_code == 200:
                print("✅ Post updated successfully.")
            else:
                print(f"❌ Failed to update post. Status: {response.status_code}, Response: {response.text}")

# --- Main loop ---
if __name__ == "__main__":
    try:
        while True:
            fetch_and_analyze_images()
            time.sleep(60)  # Wait 60 seconds before next check
    except KeyboardInterrupt:
        print("\nScript stopped by user.")
    except Exception as e:
        print(f"Critical error: {e}")
