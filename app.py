# ============================================================
# SENTILYTICS
# YouTube AI Sentiment Analysis
#
# BACKEND:
#   Python + Flask
#
# APIS:
#   YouTube Data API v3
#   Groq AI
#
# AI MODEL:
#   openai/gpt-oss-20b
#
# FEATURES:
#   - YouTube video information
#   - YouTube comments
#   - Multilingual AI sentiment analysis
#   - Single comment AI analysis
#   - English / Hindi / Tamil / Telugu / Malayalam etc.
#   - Mixed-language comments
#   - Hinglish / Tanglish
#   - Positive / Negative / Neutral classification
#   - Sentiment statistics
#   - Up to 200 comments
#   - 25 comments per Groq request
#   - Automatic Groq retry
#   - Safe fallback if AI request fails
# ============================================================


# ============================================================
# IMPORT LIBRARIES
# ============================================================

import os
import re
import json
import requests

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

from dotenv import load_dotenv
from groq import Groq


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# API KEYS
# ============================================================

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


# ============================================================
# GROQ MODEL
# ============================================================

GROQ_MODEL = "openai/gpt-oss-20b"


# ============================================================
# PROJECT SETTINGS
# ============================================================

# Number of comments sent to Groq in one request.

GROQ_BATCH_SIZE = 25


# Maximum number of YouTube comments to analyze.

MAX_COMMENTS = 200


# Number of times to retry a failed Groq request.

MAX_GROQ_RETRIES = 3


# ============================================================
# CREATE FLASK APPLICATION
# ============================================================

app = Flask(__name__)


# ============================================================
# ENABLE CORS
# ============================================================

CORS(app)


# ============================================================
# CREATE GROQ CLIENT
# ============================================================

groq_client = None


if GROQ_API_KEY:

    groq_client = Groq(
        api_key=GROQ_API_KEY
    )


# ============================================================
# VALIDATE YOUTUBE VIDEO ID
# ============================================================

def is_valid_video_id(video_id):

    if not video_id:
        return False

    return bool(
        re.fullmatch(
            r"[A-Za-z0-9_-]{11}",
            video_id
        )
    )


# ============================================================
# EXTRACT VIDEO ID FROM YOUTUBE URL
# ============================================================

def extract_video_id(value):

    if not value:
        return ""

    value = value.strip()

    # --------------------------------------------------------
    # Direct video ID
    # --------------------------------------------------------

    if is_valid_video_id(value):
        return value

    # --------------------------------------------------------
    # Supported YouTube URL formats
    # --------------------------------------------------------

    patterns = [

        r"(?:youtube\.com/watch\?v=)([A-Za-z0-9_-]{11})",

        r"(?:youtu\.be/)([A-Za-z0-9_-]{11})",

        r"(?:youtube\.com/shorts/)([A-Za-z0-9_-]{11})",

        r"(?:youtube\.com/embed/)([A-Za-z0-9_-]{11})",

        r"(?:youtube-nocookie\.com/embed/)"
        r"([A-Za-z0-9_-]{11})"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            value
        )

        if match:

            return match.group(1)

    return ""


# ============================================================
# FETCH YOUTUBE VIDEO DETAILS
# ============================================================

def fetch_video_details(video_id):

    url = (
        "https://www.googleapis.com/"
        "youtube/v3/videos"
    )

    params = {

        "part":
            "snippet,statistics",

        "id":
            video_id,

        "key":
            YOUTUBE_API_KEY
    }

    response = requests.get(
        url,
        params=params,
        timeout=20
    )

    try:

        data = response.json()

    except ValueError:

        raise Exception(
            "Invalid response from YouTube API."
        )

    if response.status_code != 200:

        message = (

            data
            .get("error", {})
            .get(
                "message",
                "YouTube API error."
            )
        )

        raise Exception(message)

    items = data.get(
        "items",
        []
    )

    if not items:

        raise Exception(
            "YouTube video not found."
        )

    video = items[0]

    snippet = video.get(
        "snippet",
        {}
    )

    statistics = video.get(
        "statistics",
        {}
    )

    thumbnails = snippet.get(
        "thumbnails",
        {}
    )

    # --------------------------------------------------------
    # Select best thumbnail available.
    # --------------------------------------------------------

    thumbnail = (

        thumbnails
        .get("maxres", {})
        .get("url")

        or

        thumbnails
        .get("high", {})
        .get("url")

        or

        thumbnails
        .get("medium", {})
        .get("url")

        or

        thumbnails
        .get("default", {})
        .get("url")

        or ""
    )

    return {

        "title":
            snippet.get(
                "title",
                "YouTube Video"
            ),

        "channel":
            snippet.get(
                "channelTitle",
                "Unknown Channel"
            ),

        "published_at":
            snippet.get(
                "publishedAt",
                ""
            ),

        "thumbnail":
            thumbnail,

        "view_count":
            statistics.get(
                "viewCount",
                "0"
            ),

        "like_count":
            statistics.get(
                "likeCount",
                "0"
            )
    }


# ============================================================
# FETCH YOUTUBE COMMENTS
# ============================================================

def fetch_youtube_comments(
    video_id,
    max_comments=200
):

    url = (
        "https://www.googleapis.com/"
        "youtube/v3/commentThreads"
    )

    comments = []

    next_page_token = None

    while len(comments) < max_comments:

        params = {

            "part":
                "snippet",

            "videoId":
                video_id,

            "maxResults":
                100,

            "textFormat":
                "plainText",

            "key":
                YOUTUBE_API_KEY
        }

        if next_page_token:

            params["pageToken"] = (
                next_page_token
            )

        response = requests.get(
            url,
            params=params,
            timeout=20
        )

        try:

            data = response.json()

        except ValueError:

            raise Exception(
                "Invalid response from YouTube comments API."
            )

        if response.status_code != 200:

            message = (

                data
                .get("error", {})
                .get(
                    "message",
                    "Unable to fetch comments."
                )
            )

            raise Exception(message)

        # ----------------------------------------------------
        # Process comments.
        # ----------------------------------------------------

        for item in data.get(
            "items",
            []
        ):

            try:

                snippet = (

                    item["snippet"]
                    ["topLevelComment"]
                    ["snippet"]
                )

                text = snippet.get(
                    "textDisplay",
                    ""
                )

                author = snippet.get(
                    "authorDisplayName",
                    "YouTube User"
                )

                published_at = snippet.get(
                    "publishedAt",
                    ""
                )

                updated_at = snippet.get(
                    "updatedAt",
                    published_at
                )

                likes = snippet.get(
                    "likeCount",
                    0
                )

                # Ignore empty comments.

                if not text.strip():

                    continue

                comments.append({

                    "text":
                        text,

                    "author":
                        author,

                    "published_at":
                        published_at,

                    "updated_at":
                        updated_at,

                    "likes":
                        likes
                })

            except (
                KeyError,
                TypeError
            ):

                continue

            if len(comments) >= max_comments:

                break

        next_page_token = data.get(
            "nextPageToken"
        )

        if not next_page_token:

            break

    return comments[:max_comments]


# ============================================================
# NORMALIZE SENTIMENT
# ============================================================

def normalize_sentiment(value):

    if not value:

        return "NEUTRAL"

    value = str(
        value
    ).strip().upper()

    if value == "POSITIVE":

        return "POSITIVE"

    if value == "NEGATIVE":

        return "NEGATIVE"

    return "NEUTRAL"


# ============================================================
# SENTIMENT SCORE
# ============================================================

def get_sentiment_score(sentiment):

    if sentiment == "POSITIVE":

        return 1

    if sentiment == "NEGATIVE":

        return -1

    return 0


# ============================================================
# CLEAN GROQ JSON RESPONSE
# ============================================================

def clean_json_response(content):

    if not content:

        return ""

    content = content.strip()

    # --------------------------------------------------------
    # Remove Markdown code fences if AI accidentally returns
    # them.
    # --------------------------------------------------------

    if content.startswith("```"):

        content = re.sub(
            r"^```(?:json)?\s*",
            "",
            content,
            flags=re.IGNORECASE
        )

        content = re.sub(
            r"\s*```$",
            "",
            content
        )

    return content.strip()


# ============================================================
# PARSE GROQ RESULT
# ============================================================

def parse_groq_results(
    content,
    expected_indexes
):

    content = clean_json_response(
        content
    )

    try:

        parsed = json.loads(
            content
        )

    except json.JSONDecodeError:

        raise Exception(
            "Groq returned invalid JSON."
        )

    results = parsed.get(
        "results",
        []
    )

    if not isinstance(
        results,
        list
    ):

        raise Exception(
            "Groq JSON results is not an array."
        )

    final_results = []

    returned_indexes = set()

    for result in results:

        if not isinstance(
            result,
            dict
        ):

            continue

        index = result.get(
            "index"
        )

        if index not in expected_indexes:

            continue

        if index in returned_indexes:

            continue

        sentiment = normalize_sentiment(

            result.get(
                "sentiment"
            )
        )

        final_results.append({

            "index":
                index,

            "sentiment":
                sentiment
        })

        returned_indexes.add(
            index
        )

    # --------------------------------------------------------
    # If Groq misses any index, safely use NEUTRAL.
    # --------------------------------------------------------

    for index in expected_indexes:

        if index not in returned_indexes:

            final_results.append({

                "index":
                    index,

                "sentiment":
                    "NEUTRAL"
            })

    final_results.sort(
        key=lambda item:
            item["index"]
    )

    return final_results


# ============================================================
# ANALYZE ONE BATCH WITH GROQ
# ============================================================

def analyze_single_groq_batch(
    batch,
    start_index
):

    # ========================================================
    # PREPARE INPUT COMMENTS
    # ========================================================

    input_comments = []

    for local_index, comment in enumerate(
        batch
    ):

        input_comments.append({

            "index":
                start_index + local_index,

            "text":
                comment.get(
                    "text",
                    ""
                )
        })

    expected_indexes = set(

        item["index"]

        for item in input_comments
    )


    # ========================================================
    # MULTILINGUAL SYSTEM PROMPT
    # ========================================================

    system_prompt = """
You are a highly accurate multilingual sentiment analysis AI.

Your task is to analyze EVERY YouTube comment provided to you.

The comments may be written in different languages,
different scripts, mixed languages, or romanized languages.

IMPORTANT:

Understand the actual meaning of every comment before
classifying its sentiment.

Do NOT assume that a comment is neutral simply because
it is not written in English.

LANGUAGE SUPPORT:

You should attempt to understand any language supported
by your language capabilities.

Examples include:

English
Hindi
Tamil
Telugu
Malayalam
Kannada
Bengali
Marathi
Gujarati
Punjabi
Urdu
Arabic
Spanish
French
German
Portuguese
Italian
Russian
Japanese
Korean
Chinese
Indonesian
Turkish
and other languages.

Also understand:

- Mixed-language comments
- Code-switching
- Hinglish
- Tanglish
- Romanized Hindi
- Romanized Tamil
- Romanized Telugu
- Romanized Malayalam
- Internet slang
- Informal spelling
- Emojis
- Common abbreviations
- Minor spelling mistakes

MULTILINGUAL RULE:

Analyze the sentiment according to the meaning of the
original comment.

Do NOT require the comment to be English.

Do NOT translate the comment in the output.

Do NOT return the detected language unless requested.

Only return the sentiment classification.

------------------------------------------------------------
SENTIMENT DEFINITIONS
------------------------------------------------------------

POSITIVE:

Use POSITIVE when the comment expresses:

- Praise
- Happiness
- Appreciation
- Support
- Excitement
- Satisfaction
- Agreement
- Enjoyment
- Favorable opinion
- Positive reaction

NEGATIVE:

Use NEGATIVE when the comment expresses:

- Criticism
- Anger
- Disappointment
- Dislike
- Complaints
- Frustration
- Insults
- Dissatisfaction
- Unfavorable opinion
- Negative reaction

NEUTRAL:

Use NEUTRAL when:

- The comment is factual.
- The comment is informational.
- The comment is a question without clear sentiment.
- The meaning is unclear.
- There is no clear positive or negative opinion.

------------------------------------------------------------
MIXED SENTIMENT
------------------------------------------------------------

If a comment contains both positive and negative statements,
determine the dominant overall sentiment.

Example:

A comment can praise the video but criticize one part.

Choose the sentiment that best represents the overall
dominant opinion.

If the dominant sentiment cannot reasonably be determined,
use NEUTRAL.

------------------------------------------------------------
IMPORTANT RULES
------------------------------------------------------------

1. Analyze EVERY comment.

2. Never skip an index.

3. Never change an index.

4. Return exactly one result for every input comment.

5. Understand the original language.

6. Do not require English.

7. Handle mixed languages.

8. Handle romanized languages when possible.

9. Consider the meaning and context.

10. Do not translate the comments in the output.

11. Use ONLY these sentiment values:

POSITIVE
NEGATIVE
NEUTRAL

12. Return valid JSON only.

13. Do not use Markdown.

14. Do not include explanations.

15. Do not include additional fields.

------------------------------------------------------------
REQUIRED JSON FORMAT
------------------------------------------------------------

{
  "results": [
    {
      "index": 0,
      "sentiment": "POSITIVE"
    }
  ]
}
"""


    # ========================================================
    # USER PROMPT
    # ========================================================

    user_prompt = (
        "Analyze the following YouTube comments "
        "for sentiment.\n\n"
        "The comments may be written in different "
        "languages.\n"
        "Understand each comment in its original language.\n"
        "Return JSON only.\n\n"
        +
        json.dumps(
            input_comments,
            ensure_ascii=False
        )
    )


    # ========================================================
    # RETRY LOOP
    # ========================================================

    last_error = None

    for attempt in range(
        1,
        MAX_GROQ_RETRIES + 1
    ):

        try:

            print(
                f"Groq attempt "
                f"{attempt}/"
                f"{MAX_GROQ_RETRIES}"
            )

            # ------------------------------------------------
            # GROQ REQUEST
            # ------------------------------------------------

            response = (
                groq_client
                .chat
                .completions
                .create(

                    model=GROQ_MODEL,

                    messages=[

                        {
                            "role":
                                "system",

                            "content":
                                system_prompt
                        },

                        {
                            "role":
                                "user",

                            "content":
                                user_prompt
                        }
                    ],

                    # JSON object mode.

                    response_format={
                        "type":
                            "json_object"
                    },

                    # Deterministic output.

                    temperature=0,

                    # Response token limit.

                    max_completion_tokens=4096,

                    # We only need the final answer.

                    include_reasoning=False
                )
            )

            # ------------------------------------------------
            # GET AI RESPONSE
            # ------------------------------------------------

            content = (

                response
                .choices[0]
                .message
                .content
            )

            print(
                "========== GROQ RESPONSE =========="
            )

            print(content)

            print(
                "==================================="
            )

            # ------------------------------------------------
            # PARSE RESULT
            # ------------------------------------------------

            results = parse_groq_results(

                content,

                expected_indexes
            )

            return results

        except Exception as error:

            last_error = error

            print(
                f"Groq attempt "
                f"{attempt} failed:"
            )

            print(
                str(error)
            )

            if attempt < MAX_GROQ_RETRIES:

                print(
                    "Retrying Groq request..."
                )


    # ========================================================
    # ALL GROQ REQUESTS FAILED
    # ========================================================

    print(
        "Groq failed after all retries."
    )

    print(
        "Using NEUTRAL fallback for this batch."
    )

    fallback_results = []

    for index in expected_indexes:

        fallback_results.append({

            "index":
                index,

            "sentiment":
                "NEUTRAL"
        })

    fallback_results.sort(
        key=lambda item:
            item["index"]
    )

    return fallback_results


# ============================================================
# GROQ AI SENTIMENT ANALYSIS
# ============================================================

def analyze_comments_with_groq(
    comments
):

    if not GROQ_API_KEY:

        raise Exception(
            "Groq API key is missing."
        )

    if groq_client is None:

        raise Exception(
            "Groq client could not be initialized."
        )

    all_results = []

    # --------------------------------------------------------
    # Split comments into batches.
    # --------------------------------------------------------

    for start in range(
        0,
        len(comments),
        GROQ_BATCH_SIZE
    ):

        batch = comments[
            start:
            start + GROQ_BATCH_SIZE
        ]

        print("")

        print(
            "----------------------------------------"
        )

        print(
            f"Analyzing comments "
            f"{start + 1} - "
            f"{start + len(batch)}..."
        )

        print(
            "----------------------------------------"
        )

        batch_results = analyze_single_groq_batch(

            batch,

            start
        )

        all_results.extend(
            batch_results
        )

    all_results.sort(
        key=lambda item:
            item["index"]
    )

    return all_results


# ============================================================
# ATTACH SENTIMENTS TO COMMENTS
# ============================================================

def attach_sentiments(
    comments,
    ai_results
):

    lookup = {}

    for result in ai_results:

        lookup[
            result["index"]
        ] = result["sentiment"]

    for index, comment in enumerate(
        comments
    ):

        sentiment = lookup.get(
            index,
            "NEUTRAL"
        )

        comment["sentiment"] = (
            sentiment
        )

        comment["score"] = (
            get_sentiment_score(
                sentiment
            )
        )

    return comments


# ============================================================
# CALCULATE STATISTICS
# ============================================================

def calculate_statistics(
    comments
):

    total = len(
        comments
    )

    positive = 0

    negative = 0

    neutral = 0

    # --------------------------------------------------------
    # Count sentiment.
    # --------------------------------------------------------

    for comment in comments:

        sentiment = normalize_sentiment(

            comment.get(
                "sentiment"
            )
        )

        if sentiment == "POSITIVE":

            positive += 1

        elif sentiment == "NEGATIVE":

            negative += 1

        else:

            neutral += 1

    # --------------------------------------------------------
    # Calculate percentages.
    # --------------------------------------------------------

    if total > 0:

        positive_percentage = (
            positive / total
        ) * 100

        negative_percentage = (
            negative / total
        ) * 100

        neutral_percentage = (
            neutral / total
        ) * 100

    else:

        positive_percentage = 0

        negative_percentage = 0

        neutral_percentage = 0

    # --------------------------------------------------------
    # Determine overall sentiment.
    # --------------------------------------------------------

    counts = {

        "POSITIVE":
            positive,

        "NEGATIVE":
            negative,

        "NEUTRAL":
            neutral
    }

    overall = max(
        counts,
        key=counts.get
    )

    return {

        "total":
            total,

        "positive":
            positive,

        "negative":
            negative,

        "neutral":
            neutral,

        "positive_percentage":
            round(
                positive_percentage,
                2
            ),

        "negative_percentage":
            round(
                negative_percentage,
                2
            ),

        "neutral_percentage":
            round(
                neutral_percentage,
                2
            ),

        "overall_sentiment":
            overall
    }


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route(
    "/api/health",
    methods=["GET"]
)
def health():

    return jsonify({

        "success":
            True,

        "status":
            "online",

        "message":
            "Sentilytics backend is running.",

        "youtube_api":
            bool(YOUTUBE_API_KEY),

        "groq_api":
            bool(GROQ_API_KEY),

        "model":
            GROQ_MODEL,

        "multilingual":
            True,

        "single_comment_ai":
            True,

        "batch_size":
            GROQ_BATCH_SIZE,

        "max_comments":
            MAX_COMMENTS
    })


# ============================================================
# ANALYZE SINGLE COMMENT WITH GROQ AI
# ============================================================

@app.route(
    "/api/analyze-comment",
    methods=["POST"]
)
def analyze_single_comment():

    try:

        # ====================================================
        # GET JSON DATA FROM FRONTEND
        # ====================================================

        data = request.get_json(
            silent=True
        ) or {}

        comment = str(
            data.get(
                "comment",
                ""
            )
        ).strip()

        # ====================================================
        # VALIDATE COMMENT
        # ====================================================

        if not comment:

            return jsonify({

                "success":
                    False,

                "error":
                    "Please enter a comment."
            }), 400

        # ====================================================
        # CHECK GROQ API KEY
        # ====================================================

        if not GROQ_API_KEY:

            return jsonify({

                "success":
                    False,

                "error":
                    (
                        "Groq API key is missing. "
                        "Add GROQ_API_KEY to .env."
                    )
            }), 500

        # ====================================================
        # CHECK GROQ CLIENT
        # ====================================================

        if groq_client is None:

            return jsonify({

                "success":
                    False,

                "error":
                    "Groq client could not be initialized."
            }), 500

        # ====================================================
        # MULTILINGUAL SYSTEM PROMPT
        # ========================================================

        system_prompt = """
You are a highly accurate multilingual sentiment analysis AI.

Your task is to analyze ONE user comment and classify
its overall sentiment.

The comment may be written in any language you understand.

IMPORTANT:

Do NOT assume that a comment is NEUTRAL because it is
not written in English.

Understand the meaning of the original comment first.

------------------------------------------------------------
LANGUAGE SUPPORT
------------------------------------------------------------

Attempt to understand:

English
Hindi
Tamil
Telugu
Malayalam
Kannada
Bengali
Marathi
Gujarati
Punjabi
Urdu
Arabic
Spanish
French
German
Portuguese
Italian
Russian
Japanese
Korean
Chinese
Indonesian
Turkish
and other supported languages.

Also handle, when possible:

- Mixed-language comments
- Code-switching
- Hinglish
- Tanglish
- Romanized Hindi
- Romanized Tamil
- Romanized Telugu
- Romanized Malayalam
- Internet slang
- Informal spelling
- Emojis
- Common abbreviations
- Minor spelling mistakes

------------------------------------------------------------
SENTIMENT DEFINITIONS
------------------------------------------------------------

POSITIVE:

Use POSITIVE when the comment expresses:

- Praise
- Happiness
- Appreciation
- Support
- Excitement
- Satisfaction
- Agreement
- Enjoyment
- Favorable opinion
- Positive reaction

NEGATIVE:

Use NEGATIVE when the comment expresses:

- Criticism
- Anger
- Disappointment
- Dislike
- Complaints
- Frustration
- Insults
- Dissatisfaction
- Unfavorable opinion
- Negative reaction

NEUTRAL:

Use NEUTRAL when:

- The comment is factual.
- The comment is informational.
- The comment is a question without clear sentiment.
- The meaning is unclear.
- There is no clear positive or negative opinion.

------------------------------------------------------------
MIXED SENTIMENT
------------------------------------------------------------

If both positive and negative statements are present,
choose the dominant overall sentiment.

If a clear dominant sentiment cannot reasonably be
determined, use NEUTRAL.

------------------------------------------------------------
IMPORTANT RULES
------------------------------------------------------------

1. Understand the original language.

2. Do NOT require English.

3. Do NOT assume non-English means NEUTRAL.

4. Handle mixed languages.

5. Handle romanized languages when possible.

6. Consider context.

7. Consider emojis.

8. Consider common slang.

9. Do NOT translate the comment.

10. Do NOT return the detected language.

11. Do NOT provide an explanation.

12. Return ONLY valid JSON.

13. The sentiment must be exactly:

POSITIVE
NEGATIVE
NEUTRAL

------------------------------------------------------------
REQUIRED JSON FORMAT
------------------------------------------------------------

{
    "sentiment": "POSITIVE"
}
"""

        # ====================================================
        # USER PROMPT
        # ====================================================

        user_prompt = (
            "Analyze the sentiment of this comment.\n\n"
            "Comment:\n"
            + comment
        )

        # ====================================================
        # GROQ REQUEST
        # ====================================================

        print("")
        print(
            "========================================"
        )

        print(
            "SINGLE COMMENT AI ANALYSIS"
        )

        print(
            "========================================"
        )

        print(
            "Comment:",
            comment
        )

        response = (
            groq_client
            .chat
            .completions
            .create(

                model=GROQ_MODEL,

                messages=[

                    {
                        "role":
                            "system",

                        "content":
                            system_prompt
                    },

                    {
                        "role":
                            "user",

                        "content":
                            user_prompt
                    }
                ],

                response_format={
                    "type":
                        "json_object"
                },

                temperature=0,

                max_completion_tokens=1000,

                include_reasoning=False
            )
        )

        # ====================================================
        # GET AI RESPONSE
        # ====================================================

        content = (

            response
            .choices[0]
            .message
            .content
        )

        print(
            "Groq response:",
            content
        )

        # ====================================================
        # CLEAN RESPONSE
        # ====================================================

        content = clean_json_response(
            content
        )

        # ====================================================
        # PARSE JSON
        # ====================================================

        parsed = json.loads(
            content
        )

        # ====================================================
        # GET SENTIMENT
        # ====================================================

        sentiment = normalize_sentiment(

            parsed.get(
                "sentiment"
            )
        )

        # ====================================================
        # FINAL RESULT
        # ====================================================

        print(
            "Detected sentiment:",
            sentiment
        )

        print(
            "========================================"
        )

        return jsonify({

            "success":
                True,

            "sentiment":
                sentiment
        })

    # ========================================================
    # JSON ERROR
    # ========================================================

    except json.JSONDecodeError:

        print(
            "ERROR: Groq returned invalid JSON."
        )

        return jsonify({

            "success":
                False,

            "error":
                "Groq returned an invalid response."
        }), 500

    # ========================================================
    # GENERAL ERROR
    # ========================================================

    except Exception as error:

        print("")
        print(
            "========================================"
        )

        print(
            "SINGLE COMMENT ANALYSIS ERROR"
        )

        print(
            "========================================"
        )

        print(
            str(error)
        )

        print(
            "========================================"
        )

        return jsonify({

            "success":
                False,

            "error":
                str(error)
        }), 500


# ============================================================
# ANALYZE YOUTUBE VIDEO
# ============================================================

@app.route(
    "/api/analyze",
    methods=[
        "GET",
        "POST"
    ]
)
def analyze_video():

    # ========================================================
    # GET REQUEST
    # ========================================================

    if request.method == "GET":

        video_id = request.args.get(
            "video_id",
            ""
        ).strip()

    # ========================================================
    # POST REQUEST
    # ========================================================

    else:

        data = request.get_json(
            silent=True
        ) or {}

        video_id = str(

            data.get(
                "video_id",
                ""
            )

        ).strip()

        # ----------------------------------------------------
        # If video ID doesn't exist,
        # extract it from URL.
        # ----------------------------------------------------

        if not video_id:

            url = str(

                data.get(
                    "url",
                    ""
                )

            ).strip()

            video_id = extract_video_id(
                url
            )

    # ========================================================
    # VALIDATE VIDEO ID
    # ========================================================

    if not is_valid_video_id(
        video_id
    ):

        return jsonify({

            "success":
                False,

            "error":
                "Invalid YouTube video ID."
        }), 400

    # ========================================================
    # CHECK YOUTUBE API KEY
    # ========================================================

    if not YOUTUBE_API_KEY:

        return jsonify({

            "success":
                False,

            "error":
                (
                    "YouTube API key is missing. "
                    "Add YOUTUBE_API_KEY to .env."
                )
        }), 500

    # ========================================================
    # CHECK GROQ API KEY
    # ========================================================

    if not GROQ_API_KEY:

        return jsonify({

            "success":
                False,

            "error":
                (
                    "Groq API key is missing. "
                    "Add GROQ_API_KEY to .env."
                )
        }), 500

    # ========================================================
    # MAIN PROCESS
    # ========================================================

    try:

        print("")

        print(
            "========================================"
        )

        print(
            "SENTILYTICS ANALYSIS STARTED"
        )

        print(
            "========================================"
        )

        # ====================================================
        # STEP 1:
        # FETCH VIDEO DETAILS
        # ====================================================

        print(
            "Fetching video details..."
        )

        video = fetch_video_details(
            video_id
        )

        # ====================================================
        # STEP 2:
        # FETCH COMMENTS
        # ====================================================

        print(
            "Fetching YouTube comments..."
        )

        comments = fetch_youtube_comments(

            video_id,

            MAX_COMMENTS
        )

        if not comments:

            return jsonify({

                "success":
                    False,

                "error":
                    (
                        "No public comments were "
                        "found for this video."
                    )
            }), 404

        print(
            "Comments fetched:",
            len(comments)
        )

        # ====================================================
        # STEP 3:
        # MULTILINGUAL GROQ AI ANALYSIS
        # ====================================================

        print(
            "Starting multilingual Groq AI "
            "sentiment analysis..."
        )

        ai_results = (
            analyze_comments_with_groq(
                comments
            )
        )

        # ====================================================
        # STEP 4:
        # ATTACH SENTIMENT
        # ====================================================

        comments = attach_sentiments(

            comments,

            ai_results
        )

        # ====================================================
        # STEP 5:
        # CALCULATE STATISTICS
        # ====================================================

        statistics = (
            calculate_statistics(
                comments
            )
        )

        # ====================================================
        # STEP 6:
        # FORMAT COMMENTS FOR FRONTEND
        # ====================================================

        formatted_comments = []

        for comment in comments:

            formatted_comments.append({

                "text":
                    comment.get(
                        "text",
                        ""
                    ),

                "author":
                    comment.get(
                        "author",
                        "YouTube User"
                    ),

                "publishedAt":
                    comment.get(
                        "published_at",
                        ""
                    ),

                "updatedAt":
                    comment.get(
                        "updated_at",
                        ""
                    ),

                "likes":
                    comment.get(
                        "likes",
                        0
                    ),

                "sentiment":
                    comment.get(
                        "sentiment",
                        "NEUTRAL"
                    ),

                "score":
                    comment.get(
                        "score",
                        0
                    )
            })

        # ====================================================
        # FINAL RESPONSE
        # ====================================================

        result = {

            "success":
                True,

            "video_id":
                video_id,

            "video":
                video,

            "total_comments":
                statistics[
                    "total"
                ],

            "overall_sentiment":
                statistics[
                    "overall_sentiment"
                ],

            "sentiment_counts": {

                "positive":
                    statistics[
                        "positive"
                    ],

                "neutral":
                    statistics[
                        "neutral"
                    ],

                "negative":
                    statistics[
                        "negative"
                    ]
            },

            "sentiment_percentages": {

                "positive":
                    statistics[
                        "positive_percentage"
                    ],

                "neutral":
                    statistics[
                        "neutral_percentage"
                    ],

                "negative":
                    statistics[
                        "negative_percentage"
                    ]
            },

            "comments":
                formatted_comments
        }

        # ====================================================
        # PRINT FINAL STATISTICS
        # ====================================================

        print("")

        print(
            "========================================"
        )

        print(
            "SENTILYTICS ANALYSIS COMPLETED"
        )

        print(
            "========================================"
        )

        print(
            "Total comments:",
            statistics["total"]
        )

        print(
            "Positive:",
            statistics["positive"]
        )

        print(
            "Negative:",
            statistics["negative"]
        )

        print(
            "Neutral:",
            statistics["neutral"]
        )

        print(
            "Overall:",
            statistics[
                "overall_sentiment"
            ]
        )

        print(
            "Multilingual Analysis:",
            "ENABLED"
        )

        print(
            "Single Comment AI:",
            "ENABLED"
        )

        print(
            "========================================"
        )

        return jsonify(
            result
        )

    # ========================================================
    # ERROR HANDLER
    # ========================================================

    except Exception as error:

        print("")

        print(
            "========================================"
        )

        print(
            "SENTILYTICS ERROR"
        )

        print(
            "========================================"
        )

        print(
            str(error)
        )

        print(
            "========================================"
        )

        return jsonify({

            "success":
                False,

            "error":
                str(error)
        }), 500


# ============================================================
# 404 ERROR HANDLER
# ============================================================

@app.errorhandler(404)
def not_found(error):

    return jsonify({

        "success":
            False,

        "error":
            "API endpoint not found."
    }), 404


# ============================================================
# 405 ERROR HANDLER
# ============================================================

@app.errorhandler(405)
def method_not_allowed(error):

    return jsonify({

        "success":
            False,

        "error":
            "HTTP method not allowed."
    }), 405


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    print("")

    print(
        "================================================"
    )

    print(
        "          SENTILYTICS AI BACKEND"
    )

    print(
        "================================================"
    )

    # --------------------------------------------------------
    # YouTube API status.
    # --------------------------------------------------------

    print(

        "YouTube API:",

        "CONNECTED"
        if YOUTUBE_API_KEY
        else
        "MISSING"
    )

    # --------------------------------------------------------
    # Groq API status.
    # --------------------------------------------------------

    print(

        "Groq API:",

        "CONNECTED"
        if GROQ_API_KEY
        else
        "MISSING"
    )

    # --------------------------------------------------------
    # Model.
    # --------------------------------------------------------

    print(
        "Groq Model:",
        GROQ_MODEL
    )

    # --------------------------------------------------------
    # Multilingual status.
    # --------------------------------------------------------

    print(
        "Multilingual AI:",
        "ENABLED"
    )

    # --------------------------------------------------------
    # Single comment AI.
    # --------------------------------------------------------

    print(
        "Single Comment AI:",
        "ENABLED"
    )

    # --------------------------------------------------------
    # Batch size.
    # --------------------------------------------------------

    print(
        "Groq Batch Size:",
        GROQ_BATCH_SIZE
    )

    # --------------------------------------------------------
    # Maximum comments.
    # --------------------------------------------------------

    print(
        "Maximum Comments:",
        MAX_COMMENTS
    )

    # --------------------------------------------------------
    # Retry count.
    # --------------------------------------------------------

    print(
        "Groq Retries:",
        MAX_GROQ_RETRIES
    )

    # --------------------------------------------------------
    # Server.
    # --------------------------------------------------------

    print(
        "Server:",
        "http://127.0.0.1:5000"
    )

    print(
        "================================================"
    )

    # --------------------------------------------------------
    # Start Flask server.
    # --------------------------------------------------------

    app.run(

        host="0.0.0.0",

        port=5000,

        debug=True
    )