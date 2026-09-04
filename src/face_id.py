"""
face_id.py
----------
Step 1 of the pipeline: detect a face in an input image and produce a
numeric encoding that can be used later for matching/comparison.

Uses the `face_recognition` library (built on dlib), which gives a
128-dimension embedding per face. Two faces are considered a "match"
if the Euclidean distance between their encodings is below a threshold
(default 0.6, which is the library's own recommended cutoff).
"""

import face_recognition
import numpy as np


class NoFaceFoundError(Exception):
    pass


def load_and_encode(image_path: str):
    """
    Load an image from disk, detect the first face in it, and return:
      - the 128-d face encoding (numpy array)
      - the face location (top, right, bottom, left)
    Raises NoFaceFoundError if no face is detected.
    """
    image = face_recognition.load_image_file(image_path)
    face_locations = face_recognition.face_locations(image)

    if not face_locations:
        raise NoFaceFoundError(f"No face detected in {image_path}")

    encodings = face_recognition.face_encodings(image, known_face_locations=face_locations)

    if not encodings:
        raise NoFaceFoundError(f"Face detected but encoding failed for {image_path}")

    return encodings[0], face_locations[0]


def compare_faces(encoding_a: np.ndarray, encoding_b: np.ndarray, threshold: float = 0.6):
    """
    Compare two face encodings. Returns (is_match: bool, distance: float).
    Lower distance = more similar. 0.6 is face_recognition's default cutoff.
    """
    distance = float(face_recognition.face_distance([encoding_a], encoding_b)[0])
    return distance <= threshold, distance


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python face_id.py <image_path>")
        sys.exit(1)

    enc, loc = load_and_encode(sys.argv[1])
    print(f"Face found at {loc}")
    print(f"Encoding (first 8 dims): {enc[:8]}")
