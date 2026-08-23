import os
import hmac

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, FileResponse, Response

from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VoiceGrant


router = APIRouter()


def get_public_host() -> str:
    host = os.getenv(
        "PUBLIC_HOST",
        "",
    ).strip()

    host = host.replace(
        "https://",
        "",
    )

    host = host.replace(
        "http://",
        "",
    )

    host = host.replace(
        "wss://",
        "",
    )

    host = host.replace(
        "ws://",
        "",
    )

    return host.rstrip("/")


def verify_test_secret(
    supplied: str,
):
    expected = os.getenv(
        "BROWSER_TEST_SECRET",
        "",
    ).strip()

    if not expected:
        raise HTTPException(
            status_code=500,
            detail=(
                "BROWSER_TEST_SECRET "
                "is not configured"
            ),
        )

    if not hmac.compare_digest(
        supplied,
        expected,
    ):
        raise HTTPException(
            status_code=403,
            detail="Invalid browser test key",
        )


@router.get(
    "/browser-token"
)
async def browser_token(
    key: str = Query(...),
):
    verify_test_secret(
        key
    )

    account_sid = os.getenv(
        "TWILIO_ACCOUNT_SID",
        "",
    ).strip()

    api_key_sid = os.getenv(
        "TWILIO_API_KEY_SID",
        "",
    ).strip()

    api_key_secret = os.getenv(
        "TWILIO_API_KEY_SECRET",
        "",
    ).strip()

    twiml_app_sid = os.getenv(
        "TWILIO_TWIML_APP_SID",
        "",
    ).strip()

    identity = os.getenv(
        "BROWSER_TEST_IDENTITY",
        "civicresolve_mac_test",
    ).strip()

    required = {
        "TWILIO_ACCOUNT_SID":
            account_sid,
        "TWILIO_API_KEY_SID":
            api_key_sid,
        "TWILIO_API_KEY_SECRET":
            api_key_secret,
        "TWILIO_TWIML_APP_SID":
            twiml_app_sid,
    }

    missing = [
        name
        for name, value
        in required.items()
        if not value
    ]

    if missing:
        raise HTTPException(
            status_code=500,
            detail=(
                "Missing Twilio settings: "
                + ", ".join(missing)
            ),
        )

    token = AccessToken(
        account_sid,
        api_key_sid,
        api_key_secret,
        identity=identity,
        ttl=3600,
    )

    voice_grant = VoiceGrant(
        outgoing_application_sid=
            twiml_app_sid,
        incoming_allow=False,
    )

    token.add_grant(
        voice_grant
    )

    jwt_token = token.to_jwt()

    if isinstance(
        jwt_token,
        bytes,
    ):
        jwt_token = jwt_token.decode(
            "utf-8"
        )

    return {
        "token":
            jwt_token,
        "identity":
            identity,
    }


@router.post(
    "/browser-voice"
)
async def browser_voice():
    public_host = (
        get_public_host()
    )

    if not public_host:
        return Response(
            content=(
                "<Response>"
                "<Say>"
                "Public host is not "
                "configured."
                "</Say>"
                "</Response>"
            ),
            media_type="application/xml",
        )

    stream_url = (
        f"wss://"
        f"{public_host}"
        f"/media-stream"
    )

    test_sms_to = os.getenv(
        "BROWSER_TEST_SMS_TO",
        "",
    ).strip()

    parameter_xml = ""

    if test_sms_to:
        parameter_xml = (
            '<Parameter '
            'name="caller_number" '
            f'value="{test_sms_to}" />'
        )

    twiml = f"""
<Response>
    <Connect>
        <Stream url="{stream_url}">
            {parameter_xml}
        </Stream>
    </Connect>
</Response>
""".strip()

    print(
        "\n💻 Browser Voice SDK call",
        flush=True,
    )

    print(
        "🔗 Media stream:",
        stream_url,
        flush=True,
    )

    return Response(
        content=twiml,
        media_type="application/xml",
    )


@router.get(
    "/browser-sdk.js"
)
async def browser_sdk():
    return FileResponse(
        "app/static/twilio.min.js",
        media_type=
            "application/javascript",
    )


@router.get(
    "/browser-test",
    response_class=HTMLResponse,
)
async def browser_test(
    key: str = Query(...),
):
    verify_test_secret(
        key
    )

    html = """
<!doctype html>

<html>
<head>
    <meta charset="utf-8">
    <meta
        name="viewport"
        content="width=device-width,
        initial-scale=1"
    >

    <title>
        CivicResolve Voice Test
    </title>

    <style>
        body {
            font-family:
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                sans-serif;

            max-width: 620px;
            margin: 60px auto;
            padding: 24px;
            background: #faf8f5;
            color: #212529;
        }

        .card {
            background: white;
            border-radius: 18px;
            padding: 30px;
            box-shadow:
                0 12px 40px
                rgba(0,0,0,.08);
        }

        h1 {
            margin-top: 0;
        }

        #status {
            padding: 14px;
            background: #f4f4f4;
            border-radius: 10px;
            margin: 20px 0;
            font-weight: 600;
        }

        button {
            padding: 14px 20px;
            font-size: 16px;
            border-radius: 10px;
            border: none;
            cursor: pointer;
            margin-right: 8px;
        }

        #start {
            background: #722f37;
            color: white;
        }

        #end {
            background: #dedede;
            color: #222;
        }

        .small {
            margin-top: 20px;
            font-size: 14px;
            color: #666;
        }
    </style>
</head>

<body>

<div class="card">

    <h1>
        CivicResolve Voice Test
    </h1>

    <p>
        Use your Mac microphone and
        speakers to test the real
        Twilio voice pipeline.
    </p>

    <div id="status">
        Loading Twilio...
    </div>

    <button
        id="start"
        disabled
    >
        Start Test Call
    </button>

    <button
        id="end"
        disabled
    >
        End Call
    </button>

    <div class="small">
        Chrome microphone permission
        must be allowed.
    </div>

</div>


<script src="/browser-sdk.js"></script>

<script>
let device = null;
let activeCall = null;

const statusBox =
    document.getElementById(
        "status"
    );

const startButton =
    document.getElementById(
        "start"
    );

const endButton =
    document.getElementById(
        "end"
    );

const pageParams =
    new URLSearchParams(
        window.location.search
    );

const testKey =
    pageParams.get("key");


function setStatus(text) {
    statusBox.textContent = text;
}


async function fetchToken() {
    const url =
        "/browser-token?key="
        + encodeURIComponent(
            testKey
        );

    const response =
        await fetch(
            url,
            {
                cache:
                    "no-store"
            }
        );

    const data =
        await response.json();

    if (!response.ok) {
        throw new Error(
            data.detail
            || "Token request failed"
        );
    }

    return data;
}


async function initialiseDevice() {
    try {
        setStatus(
            "Getting Twilio token..."
        );

        const data =
            await fetchToken();

        device =
            new Twilio.Device(
                data.token,
                {
                    logLevel: 0,
                    enableImprovedSignalingErrorPrecision: true
                }
            );

        device.on(
            "error",
            function(error) {
                console.error(
                    error
                );

                setStatus(
                    "Twilio error: "
                    + error.message
                );
            }
        );

        device.on(
            "tokenWillExpire",
            async function() {
                const fresh =
                    await fetchToken();

                device.updateToken(
                    fresh.token
                );
            }
        );

        setStatus(
            "Ready — click Start Test Call"
        );

        startButton.disabled =
            false;

    } catch (error) {
        console.error(
            error
        );

        setStatus(
            "Setup failed: "
            + error.message
        );
    }
}


async function startCall() {
    try {
        startButton.disabled =
            true;

        setStatus(
            "Requesting microphone..."
        );

        const call =
            await device.connect({
                params: {
                    mode:
                        "civicresolve-browser-test"
                }
            });

        activeCall = call;

        endButton.disabled =
            false;

        setStatus(
            "Connected to CivicResolve"
        );

        call.on(
            "disconnect",
            function() {
                activeCall = null;

                startButton.disabled =
                    false;

                endButton.disabled =
                    true;

                setStatus(
                    "Call ended"
                );
            }
        );

        call.on(
            "error",
            function(error) {
                console.error(
                    error
                );

                setStatus(
                    "Call error: "
                    + error.message
                );
            }
        );

    } catch (error) {
        console.error(
            error
        );

        startButton.disabled =
            false;

        endButton.disabled =
            true;

        setStatus(
            "Call failed: "
            + error.message
        );
    }
}


function endCall() {
    if (
        activeCall
    ) {
        activeCall.disconnect();
    }
}


startButton.addEventListener(
    "click",
    startCall
);

endButton.addEventListener(
    "click",
    endCall
);


initialiseDevice();
</script>

</body>
</html>
"""

    return HTMLResponse(
        html
    )
