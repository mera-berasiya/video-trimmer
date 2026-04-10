import os
import subprocess
import tempfile
from flask import Flask, request, send_file, jsonify

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/trim", methods=["POST"])
def trim_video():
    data = request.get_json()

    video_url = data.get("videoUrl")
    start_time = int(data.get("startTime", 0))
    end_time = int(data.get("endTime", 60))
    duration = end_time - start_time

    if not video_url:
        return jsonify({"error": "videoUrl is required"}), 400

    if duration <= 0:
        return jsonify({"error": "endTime must be greater than startTime"}), 400

    with tempfile.TemporaryDirectory() as tmpdir:
        video_file = os.path.join(tmpdir, "video.mp4")
        output_file = os.path.join(tmpdir, "clip.mp4")

        # Download video
        dl_result = subprocess.run([
            "yt-dlp",
            "-f", "best[height<=1080][ext=mp4]/best[height<=1080]/best",
            "-o", video_file,
            video_url
        ], capture_output=True, text=True)

        if dl_result.returncode != 0:
            return jsonify({"error": "Download failed", "details": dl_result.stderr}), 500

        # Trim with ffmpeg
        trim_result = subprocess.run([
            "ffmpeg",
            "-ss", str(start_time),
            "-i", video_file,
            "-t", str(duration),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-y",
            output_file
        ], capture_output=True, text=True)

        if trim_result.returncode != 0:
            return jsonify({"error": "Trim failed", "details": trim_result.stderr}), 500

        return send_file(output_file, mimetype="video/mp4", as_attachment=True, download_name="clip.mp4")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
