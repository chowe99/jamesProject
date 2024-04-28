from flask import Blueprint, render_template, request, session, jsonify, current_app
from uuid import uuid4
from threading import Thread
from .utils.functions import async_api_call

main_blueprint = Blueprint('main', __name__)

@main_blueprint.route('/', methods=['GET', 'POST'])
def home():
    # Initialize or retrieve the session ID
    if 'session_id' not in session:
        session['session_id'] = str(uuid4())

    session_id = session['session_id']
    # Ensure there is an entry for this session
    if session_id not in current_app.config['RESULTS_STORAGE']:
        current_app.config['RESULTS_STORAGE'][session_id] = (None, [], "")

    # Retrieve stored results or initialize them if not present
    story, image_urls, video_path = current_app.config['RESULTS_STORAGE'][session_id]
    image_frequency = None  # Initialize image_frequency to ensure it's always defined

    # Handle form submission
    if request.method == 'POST':
        prompt = request.form.get('prompt', '')
        image_frequency = request.form.get('image_frequency', '')
        # Start the async task if no results are stored yet
        if not story and not image_urls and not video_path:  # Adjust as needed to match your logic for task completion
            thread = Thread(target=async_api_call, args=(prompt, image_frequency, session_id))
            thread.start()

    # Render the template with all necessary variables
    return render_template('home.html', video_path=video_path, image_urls=image_urls, story=story, image_frequency=image_frequency)


@main_blueprint.route('/check-results')
def check_results():
    session_id = session.get('session_id', None)
    if not session_id:
        return jsonify({'ready': False})

    content = current_app.config['RESULTS_STORAGE'].get(session_id)
    if content is None:
        return jsonify({'ready': False})

    story, image_urls, video_path = content
    is_ready = story is not None and image_urls is not None and video_path is not None
    return jsonify({
        'ready': is_ready,
        'story': story,
        'image_urls': image_urls,
        'video_path': video_path
    })


from flask import send_from_directory

@main_blueprint.route('/videos/<filename>')
def get_video(filename):
    directory = '/app/app/static/'
    return send_from_directory(directory, filename)
