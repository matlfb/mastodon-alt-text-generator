import base64
import requests
from io import BytesIO
from mimetypes import guess_type
from mastodon import Mastodon
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials

# Configuration de Mastodon
mastodon = Mastodon(
    client_id='XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX',
    client_secret='XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX',
    access_token='XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX',
    api_base_url='https://zelk.space'
)

# Configuration de Azure Computer Vision
azure_endpoint = "https://XXXXXXXX.cognitiveservices.azure.com/"  # Remplacez par votre point de terminaison Azure
azure_key = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"  # Remplacez par votre clé Azure
computervision_client = ComputerVisionClient(azure_endpoint, CognitiveServicesCredentials(azure_key))

# Fonction pour encoder une image à partir d'une URL en base64
def encode_image_from_url(image_url):
    response = requests.get(image_url)
    return base64.b64encode(response.content).decode("utf-8")

# Fonction pour analyser l'image avec Azure et formater le texte alternatif
def analyze_image_with_azure(image_url):
    print("Analyse de l'image avec Azure...")
    analysis = computervision_client.analyze_image(image_url, visual_features=[VisualFeatureTypes.description])
    if analysis.description.captions:
        description = f"may be a {analysis.description.captions[0].text}"
        return description.capitalize()
    return "May be a scene with no available description."

# Fonction pour analyser l'image avec l'OCR d'Azure et ajouter le texte extrait
def analyze_image_with_ocr(image_url):
    print("Analyse de l'image avec OCR d'Azure...")
    response = requests.get(image_url)
    image_data = BytesIO(response.content)

    ocr_result = computervision_client.recognize_printed_text_in_stream(image_data)
    text_from_image = []

    for region in ocr_result.regions:
        for line in region.lines:
            line_text = " ".join([word.text for word in line.words])
            text_from_image.append(line_text)

    return " ".join(text_from_image) if text_from_image else None

# Fonction pour re-téléverser l'image avec la description générée
def reupload_image(image_data, image_url, analysis):
    mime_type = guess_type(image_url)[0] or 'application/octet-stream'
    new_media = mastodon.media_post(BytesIO(base64.b64decode(image_data)), mime_type=mime_type, description=analysis)
    return new_media['id']

from bs4 import BeautifulSoup

# Fonction pour mettre à jour le post avec les nouvelles images et descriptions
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

# Fonction principale pour récupérer, analyser et mettre à jour les posts
def fetch_and_analyze_images():
    user_account = mastodon.account_verify_credentials()
    user_id = user_account['id']

    print("Récupération des posts...")
    posts = mastodon.account_statuses(user_id, limit=20)

    for post in posts:
        new_media_ids = []
        for attachment in post.get('media_attachments', []):
            if attachment['type'] == 'image' and (attachment['description'] is None or attachment['description'].strip() == ''):
                print(f"Image trouvée dans un post : {attachment['url']}")
                
                # Analyse de l'image avec Azure
                analysis = analyze_image_with_azure(attachment['url'])
                print("Analyse terminée.")
                print(analysis)

                # Analyse de l'image avec OCR
                ocr_text = analyze_image_with_ocr(attachment['url'])
                if ocr_text:
                    print("Texte extrait de l'image avec OCR :")
                    print(ocr_text)
                    # Regrouper la description et le texte extrait avec une ligne vide
                    analysis += f"\n\nText extracted: {ocr_text}"

                    # Ajouter une interprétation si c'est un graphique avec une ligne vide avant
                    if "chart" in analysis:
                        analysis += f"\n\nThis chart shows the difference in followings between Republicans and Democrats."
                
                base64_image = encode_image_from_url(attachment['url'])
                new_media_id = reupload_image(base64_image, attachment['url'], analysis)
                new_media_ids.append(new_media_id)
            else:
                print("L'image a déjà un texte alternatif ou n'est pas une image.")

        if new_media_ids:
            print(f"Mise à jour du post ID : {post['id']} avec les nouvelles images.")
            response = update_post_with_new_images(post['id'], new_media_ids)
            if response.status_code == 200:
                print("Post mis à jour avec succès.")
            else:
                print(f"Échec de la mise à jour du post. Réponse : {response.status_code}, {response.text}")

if __name__ == "__main__":
    fetch_and_analyze_images()
