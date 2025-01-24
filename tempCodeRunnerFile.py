from flask import Flask, request, jsonify
import sqlite3
import os
from datetime import datetime

App=Flask(__name__)
DB_name="Motion_Alarm.db"
UPLOAD_FOLDER = r"D:\Sesha_Programs\Raspberry_pi\Uploaded_Videos"
if os.path.exists(UPLOAD_FOLDER)==False:
    os.mkdir(UPLOAD_FOLDER)

def make_db():
    connect=sqlite3.connect(DB_name)
    cursor=connect.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Motion_Alarm (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            video_path TEXT
        )
    ''')
    connect.commit()
    connect.close()

@App.route('/api/Motion_Alarm', methods=['POST'])

def Recieve_Vids():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # Save the file with date and time as filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_filename = f"motion_{timestamp}.avi"
    video_path = os.path.join(UPLOAD_FOLDER, video_filename)
    file.save(video_path)

    # Log the event in the database
    conn = sqlite3.connect(DB_name)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Motion_Alarm (video_path) VALUES (?)", (video_path,))
    conn.commit()
    conn.close()

    return jsonify({"message": "Motion event recorded", "video_path": video_path}), 200
@App.route('/api/Motion_Alarm', methods=['GET'])
def get_events():
    conn = sqlite3.connect(DB_name)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Motion_Alarm ORDER BY timestamp DESC")
    events = cursor.fetchall()
    conn.close()

    response = [
        {"id": row[0], "timestamp": row[1], "video_path": row[2]} for row in events
    ]

    return jsonify(response), 200
if __name__ == "__main__":
    make_db()
    App.run(host="0.0.0.0", port=8000)


