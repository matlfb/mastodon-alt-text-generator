import base64
import requests
from io import BytesIO
from mimetypes import guess_type
from mastodon import Mastodon
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials
from bs4 import BeautifulSoup
import time
import re

# Mastodon Configuration
mastodon = Mastodon(
    client_id='YOUR_CLIENT_ID',
    client_secret='YOUR_CLIENT_SECRET',
    access_token='YOUR_ACCESS_TOKEN',
    api_base_url='YOUR_MASTODON_INSTANCE'  # e.g., 'https://mastodon.social'
)

# Azure Computer Vision Configuration
azure_endpoint = "YOUR_AZURE_ENDPOINT"
azure_key = "YOUR_AZURE_KEY"
computervision_client = ComputerVisionClient(azure_endpoint, CognitiveServicesCredentials(azure_key))

def encode_image_from_url(image_url):
    response = requests.get(image_url)
    return base64.b64encode(response.content).decode("utf-8")

def analyze_image_with_azure(image_url):
    print("Analyzing image with Azure...")
    analysis = computervision_client.analyze_image(image_url, visual_features=[VisualFeatureTypes.description])
    if analysis.description.captions:
        description = f"may be a {analysis.description.captions[0].text}"
        return description.capitalize()
    return "May be a scene with no available description."

def analyze_image_with_ocr(image_url):
    print("Analyzing image with Azure OCR...")
    response = requests.get(image_url)
    image_data = BytesIO(response.content)

    ocr_result = computervision_client.recognize_printed_text_in_stream(image_data)
    text_from_image = []

    for region in ocr_result.regions:
        for line in region.lines:
            line_text = " ".join([word.text for word in line.words])
            text_from_image.append(line_text)

    return " ".join(text_from_image) if text_from_image else None

def reupload_image(image_data, image_url, analysis):
    mime_type = guess_type(image_url)[0] or 'application/octet-stream'
    new_media = mastodon.media_post(BytesIO(base64.b64decode(image_data)), mime_type=mime_type, description=analysis)
    return new_media['id']

def get_post_with_text(post_id):
    post = mastodon.status(post_id)
    post_text = post['content']
    media_attachments = post.get('media_attachments', [])
    return post_text, media_attachments

def clean_html_preserve_newlines(html_content):
    # Replace <br> and </p><p> with newlines
    html_content = re.sub(r'<br\s*/?>', '\n', html_content)
    html_content = re.sub(r'</p>\s*<p>', '\n\n', html_content)
    
    # Use BeautifulSoup to remove all other HTML tags
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text()
    
    # Preserve multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()

def update_post_with_media(post_id, media_ids):
    post_text, media_attachments = get_post_with_text(post_id)
    
    # Clean HTML while preserving newlines
    post_text_cleaned = clean_html_preserve_newlines(post_text)

    headers = {'Authorization': f'Bearer {mastodon.access_token}'}
    data = {
        'status': post_text_cleaned,
        'media_ids[]': media_ids
    }
    put_url = f'{mastodon.api_base_url}/api/v1/statuses/{post_id}'
    response = requests.put(put_url, headers=headers, data=data)
    return response

def fetch_and_analyze_images():
    user_account = mastodon.account_verify_credentials()
    user_id = user_account['id']

    print("Retrieving posts...")
    posts = mastodon.account_statuses(user_id, limit=20)

    for post in posts:
        new_media_ids = []
        for attachment in post.get('media_attachments', []):
            if attachment['type'] == 'image' and (attachment['description'] is None or attachment['description'].strip() == ''):
                print(f"Found image in post: {attachment['url']}")
                
                analysis = analyze_image_with_azure(attachment['url'])
                print("Analysis completed.")
                print(analysis)

                ocr_text = analyze_image_with_ocr(attachment['url'])
                if ocr_text:
                    print("Text extracted from image with OCR:")
                    print(ocr_text)
                    analysis += f"\n\nText extracted: {ocr_text}"

                base64_image = encode_image_from_url(attachment['url'])
                new_media_id = reupload_image(base64_image, attachment['url'], analysis)
                new_media_ids.append(new_media_id)
            else:
                print("Image already has alt text or is not an image.")

        if new_media_ids:
            print(f"Updating post ID: {post['id']} with new images.")
            response = update_post_with_media(post['id'], new_media_ids)
            if response.status_code == 200:
                print("Post updated successfully.")
            else:
                print(f"Failed to update post. Response: {response.status_code}, {response.text}")

if __name__ == "__main__":
    try:
        while True:  # Adding the infinite loop
            fetch_and_analyze_images()
            time.sleep(60)  # Wait 60 seconds before next execution
    except requests.exceptions.TooManyRedirects as e:
        print(f"Redirection error: {e}")
    except requests.exceptions.RequestException as e:
        print(f"A request error occurred: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
