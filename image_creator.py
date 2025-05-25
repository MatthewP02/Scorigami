import requests
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
import os

load_dotenv()

HCTI_API_ENDPOINT = "https://hcti.io/v1/image"
# Retrieve these from https://htmlcsstoimage.com/dashboard
HCTI_API_USER_ID = os.getenv('HCTI_API_USER_ID')
HCTI_API_KEY = os.getenv('HCTI_API_KEY')

# Function to fetch team logos
def fetch_logo(team_id):
    url = f"https://cdn.collegefootballdata.com/logos/500/{team_id}.png"
    return url

# Function to crop the center of the image
def crop_center(image, crop_width, crop_height):
    img_width, img_height = image.size
    left = (img_width - crop_width) / 2
    top = (img_height - crop_height) / 2
    right = (img_width + crop_width) / 2
    bottom = (img_height + crop_height) / 2
    return image.crop((left, top, right, bottom))

# Function to get the color and text for the Scorigami flag
def get_scorigami_status(status):
    if status == 0:
        return "No Scorigami", "#b23b3b"  # Dimmed red
    elif status == 1:
        return "Scorigami!", "#4b9f4b"  # Dimmed green
    elif status == 2:
        return "Potential Scorigami", "#d3b84b"  # Dimmed yellow

# Function to create score image using WeasyPrint
def create_score_image(home_team_id, away_team_id, home_team_name, away_team_name, home_score, away_score, period, time_left, scorigami_status):
    # Fetch logos
    home_logo = fetch_logo(home_team_id)
    away_logo = fetch_logo(away_team_id)

    # Get Scorigami flag details
    scorigami_text, scorigami_color = get_scorigami_status(scorigami_status)

    # HTML structure with dynamic data
    data = {'html': f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CFB Scorigami Score</title>
        <style>
            body {{
                font-family: 'Roboto', sans-serif;
                background: #121212;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }}

            .scoreboard {{
                background: #1f1f1f;
                width: 750px;
                height: 350px;
                border-radius: 20px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                color: #ffffff;
                padding: 20px;
                position: relative;
            }}

            .team-section {{
                display: flex;
                flex-direction: column;
                align-items: center;
                flex: 0.4;
                padding-top: 10px;
            }}

            .team-section img {{
                width: 200px;
                height: 200px;
                margin-bottom: 10px;
                object-fit: contain;
            }}

            .team-name {{
                font-size: 24px;
                font-weight: 400;
                color: rgba(255, 255, 255, 0.8);
                text-align: center;
            }}

            .scores {{
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                font-size: 100px;
                font-weight: 700;
                flex: 0.3;
            }}

            .info {{
                font-size: 20px;
                text-align: left;
                padding: 10px 20px;
                border-radius: 10px;
                background-color: rgba(255, 255, 255, 0.1);
                position: absolute;
                justify-content: center;
                align-items: center;
                bottom: 20px;
                left: 20px;
            }}

            .branding {{
                position: absolute;
                font-size: 18px;
                font-weight: 700;
                top: 20px;
                left: 20px;
                color: #333333;
            }}

            .scorigami-flag {{
                position: absolute;
                bottom: 20px;
                right: 20px;
                background-color: {scorigami_color};
                color: white;
                font-size: 24px;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 10px;
            }}
        </style>
    </head>
    <body>

    <div class="scoreboard">
        <div class="team-section">
            <img src="{away_logo}" alt="{away_team_name} Logo">
            <div class="team-name">{away_team_name}</div>
        </div>
        <div class="scores">
            <div>{away_score}</div>
            <div>{home_score}</div>
        </div>
        <div class="team-section">
            <img src="{home_logo}" alt="{home_team_name} Logo">
            <div class="team-name">{home_team_name}</div>
        </div>

        <div class="info">{period} Quarter | {time_left} Left</div>
        <div class="branding">@CFBScorigami_</div>
        <div class="scorigami-flag">{scorigami_text}</div>
    </div>

    </body>
    </html>
    """}

    image_response = requests.post(url=HCTI_API_ENDPOINT, data=data, auth=(HCTI_API_USER_ID, HCTI_API_KEY))
    image_url = image_response.json()['url']
    print(f"Your image URL is: {image_url}")

    # Download the image
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))

    # Crop the image to 750x350 pixels
    cropped_img = crop_center(img, 790, 390)

    # Save the cropped image
    cropped_img.save("cropped_score_image.png")
    print("Image saved as cropped_score_image.png")