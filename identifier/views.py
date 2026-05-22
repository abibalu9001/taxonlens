from django.shortcuts import render

from PIL import Image

import google.generativeai as genai

import json

from .models import Identification

import os

import requests

from io import BytesIO


# =========================================
# Configure Gemini
# =========================================

genai.configure(

    api_key=os.environ.get(
        "GEMINI_API_KEY"
    )

)


# =========================================
# Gemini Model
# =========================================

model = genai.GenerativeModel(

    "gemini-2.5-flash"

)


# =========================================
# PLANT IDENTIFICATION
# =========================================

def identify_plant(image_file):

    api_key = os.environ.get(
        "PLANTNET_API_KEY"
    )

    url = (

        f"https://my-api.plantnet.org/v2/identify/all"

        f"?api-key={api_key}"

    )


    # Open image

    img = Image.open(image_file)


    # Convert unsupported formats

    img = img.convert("RGB")


    # Convert to JPEG in memory

    buffer = BytesIO()

    img.save(

        buffer,

        format="JPEG"

    )

    buffer.seek(0)


    files = {

        "images": (

            "image.jpg",

            buffer,

            "image/jpeg"

        )

    }


    response = requests.post(

        url,

        files=files

    )


    data = response.json()


    # Safety checks

    if "results" not in data:

        raise Exception(

            f"PlantNet Error: {data}"

        )


    if len(data["results"]) == 0:

        raise Exception(

            "No plant identified"

        )


    best_match = data[
        "results"
    ][0]


    scientific_name = best_match[
        "species"
    ][
        "scientificNameWithoutAuthor"
    ]


    confidence = round(

        best_match["score"] * 100,

        2

    )


    return (

        scientific_name,

        confidence

    )


# =========================================
# ANIMAL IDENTIFICATION
# =========================================

def identify_animal(image_file):

    url = (

        "https://api.inaturalist.org/v1/"

        "computervision/score_image"

    )


    # Open image

    img = Image.open(image_file)


    # Convert to RGB

    img = img.convert("RGB")


    # Convert to JPEG

    buffer = BytesIO()

    img.save(

        buffer,

        format="JPEG"

    )

    buffer.seek(0)


    files = {

        "image": (

            "image.jpg",

            buffer,

            "image/jpeg"

        )

    }


    response = requests.post(

        url,

        files=files

    )


    result = response.json()


    # Safety checks

    if "results" not in result:

        raise Exception(

            f"iNaturalist Error: {result}"

        )


    if len(result["results"]) == 0:

        raise Exception(

            "No animal identified"

        )


    best = result[
        "results"
    ][0]


    scientific_name = best[
        "taxon"
    ][
        "name"
    ]


    common_name = best[
        "taxon"
    ].get(

        "preferred_common_name",

        scientific_name

    )


    confidence = round(

        best["combined_score"] * 100,

        2

    )


    return (

        common_name,

        scientific_name,

        confidence

    )


# =========================================
# MAIN HOME VIEW
# =========================================

def home(request):

    common_name = ""

    scientific_name = ""

    family_name = ""

    tamil_name = ""

    confidence = ""

    wikipedia_link = ""

    description = ""

    ai_cost = 0

    organism_type = ""


    if request.method == "POST":

        try:

            # =========================================
            # Uploaded Image
            # =========================================

            uploaded_image = request.FILES["image"]


            # Open image for Gemini

            image = Image.open(
                uploaded_image
            )


            # =========================================
            # Detect PLANT or ANIMAL
            # =========================================

            classify = model.generate_content([

                """

                Is this image a PLANT or ANIMAL?

                Reply ONLY with:

                PLANT

                or

                ANIMAL

                """,

                image

            ])


            organism_type = (

                classify.text
                .strip()
                .upper()

            )


            # Reset file pointer

            uploaded_image.seek(0)


            # =========================================
            # PLANT
            # =========================================

            if organism_type == "PLANT":

                scientific_name, confidence = identify_plant(

                    uploaded_image

                )

                common_name = scientific_name


            # =========================================
            # ANIMAL
            # =========================================

            else:

                common_name, scientific_name, confidence = identify_animal(

                    uploaded_image

                )


            # =========================================
            # GEMINI ENRICHMENT
            # =========================================

            response = model.generate_content(

                f"""

                Give details for:

                {scientific_name}

                Return ONLY valid JSON.

                {{

                  "common_name": "",

                  "family_name": "",

                  "tamil_name": "",

                  "wikipedia_link": "",

                  "description": ""

                }}

                """

            )


            # =========================================
            # Clean Gemini Response
            # =========================================

            text = response.text

            text = text.replace(

                "```json",

                ""

            )

            text = text.replace(

                "```",

                ""

            )


            # =========================================
            # Parse JSON
            # =========================================

            data = json.loads(text)


            common_name = data.get(

                "common_name",

                common_name

            )

            family_name = data.get(

                "family_name",

                "-"

            )

            tamil_name = data.get(

                "tamil_name",

                "-"

            )

            wikipedia_link = data.get(

                "wikipedia_link",

                ""

            )

            description = data.get(

                "description",

                "-"

            )


            # =========================================
            # AI COST
            # =========================================

            usage = response.usage_metadata


            prompt_tokens = (

                usage.prompt_token_count

            )


            response_tokens = (

                usage.candidates_token_count

            )


            input_cost = (

                prompt_tokens / 1_000_000

            ) * 0.075


            output_cost = (

                response_tokens / 1_000_000

            ) * 0.30


            ai_cost = round(

                input_cost + output_cost,

                8

            )


            # =========================================
            # SAVE TO DATABASE
            # =========================================

            uploaded_image.seek(0)

            image_for_db = request.FILES["image"]


            Identification.objects.create(

                image=image_for_db,

                organism_type=organism_type,

                common_name=common_name,

                scientific_name=scientific_name,

                family_name=family_name,

                tamil_name=tamil_name,

                confidence=confidence,

                wikipedia_link=wikipedia_link,

                description=description,

                ai_cost=ai_cost

            )


        except Exception as e:

            common_name = "Error"

            scientific_name = str(e)

            family_name = "-"

            tamil_name = "-"

            confidence = "0%"

            wikipedia_link = ""

            description = (

                "Unable to identify organism."

            )

            ai_cost = 0


    return render(

        request,

        "index.html",

        {

            "organism_type": organism_type,

            "common_name": common_name,

            "scientific_name": scientific_name,

            "family_name": family_name,

            "tamil_name": tamil_name,

            "confidence": confidence,

            "wikipedia_link": wikipedia_link,

            "description": description,

            "ai_cost": ai_cost

        }

    )
