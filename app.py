from flask import Flask, request, jsonify
from flask_cors import CORS
from models.hugging_skt_kogpt2 import add_comment
from models.hearus_nlp_model import process_json_data, process_data_to_json
import pandas as pd
import json

import whisper
import numpy as np
from pydub import AudioSegment
import io

app = Flask(__name__)
CORS(app)

# Choose a model size ("tiny", "base", "small", "medium", "large")
whisper_model = whisper.load_model("base")


@app.route("/transcribe", methods=["POST"])
def transcribe():
    # Get the audio file from the request
    audio_file = request.files["audio"]

    # Convert the audio file to the appropriate format
    audio_format = audio_file.filename.split(".")[-1]
    audio_segment = AudioSegment.from_file(
        io.BytesIO(audio_file.read()), format=audio_format
    )

    # Convert to mono and the required sample rate (16kHz for Whisper)
    audio_segment = audio_segment.set_frame_rate(16000).set_channels(1)

    # Convert to numpy array
    audio_numpy = np.array(audio_segment.get_array_of_samples(), dtype=np.float32)
    audio_numpy = audio_numpy / np.iinfo(audio_segment.array_type).max  # Normalize

    # Transcribe the audio file using Whisper
    result = whisper_model.transcribe(audio_numpy, language="ko")
    transcription = result["text"]

    app.logger.info("Transcription Result: " + transcription)
    return transcription


@app.route("/process", methods=["POST"])
def process():
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400

    try:
        origin_data = request.get_json()

        dataFrame = process_json_data(origin_data)
        nlpResultDictData = process_data_to_json(
            dataFrame,
            dataFrame["important_words"][0],
            dataFrame["important_sentence"][0],
        )
        app.logger.inf("DictData : " + nlpResultDictData)
        # nlpResultJsonData = json.dumps(nlpResultDictData)

        # app.logger.inf(nlpResultJsonData)

        # GPT API 호출, 서버로 반환
        # processed_data = add_comment(app, processed_data)
        # return jsonify(processed_data)
    except json.JSONDecodeError as e:
        return jsonify({"error": "Invalid JSON"}), 400


if __name__ == "__main__":
    app.run(port=5000, debug=True)
