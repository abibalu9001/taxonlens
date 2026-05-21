from django.shortcuts import render

from PIL import Image

import google.generativeai as genai

import json

from .models import Identification

import os


# Configure Gemini API

genai.configure(

    api_key=os.environ.get(
        "GEMINI_API_KEY"
    )

)


# Gemini Model

model = genai.GenerativeModel(

    "gemini-2.5-flash"

)


def home(request):

    common_name = ""

    scientific_name = ""

    family_name = ""

    tamil_name = ""

    confidence = ""

    wikipedia_link = ""

    description = ""

    ai_cost = 0


    if request.method == "POST":

        try:

            # Original uploaded file

            uploaded_image = request.FILES["image"]


            # Open image using Pillow

            image = Image.open(
                uploaded_image
            )


            # Send image to Gemini

            response = model.generate_content([

                """
                Identify this organism carefully.

                Return ONLY valid JSON.

                {

                  "common_name": "",

                  "scientific_name": "",

                  "family_name": "",

                  "tamil_name": "",

                  "confidence": "",

                  "wikipedia_link": "",

                  "description": ""

                }

                Rules:

                - confidence must be percentage estimate

                - wikipedia link must be valid

                - tamil_name should be in Tamil language if known

                - description should be short

                """,

                image

            ])


            # Get Gemini response text

            text = response.text


            # Remove markdown formatting

            text = text.replace(

                "```json",

                ""

            )

            text = text.replace(

                "```",

                ""

            )


            # Convert JSON text to dictionary

            data = json.loads(text)


            # Extract data

            common_name = data.get(

                "common_name",

                "-"

            )

            scientific_name = data.get(

                "scientific_name",

                "-"

            )

            family_name = data.get(

                "family_name",

                "-"

            )

            tamil_name = data.get(

                "tamil_name",

                "-"

            )

            confidence = data.get(

                "confidence",

                "0%"

            )

            wikipedia_link = data.get(

                "wikipedia_link",

                ""

            )

            description = data.get(

                "description",

                "-"

            )


            # ===== REAL AI COST =====

            usage = response.usage_metadata


            prompt_tokens = (

                usage.prompt_token_count

            )


            response_tokens = (

                usage.candidates_token_count

            )


            # Gemini Flash Pricing

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


            # Save to database

            Identification.objects.create(

                image=uploaded_image,

                common_name=common_name,

                scientific_name=scientific_name,

                family_name=family_name,

                tamil_name=tamil_name,

                confidence=confidence,

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
