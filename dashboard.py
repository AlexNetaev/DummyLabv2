"""Entry point for the OrbusSim Dummy V2 dashboard server."""
import uvicorn


def main():
    """Startet den FastAPI-Server."""
    uvicorn.run("orbus_dummy_v2.api.server:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
