import base64
import io

from PIL import Image
from huggingface_hub import InferenceClient

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.conf import settings

# ============================================================
# CONFIGURE HUGGING FACE (GLOBAL)
# ============================================================
# Put your HF token into HF_API_KEY in Render / .env
HF_VISION_MODEL_ID = "llava-hf/llava-1.5-7b-hf"          # vision-language model
HF_TEXT_MODEL_ID = "HuggingFaceH4/zephyr-7b-beta"        # text chat model [web:61][web:55]

hf_vision_client = InferenceClient(
    model=HF_VISION_MODEL_ID,
    token=settings.HF_API_KEY,
)

hf_text_client = InferenceClient(
    model=HF_TEXT_MODEL_ID,
    token=settings.HF_API_KEY,
)

# ============================================================
# STATIC PAGE ROUTES
# ============================================================
def homepage(request): return render(request, "index.html")
def services(request): return render(request, "services.html")
def about(request): return render(request, "about.html")
def team(request): return render(request, "team.html")
def contact(request): return render(request, "contact.html")
def login(request): return render(request, "login.html")
def signup(request): return render(request, "signup.html")
def pickup(request): return render(request, "pickup.html")
def reqs(request): return render(request, "reqs.html")
def detection(request): return render(request, "detection.html")
def data_destruction(request): return render(request, "data-destruction.html")
def refurbishment(request): return render(request, "refurbishment.html")

# ============================================================
# CAMERA PAGE
# ============================================================
def ewaste_camera_page(request):
    return render(request, "ewaste-camera.html")

# ============================================================
# STRICT E-WASTE DETECTION USING HF VISION
# ============================================================
@csrf_exempt
def camera_ai_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    image_data = request.POST.get("image")

    # ---- Validate Base64 ----
    if not image_data or "," not in image_data:
        return JsonResponse({"detected": "error", "caption": "invalid-image"}, status=400)

    try:
        header, base64_data = image_data.split(",", 1)

        if not (
            header.startswith("data:image/jpeg")
            or header.startswith("data:image/png")
        ):
            return JsonResponse(
                {"detected": "error", "caption": "unsupported-format"},
                status=400,
            )

        image_bytes = base64.b64decode(base64_data)

        if len(image_bytes) < 4000:
            return JsonResponse(
                {"detected": "error", "caption": "too-small-image"},
                status=400,
            )

        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    except Exception:
        return JsonResponse(
            {"detected": "error", "caption": "bad-image-data"},
            status=400,
        )

    strict_prompt = (
        "You are an object identification system. "
        "Return ONLY a single object name, no punctuation. "
        "Electronics: phone, charger, adapter, cable, battery, laptop, camera, "
        "mouse, keyboard, earbuds, airpods, webcam, powerbank, speaker, remote. "
        "If unsure, still guess one object."
    )

    try:
        # Vision-language chat: image + text prompt
        result = hf_vision_client.chat_completion(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": strict_prompt},
                        {"type": "image", "image": img},
                    ],
                }
            ],
            max_tokens=16,
        )

        raw_content = result.choices[0].message["content"]

        # content can be list-of-parts or string depending on model [web:61]
        if isinstance(raw_content, list):
            text_parts = [
                p.get("text", "")
                for p in raw_content
                if p.get("type") == "text"
            ]
            caption_raw = " ".join(text_parts)
        else:
            caption_raw = str(raw_content)

        caption_raw = caption_raw.strip().lower()
        caption = caption_raw.split()[0] if caption_raw else "unknown"

    except Exception as e:
        print("HF Vision Error:", repr(e))
        return JsonResponse(
            {"detected": "error", "caption": "ai-error"}
        )

    ewaste_keywords = [
        "phone", "mobile", "smartphone",
        "charger", "adapter", "cable", "wire", "usb",
        "battery", "powerbank",
        "earbuds", "airpods",
        "laptop", "mouse", "keyboard",
        "speaker", "camera", "webcam",
        "remote", "gadget", "device",
    ]

    detected = "ewaste" if any(k in caption for k in ewaste_keywords) else "not-ewaste"

    return JsonResponse({"detected": detected, "caption": caption})

# ============================================================
# CHATBOT USING HF TEXT MODEL
# ============================================================
@csrf_exempt
def chatbot_response(request):
    if request.method != "POST":
        return JsonResponse({"response": "Invalid request"}, status=400)

    user_message = request.POST.get("message", "")

    if not user_message:
        return JsonResponse({"response": "Please enter a message."})

    try:
        chat = hf_text_client.chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": "You are an e-waste guide. Answer briefly.",
                },
                {
                    "role": "user",
                    "content": user_message,
                },
            ],
            max_tokens=256,
        )

        bot_reply = chat.choices[0].message["content"]
        if isinstance(bot_reply, list):
            # normalize to string if model returns parts
            bot_reply = "".join(
                p.get("text", "") for p in bot_reply if p.get("type") == "text"
            )

    except Exception as e:
        print("HF Chat Error:", repr(e))
        bot_reply = "Sorry, technical issue occurred."

    return JsonResponse({"response": bot_reply})
