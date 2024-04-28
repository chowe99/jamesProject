from httpx import main
from openai import OpenAI
import requests
from PIL import Image
from io import BytesIO

client = OpenAI()

def generate_story(prompt, image_frequency="arc"):
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="gpt-3.5-turbo"
    )
    # story_text = chat_completion['choices'][0]['message']['content'].strip()
    story_text = chat_completion.choices[0].message.content.strip()

    chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": f"For each {image_frequency} in this text: {story_text}\
                    I would like you to generate a dall-e-3 prompt. I would like you to split each \
                    prompt with a '|' symbol"}],
        model="gpt-3.5-turbo"
    )
    dalle3_prompts = chat_completion.choices[0].message.content.strip().split('|')

    # Hypothetical handling for images and voiceovers in the API response
    return story_text, dalle3_prompts

def open_image_from_url(url):
    response = requests.get(url)
    if response.status_code == 200:
        img = Image.open(BytesIO(response.content))
        img.show()
    else:
        print("Failed to download image")

if __name__ == "__main__":
    story_text, dalle3_prompts = generate_story("A boy goes to the supermarket with his mum and gets lost and scared", "arc")
    image_urls = []
    for prompt in dalle3_prompts:
        image_urls.append(client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
                ).data[0].url)
    for image in image_urls:
        open_image_from_url(image)
    print(story_text)
    print(f"image_url length: {len(image_urls)}")
