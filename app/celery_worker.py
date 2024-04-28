from celery import Celery

def make_celery(app_name='app'):
    # Import create_app here to avoid circular imports
    from . import create_app
    app = create_app()
    celery = Celery(
        app.import_name,
        backend=app.config['RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery

# Instantiate celery using the factory method
celery = make_celery()

from .utils.functions import create_slideshow_with_audio, generate_story, generate_image, text_to_speech, text_to_speech_gTTS
@celery.task(name="generate_story_task")
def generate_story_task(prompt, image_frequency):
    result = generate_story(prompt, image_frequency)
    return result

@celery.task(name="generate_image_task")
def generate_image_task(dalle3_prompt):
    result = generate_image(dalle3_prompt)
    return result

@celery.task(name="text_to_speech_task")
def text_to_speech_task(text, output_file):
    result = text_to_speech_gTTS(text, output_file)

    import os
    from flask import current_app
    base_dir = current_app.root_path
    output_file_path = os.path.join(base_dir, 'app', 'static', output_file)
    print(output_file_path)

    return result

@celery.task(name="create_slideshow_with_audio_task")
def create_slideshow_with_audio_task(image_urls, audio_paths):
    create_slideshow_with_audio(image_urls, audio_paths)
