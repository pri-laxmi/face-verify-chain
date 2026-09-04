"""
web_search.py
-------------
Step 2 of the pipeline: given a local image, find real matching content
on the web/social media via a genuine reverse image search (SerpApi's
Google Reverse Image engine), then confirm the top hit is actually a
face match using the encodings from face_id.py.

SerpApi's reverse-image endpoint requires a publicly reachable image
URL rather than a raw file upload, so this module first uploads the
image to imgbb (a free, simple image host) to obtain a temporary URL,
then hands that URL to SerpApi.

You need two free API keys, both set as environment variables:
  - IMGBB_API_KEY   (https://api.imgbb.com/)
  - SERPAPI_API_KEY (https://serpapi.com/)

IMPORTANT / CONSENT NOTE:
This performs a real search against the live web. Only run it on
images you have the right to search -- e.g. your own photo, or a
photo of someone who has explicitly consented to this test. Do not
point this at photos of people who haven't agreed to be looked up.
"""

import os
import requests

IMGBB_UPLOAD_URL = "https://api.imgbb.com/1/upload"
SERPAPI_URL = "https://serpapi.com/search.json"


class SearchError(Exception):
    pass


def upload_image_get_url(image_path: str) -> str:
    """Upload a local image to imgbb and return a public URL for it."""
    api_key = os.environ.get("IMGBB_API_KEY")
    if not api_key:
        raise SearchError("IMGBB_API_KEY environment variable not set")

    with open(image_path, "rb") as f:
        resp = requests.post(
            IMGBB_UPLOAD_URL,
            params={"key": api_key},
            files={"image": f},
            timeout=30,
        )
    resp.raise_for_status()
    data = resp.json()
    if not data.get("success"):
        raise SearchError(f"imgbb upload failed: {data}")

    return data["data"]["url"]


def reverse_image_search(image_url: str, max_results: int = 10):
    """
    Run a genuine Google Reverse Image search via SerpApi on the given
    publicly reachable image URL. Returns a list of result dicts, each
    with at least 'title', 'link', and 'source'.
    """
    api_key = os.environ.get("SERPAPI_API_KEY")
    if not api_key:
        raise SearchError("SERPAPI_API_KEY environment variable not set")

    params = {
        "engine": "google_reverse_image",
        "image_url": image_url,
        "api_key": api_key,
    }
    resp = requests.get(SERPAPI_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    results = []
    for item in data.get("image_results", [])[:max_results]:
        results.append({
            "title": item.get("title"),
            "link": item.get("link"),
            "source": item.get("source"),
            "thumbnail": item.get("thumbnail"),
        })

    if not results:
        raise SearchError("No matching results found for this image")

    return results


def find_matching_post(image_path: str, max_results: int = 10):
    """
    Full step-2 flow: upload the local image, run a reverse image
    search against the live web, and return the raw candidate results.
    Verifying that a candidate actually contains the same face is left
    to the caller (pipeline.py), which re-runs face_id on the top
    candidate's image where possible.
    """
    public_url = upload_image_get_url(image_path)
    results = reverse_image_search(public_url, max_results=max_results)
    return public_url, results


if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) != 2:
        print("Usage: python web_search.py <image_path>")
        sys.exit(1)

    url, hits = find_matching_post(sys.argv[1])
    print(f"Uploaded to: {url}")
    print(json.dumps(hits, indent=2))
