from openai import OpenAI
from google.cloud import texttospeech
from concurrent.futures import ThreadPoolExecutor, as_completed
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip
from io import BytesIO
import os, requests, multiprocessing
from gtts import gTTS
from PIL import Image
import numpy as np
from os.path import abspath, join


from flask import current_app

from app import create_app


def generate_story(prompt, image_frequency="arc"):
    client = current_app.openai_client
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": f"{prompt}\nPlease generate me this story and split it into {image_frequency}s with each {image_frequency} separated with the '|' symbol"}],
        model="gpt-3.5-turbo"
    )
    story_text = chat_completion.choices[0].message.content.strip().split('|')

    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": f"For each {image_frequency} in this text: {''.join(story_text)} I would like you to generate a dall-e-3 prompt. I would like you to split each prompt with a '|' symbol"}],
        model="gpt-3.5-turbo"
    )
    dalle3_prompts = chat_completion.choices[0].message.content.strip().split('|')

    return story_text, dalle3_prompts

def generate_image(dalle3_prompt):
    try:
        client = current_app.openai_client
        response = client.images.generate(
            model="dall-e-3",
            prompt=dalle3_prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        if response.data[0].url:
            return response.data[0].url
        else:
            raise ValueError("Failed to generate image")
    except Exception as e:
        current_app.logger.error(f"Error generating image for prompt {dalle3_prompt}: {e}")
        return "/static/black_background.png"  # Provide a default image path if generation fails

def text_to_speech(text, output_file):
    # Instantiates a client
    client = texttospeech.TextToSpeechClient()

    # Set the text input to be synthesized
    synthesis_input = texttospeech.SynthesisInput(text=text)

    # Build the voice request, select the language code ("en-US") and the ssml voice gender ("neutral")
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )

    # Select the type of audio file you want
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    # Perform the text-to-speech request on the text input with the selected voice parameters and audio file type
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    # The response's audio_content is binary.
    with open(output_file, "wb") as out:
        out.write(response.audio_content)
        print(f'Audio content written to "{output_file}"')



def async_api_call(data, image_frequency, session_id):
    app = create_app()
    with app.app_context():
        try:
            # Chain tasks: first, generate the story and prompts
            from app.celery_worker import generate_story_task
            story_result = generate_story_task.delay(data, image_frequency)
            story, dalle3_prompts = story_result.get()  # This waits for the task to complete   

            # Generate images in parallel
            from app.celery_worker import generate_image_task
            image_tasks = [generate_image_task.delay(prompt) for prompt in dalle3_prompts]
            image_urls = [task.get() for task in image_tasks]  # Collect results    
            
            # Prepare audio paths and corresponding texts
            audio_files = ["/app/app/static/audio{}.mp3".format(i) for i, text in enumerate(story)]
            audio_args = [(text, audiofile) for text, audiofile in zip(story, audio_files)] 
            
            # Generate audio files in parallel
            from app.celery_worker import text_to_speech_task
            audio_tasks = [text_to_speech_task.delay(*args) for args in audio_args]
            for task in audio_tasks:
                task.wait()  # Ensure all audio files are created

            # Create the final slideshow video
            from app.celery_worker import create_slideshow_with_audio_task
            video_task = create_slideshow_with_audio_task.delay(image_urls, audio_files)
            video_task.wait()  # Ensure video is created before proceeding

            video_path = "final_slideshow.mp4"  # Just the file name, not the full path
            current_app.config['RESULTS_STORAGE'][session_id] = (story, image_urls, video_path)
 
        except Exception as e:
            print(f"Error during API processing: {e}")
            current_app.config['RESULTS_STORAGE'][session_id] = (None, [], "")



def create_slideshow_with_audio(image_urls, audio_paths, duration=5):
    clips = []
    for image_url, audio_path in zip(image_urls, audio_paths):
        if image_url and not image_url.startswith('http'):
            # It's a local file, construct the path safely
            image_path = abspath(join(current_app.root_path or '', image_url.strip('/')))
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
            pil_image = Image.open(BytesIO(image_bytes))  # Convert bytes to a PIL image
        else:
            # It's a URL, make an HTTP request
            response = requests.get(image_url)
            response.raise_for_status()
            image_bytes = BytesIO(response.content)  # Create a BytesIO from HTTP response bytes
            pil_image = Image.open(image_bytes)  # Load image from BytesIO
        
        image_array = np.array(pil_image)  # Convert PIL image to numpy array
        audio_clip = AudioFileClip(audio_path)
        
        image_clip = ImageClip(image_array).set_duration(audio_clip.duration)
        
        # Set the audio of the image clip to be the audio clip
        video_clip = image_clip.set_audio(audio_clip)
        clips.append(video_clip)
    
    # Concatenate all video clips together
    final_clip = concatenate_videoclips(clips, method="compose")
    final_output_path = abspath(join(current_app.static_folder or '', "final_slideshow.mp4"))
    # final_output_path = "/video/final_slideshow.mp4"
    final_clip.write_videofile(final_output_path, fps=24, codec='libx264')

def text_to_speech_gTTS(text, output_file):
    try:
        tts = gTTS(text)
        tts.save(output_file)
        return "Audio content written successfully."
    except Exception as e:
        print(f"An error occurred: {e}")
        return "Failed to generate speech."
