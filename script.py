import base64
import requests
from io import BytesIO
from mimetypes import guess_type
from mastodon import Mastodon
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials

# Mastodon configuration
mastodon = Mastodon(
    client_id='XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX',
    client_secret='XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX',
    access_token='XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX',
    api_base_url='https://your.instance'
)

# Azure Computer Vision configuration
azure_endpoint = "https://XXXXXXXX.cognitiveservices.azure.com/"  # Replace with your Azure endpoint
azure_key = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"  # Replace with your Azure key
computervision_client = ComputerVisionClient(azure_endpoint, CognitiveServicesCredentials(azure_key))

# Function to encode an image from a URL to base64
def encode_image_from_url(image_url):
    response = requests.get(image_url)
    return base64.b64encode(response.content).decode("utf-8")

# Function to analyze the image with Azure and format the alt text
def analyze_image_with_azure(image_url):
    print("Analyzing the image with Azure...")
    analysis = computervision_client.analyze_image(image_url, visual_features=[VisualFeatureTypes.description])
    if analysis.description.captions:
        description = f"may be a {analysis.description.captions[0].text}"
        return description.capitalize()
    return "May be a scene with no available description."

# Function to analyze the image with Azure's OCR and add the extracted text
def analyze_image_with_ocr(image_url):
    print("Analyzing the image with Azure OCR...")
    response = requests.get(image_url)
    image_data = BytesIO(response.content)

    ocr_result = computervision_client.recognize_printed_text_in_stream(image_data)
    text_from_image = []

    for region in ocr_result.regions:
        for line in region.lines:
            line_text = " ".join([word.text for word in line.words])
            text_from_image.append(line_text)

    return " ".join(text_from_image) if text_from_image else None

# Function to re-upload the image with the generated description
def reupload_image(image_data, image_url, analysis):
    mime_type = guess_type(image_url)[0] or 'application/octet-stream'
    new_media = mastodon.media_post(BytesIO(base64.b64decode(image_data)), mime_type=mime_type, description=analysis)
    return new_media['id']

from bs4 import BeautifulSoup

# Function to update the post with the new images and descriptions
def update_post_with_new_images(post_id, new_media_ids):
    original_post = mastodon.status(post_id)
    original_text = BeautifulSoup(original_post['content'], 'html.parser').get_text()

    headers = {'Authorization': f'Bearer {mastodon.access_token}'}
    data = {
        'status': original_text,
        'media_ids[]': new_media_ids
    }
    put_url = f'{mastodon.api_base_url}/api/v1/statuses/{post_id}'
    response = requests.put(put_url, headers=headers, data=data)
    return response

# Main function to fetch, analyze, and update the posts
def fetch_and_analyze_images():
    user_account = mastodon.account_verify_credentials()
    user_id = user_account['id']

    print("Fetching posts...")
    posts = mastodon.account_statuses(user_id, limit=20)

    for post in posts:
        new_media_ids = []
        for attachment in post.get('media_attachments', []):
            if attachment['type'] == 'image' and (attachment['description'] is None or attachment['description'].strip() == ''):
                print(f"Image found in a post: {attachment['url']}")
                
                # Analyze the image with Azure
                analysis = analyze_image_with_azure(attachment['url'])
                print("Analysis completed.")
                print(analysis)

                # Analyze the image with OCR
                ocr_text = analyze_image_with_ocr(attachment['url'])
                if ocr_text:
                    print("Text extracted from the image with OCR:")
                    print(ocr_text)
                    # Combine the description and extracted text with a blank line
                    analysis += f"\n\nText extracted: {ocr_text}"

                    # Add an interpretation if it's a chart with a blank line before
                    if "chart" in analysis:
                        analysis += f"\n\nThis chart shows the difference in followings between Republicans and Democrats."
                
                base64_image = encode_image_from_url(attachment['url'])
                new_media_id = reupload_image(base64_image, attachment['url'], analysis)
                new_media_ids.append(new_media_id)
            else:
                print("The image already has an alt text or is not an image.")

        if new_media_ids:
            print(f"Updating post ID: {post['id']} with the new images.")
            response = update_post_with_new_images(post['id'], new_media_ids)
            if response.status_code == 200:
                print("Post updated successfully.")
            else:
                print(f"Failed to update the post. Response: {response.status_code}, {response.text}")

if __name__ == "__main__":
    fetch_and_analyze_images()
