import html
import os

import httpx

from fastapi import (
    APIRouter,
    File,
    Form,
    UploadFile,
)

from fastapi.responses import (
    HTMLResponse,
)

from app.evidence_links import (
    EvidenceLinkError,
    EvidenceLinkStore,
)


router = APIRouter()


def page_shell(
    title: str,
    body: str,
) -> str:
    return f"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta
    name="viewport"
    content="width=device-width, initial-scale=1"
>
<title>{html.escape(title)}</title>

<style>
* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;
    padding: 24px 16px;
    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
    background: #faf8f5;
    color: #212529;
}}

.card {{
    max-width: 520px;
    margin: 0 auto;
    background: white;
    border-radius: 20px;
    padding: 24px;
    box-shadow:
        0 10px 35px
        rgba(0,0,0,.08);
}}

h1 {{
    margin-top: 0;
    font-size: 26px;
}}

p {{
    line-height: 1.5;
}}

label {{
    display: block;
    font-weight: 600;
    margin: 20px 0 8px;
}}

input[type=file] {{
    width: 100%;
}}

button {{
    width: 100%;
    margin-top: 14px;
    border: 0;
    border-radius: 12px;
    padding: 14px;
    font-size: 16px;
    cursor: pointer;
}}

.primary {{
    background: #722f37;
    color: white;
}}

.secondary {{
    background: #f1eeee;
    color: #212529;
}}

.status {{
    margin-top: 12px;
    padding: 12px;
    border-radius: 10px;
    background: #f6f6f6;
    font-size: 14px;
}}

.note {{
    color: #666;
    font-size: 14px;
}}

.success {{
    font-size: 18px;
}}
</style>
</head>

<body>
<div class="card">
{body}
</div>
</body>
</html>
""".strip()


def error_page(
    message: str,
) -> HTMLResponse:
    return HTMLResponse(
        page_shell(
            "Evidence Link",
            f"""
<h1>CivicResolve</h1>
<p>{html.escape(message)}</p>
<p class="note">
Your original complaint is not affected.
</p>
""",
        ),
        status_code=410,
    )


@router.get(
    "/evidence/{token}",
    response_class=HTMLResponse,
)
async def evidence_page(
    token: str,
):
    store = EvidenceLinkStore()

    try:
        record = store.resolve(
            token
        )

    except EvidenceLinkError as exc:
        return error_page(
            str(exc)
        )

    complaint_id = html.escape(
        record["complaint_id"]
    )

    body = f"""
<h1>Add evidence</h1>

<p>
Complaint:
<strong>{complaint_id}</strong>
</p>

<p>
You can optionally add a photo,
your current location, or both.
</p>

<p class="note">
Camera and precise location are optional.
Your complaint remains registered even if
you choose not to provide them.
</p>

<form
    id="evidenceForm"
    method="post"
    action="/evidence/{html.escape(token)}/submit"
    enctype="multipart/form-data"
>

<label for="image">
Photo
</label>

<input
    id="image"
    name="image"
    type="file"
    accept="image/jpeg,image/png,image/webp"
    capture="environment"
>

<input
    id="latitude"
    name="latitude"
    type="hidden"
>

<input
    id="longitude"
    name="longitude"
    type="hidden"
>

<input
    id="gps_accuracy"
    name="gps_accuracy"
    type="hidden"
>

<input
    id="location_confirmed"
    name="location_confirmed"
    type="hidden"
    value="false"
>

<button
    type="button"
    class="secondary"
    onclick="getLocation()"
>
📍 Use My Current Location
</button>

<div
    id="locationStatus"
    class="status"
>
No precise location added.
</div>

<button
    type="submit"
    class="primary"
>
Submit Evidence
</button>

</form>

<script>
function getLocation() {{
    const status =
        document.getElementById(
            "locationStatus"
        );

    if (!navigator.geolocation) {{
        status.textContent =
            "Location is not supported by this browser.";
        return;
    }}

    status.textContent =
        "Requesting location permission...";

    navigator.geolocation.getCurrentPosition(
        function(position) {{
            document.getElementById(
                "latitude"
            ).value =
                position.coords.latitude;

            document.getElementById(
                "longitude"
            ).value =
                position.coords.longitude;

            document.getElementById(
                "gps_accuracy"
            ).value =
                position.coords.accuracy || "";

            document.getElementById(
                "location_confirmed"
            ).value =
                "true";

            status.textContent =
                "✓ Current location added. " +
                "Accuracy: approximately " +
                Math.round(
                    position.coords.accuracy
                ) +
                " meters.";
        }},
        function(error) {{
            document.getElementById(
                "location_confirmed"
            ).value =
                "false";

            status.textContent =
                "Location was not added. " +
                "You can still submit a photo.";
        }},
        {{
            enableHighAccuracy: true,
            timeout: 12000,
            maximumAge: 0
        }}
    );
}}

document.getElementById(
    "evidenceForm"
).addEventListener(
    "submit",
    function(event) {{
        const image =
            document.getElementById(
                "image"
            );

        const confirmed =
            document.getElementById(
                "location_confirmed"
            ).value === "true";

        const hasImage =
            image.files &&
            image.files.length > 0;

        if (!hasImage && !confirmed) {{
            event.preventDefault();

            alert(
                "Please add a photo, " +
                "your current location, or both."
            );
        }}
    }}
);
</script>
"""

    return HTMLResponse(
        page_shell(
            "CivicResolve Evidence",
            body,
        )
    )


@router.post(
    "/evidence/{token}/submit",
    response_class=HTMLResponse,
)
async def submit_evidence(
    token: str,
    image: UploadFile | None = File(None),
    latitude: float | None = Form(None),
    longitude: float | None = Form(None),
    gps_accuracy: float | None = Form(None),
    location_confirmed: bool = Form(False),
):
    store = EvidenceLinkStore()

    try:
        record = store.resolve(
            token
        )

    except EvidenceLinkError as exc:
        return error_page(
            str(exc)
        )

    complaint_id = (
        record["complaint_id"]
    )

    has_image = bool(
        image
        and image.filename
    )

    if (
        not has_image
        and not location_confirmed
    ):
        return HTMLResponse(
            page_shell(
                "Evidence Required",
                """
<h1>Nothing was submitted</h1>

<p>
Please add a photo or confirm your
current location before submitting.
</p>

<button
    class="secondary"
    onclick="history.back()"
>
Go Back
</button>
""",
            ),
            status_code=400,
        )

    data = {
        "location_confirmed":
            "true"
            if location_confirmed
            else "false",
    }

    if latitude is not None:
        data["latitude"] = str(
            latitude
        )

    if longitude is not None:
        data["longitude"] = str(
            longitude
        )

    if gps_accuracy is not None:
        data["gps_accuracy"] = str(
            gps_accuracy
        )

    files = None

    if has_image:
        image_bytes = await image.read()

        if len(image_bytes) > (
            8 * 1024 * 1024
        ):
            return HTMLResponse(
                page_shell(
                    "Image Too Large",
                    """
<h1>Photo is too large</h1>
<p>
Please use an image smaller than 8 MB.
</p>
<button
    class="secondary"
    onclick="history.back()"
>
Go Back
</button>
""",
                ),
                status_code=413,
            )

        files = {
            "image": (
                image.filename,
                image_bytes,
                image.content_type
                or "image/jpeg",
            )
        }

    base_url = os.getenv(
        "CIVICRESOLVE_API_URL",
        "http://127.0.0.1:8000",
    ).rstrip("/")

    endpoint = (
        f"{base_url}"
        f"/api/complaints/"
        f"{complaint_id}"
        f"/evidence"
    )

    try:
        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:
            response = await client.post(
                endpoint,
                data=data,
                files=files,
            )

    except Exception:
        return HTMLResponse(
            page_shell(
                "Temporary Error",
                """
<h1>Could not upload evidence</h1>

<p>
Please try again in a moment.
Your complaint is still registered.
</p>

<button
    class="secondary"
    onclick="history.back()"
>
Try Again
</button>
""",
            ),
            status_code=502,
        )

    if response.status_code >= 400:
        try:
            message = (
                response.json().get(
                    "detail",
                    "Evidence upload failed.",
                )
            )
        except Exception:
            message = (
                "Evidence upload failed."
            )

        return HTMLResponse(
            page_shell(
                "Upload Failed",
                f"""
<h1>Could not add evidence</h1>
<p>{html.escape(str(message))}</p>
<p>
Your complaint is still registered.
</p>
<button
    class="secondary"
    onclick="history.back()"
>
Try Again
</button>
""",
            ),
            status_code=502,
        )

    store.mark_used(
        token
    )

    return HTMLResponse(
        page_shell(
            "Evidence Added",
            f"""
<h1>Evidence added ✓</h1>

<p class="success">
Your evidence has been attached to
<strong>{html.escape(complaint_id)}</strong>.
</p>

<p>
You can close this page.
</p>
""",
        )
    )
