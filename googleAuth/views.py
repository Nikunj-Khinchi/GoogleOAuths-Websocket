import os
import tempfile
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.conf import settings
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt  # Optional: If using CSRF token, remove this
def upload_to_drive(request):
    if "credentials" not in request.session:
        return JsonResponse({"error": "User not authenticated"}, status=401)

    credentials = Credentials(**request.session["credentials"])
    service = build("drive", "v3", credentials=credentials)

    if request.method == "POST" and request.FILES.get("file"):
        uploaded_file = request.FILES["file"]

        # Save file temporarily
        temp_file = tempfile.NamedTemporaryFile(delete=False)  # Do NOT delete immediately
        temp_file_path = temp_file.name  # Get the temporary file path

        try:
            # Write the file contents
            for chunk in uploaded_file.chunks():
                temp_file.write(chunk)

            temp_file.close()  # Ensure file is closed before upload

            # Upload the file to Google Drive
            file_metadata = {"name": uploaded_file.name}
            media = MediaFileUpload(temp_file_path, mimetype=uploaded_file.content_type, resumable=True)
            file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()

            return JsonResponse({"file_id": file["id"], "message": "File uploaded successfully"})
        
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

        finally:
            # Ensure the file is fully closed before attempting to delete it
            if os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except PermissionError:
                    pass  # If still locked, let the system clean it up later

    return JsonResponse({"error": "No file provided"}, status=400)


def index(request):
    user_info = request.session.get("user_info", None)
    return render(request, "index.html", {"user_info": user_info})

def google_login(request):
    flow = Flow.from_client_secrets_file(
        settings.GOOGLE_CREDENTIALS_FILE,
        scopes=settings.GOOGLE_SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
    )
    auth_url, _ = flow.authorization_url(prompt="consent")
    return redirect(auth_url)


def google_callback(request):
    code = request.GET.get("code")
    if not code:
        return JsonResponse({"error": "No authorization code provided"}, status=400)

    flow = Flow.from_client_secrets_file(
        settings.GOOGLE_CREDENTIALS_FILE,
        scopes=settings.GOOGLE_SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
    )
    flow.fetch_token(code=code)
    credentials = flow.credentials

    service = build("oauth2", "v2", credentials=credentials)
    user_info = service.userinfo().get().execute()

    request.session["credentials"] = credentials_to_dict(credentials)
    request.session["user_info"] = user_info

    return redirect("/")

def google_logout(request):
    request.session.flush()
    return redirect("/")

def credentials_to_dict(credentials):
    return {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes,
    }

    return JsonResponse({"error": "No file provided"}, status=400)

def fetch_drive_files(request):
    if "credentials" not in request.session:
        return JsonResponse({"error": "User not authenticated"}, status=401)

    credentials = Credentials(**request.session["credentials"])
    service = build("drive", "v3", credentials=credentials)

    results = service.files().list().execute()
    files = results.get("files", [])

    return JsonResponse({"files": files})
