from django.shortcuts import render

from PIL import Image

import google.generativeai as genai

import json

from .models import Identification

import os

import requests


# ==============================
# Configure Gemini API
# ==============================

genai.configure(

    api_key=os.environ.get(
        "GEMINI_API_KEY"
    )

)


# ==============================
# Gemini Model
# ==============================

model = genai.GenerativeModel(

    "gemini-2.5-flash"

)


# ==============================
# PlantNet Function
# ==============================

def identify_plant(image_file):

    api_key = os.environ.get(
        "PLANTNET_API_KEY"
    )

    url = (

        f"https://my-api.plantnet.org/v2/identify/all"

        f"?api-key={api_key}"

    )

    files = {

        "images": image_file

    }

    response = requests.post(

        url,

        files=files

    )

    data = response.json()


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


    return scientific_name, confidence


# ==============================
# iNaturalist Function
# ==============================

def identify_animal(image_url):

    url = (

        "https://api.inaturalist.org/v1/"

        "computervision/score_image"

    )

    data = {

        "image_url": image_url

    }

    response = requests.post(

        url,

        data=data

    )

    result = response.json()


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


# ==============================
# Main Home View
# ==============================

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

            # ==============================
            # Uploaded Image
            # ==============================

            uploaded_image = request.FILES["image"]

            image = Image.open(
                uploaded_image
            )


            # ==============================
            # Detect Plant or Animal
            # ==============================

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


            # ==============================
            # PLANT IDENTIFICATION
            # ==============================

            if organism_type == "PLANT":

                scientific_name, confidence = identify_plant(

                    uploaded_image

                )

                common_name = scientific_name


            # ==============================
            # ANIMAL IDENTIFICATION
            # ==============================

            else:

                # Save temporary object

                temp = Identification.objects.create(

                    image=uploaded_image,

                    common_name="Processing",

                    scientific_name="Processing"

                )


                # Get image URL

                image_url = request.build_absolute_uri(

                    temp.image.url

                )


                # Identify animal

                common_name, scientific_name, confidence = identify_animal(

                    image_url

                )


            # ==============================
            # Gemini Enrichment
            # ==============================

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


            # ==============================
            # Clean Response
            # ==============================

            text = response.text

            text = text.replace(
                "```json",
                ""
            )

            text = text.replace(
                "```",
                ""
            )


            # ==============================
            # Parse JSON
            # ==============================

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


            # ==============================
            # AI COST CALCULATION
            # ==============================

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


            # ==============================
            # Save Final Result
            # ==============================

            Identification.objects.create(

                image=uploaded_image,

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
