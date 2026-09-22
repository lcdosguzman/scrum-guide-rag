import json
import mimetypes
from pathlib import Path
from typing import Optional
from urllib.parse import unquote

from scrum_rag.rag import ScrumRag

STATIC_DIR = Path(__file__).parent / "static"

rag: Optional[ScrumRag] = None


async def app(scope, receive, send):
    if scope["type"] != "http":
        return

    path = scope.get("path", "/")
    method = scope.get("method", "GET")

    if method == "GET" and path == "/":
        await send_file(send, STATIC_DIR / "index.html", "text/html; charset=utf-8")
        return

    if method == "GET" and path.startswith("/static/"):
        requested = unquote(path.removeprefix("/static/"))
        file_path = (STATIC_DIR / requested).resolve()
        if STATIC_DIR.resolve() not in file_path.parents:
            await send_json(send, {"error": "Ruta invalida"}, status=400)
            return
        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        await send_file(send, file_path, content_type)
        return

    if method == "GET" and path == "/api/health":
        await send_json(send, {"status": "ok"})
        return

    if method == "POST" and path == "/api/chat":
        payload = await read_json(receive)
        question = str(payload.get("question", "")).strip()
        if not question:
            await send_json(send, {"error": "La pregunta no puede estar vacia."}, status=400)
            return

        try:
            result = get_rag().ask(question)
        except Exception as error:
            await send_json(send, {"error": str(error)}, status=500)
            return

        await send_json(
            send,
            {
                "answer": result.answer,
                "sources": [
                    {
                        "index": source.index,
                        "source": source.source,
                        "page": source.page,
                        "preview": source.preview,
                    }
                    for source in result.sources
                ],
            },
        )
        return

    await send_json(send, {"error": "No encontrado"}, status=404)


def get_rag() -> ScrumRag:
    global rag
    if rag is None:
        rag = ScrumRag()
    return rag


async def read_json(receive) -> dict:
    body = b""
    more_body = True
    while more_body:
        message = await receive()
        body += message.get("body", b"")
        more_body = message.get("more_body", False)
    if not body:
        return {}
    return json.loads(body.decode("utf-8"))


async def send_file(send, path: Path, content_type: str) -> None:
    if not path.exists() or not path.is_file():
        await send_json(send, {"error": "Archivo no encontrado"}, status=404)
        return
    content = path.read_bytes()
    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [
                [b"content-type", content_type.encode("utf-8")],
                [b"content-length", str(len(content)).encode("utf-8")],
                [b"cache-control", b"no-store"],
            ],
        }
    )
    await send({"type": "http.response.body", "body": content})


async def send_json(send, payload: dict, status: int = 200) -> None:
    body = json.dumps(payload).encode("utf-8")
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [
                [b"content-type", b"application/json; charset=utf-8"],
                [b"content-length", str(len(body)).encode("utf-8")],
            ],
        }
    )
    await send({"type": "http.response.body", "body": body})
