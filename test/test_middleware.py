import sys
import pytest
from io import StringIO

from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse

from test import stdout_redirect
from fastapi_profiler import PyInstrumentProfilerMiddleware


@pytest.fixture(name="test_middleware")
def test_middleware():
    def _test_middleware(**profiler_kwargs):
        app = FastAPI()
        if profiler_kwargs.get("profiler_output_type") != "text":
            profiler_kwargs.update({"server_app": app})
        app.add_middleware(PyInstrumentProfilerMiddleware, **profiler_kwargs)

        @app.route("/test")
        async def normal_request(request):
            return JSONResponse({"retMsg": "Normal Request test Success!"})

        return app

    return _test_middleware


class TestProfilerMiddleware:
    @pytest.fixture
    def client(self, test_middleware):
        return TestClient(test_middleware())

    def test_profiler_print_at_console(self, client):
        # Hack the console to get the result from print function
        stdout_redirect.fp = StringIO()
        temp_stdout, sys.stdout = sys.stdout, stdout_redirect

        # request
        request_path = "/test"
        client.get(request_path)

        sys.stdout = temp_stdout
        assert f"Path: {request_path}" in stdout_redirect.fp.getvalue()

    def test_profiler_export_to_html(self, test_middleware, tmpdir):
        full_path = tmpdir / "test.html"

        with TestClient(
            test_middleware(
                profiler_output_type="html",
                is_print_each_request=False,
                profiler_interval=0.0000001,
                html_file_name=str(full_path),
            )
        ) as client:
            # request
            request_path = "/test"
            client.get(request_path)

        # HTML will record the py file name.
        assert "profiler.py" in full_path.read_text("utf-8")

    def test_profiler_export_to_prof(self, test_middleware, tmpdir):
        full_path = tmpdir / "test.prof"

        with TestClient(
            test_middleware(
                profiler_output_type="prof",
                is_print_each_request=False,
                profiler_interval=0.0000001,
                prof_file_name=str(full_path),
            )
        ) as client:
            # request
            request_path = "/test"
            client.get(request_path)

        # Check if the .prof file has been created and has content
        assert full_path.exists()
        assert full_path.read_binary()

    def test_profiler_export_to_json(self, test_middleware, tmpdir):
        full_path = tmpdir / "test.json"

        with TestClient(
            test_middleware(
                profiler_output_type="json",
                is_print_each_request=False,
                profiler_interval=0.0000001,
                prof_file_name=str(full_path),
            )
        ) as client:
            # request
            request_path = "/test"
            client.get(request_path)

        # Check if the .prof file has been created and has content
        assert full_path.exists()
        assert full_path.read_binary()

    def test_profiler_export_to_speedscope(self, test_middleware, tmpdir):
        full_path = tmpdir / "test_speedscope.json"

        with TestClient(
            test_middleware(
                profiler_output_type="speedscope",
                is_print_each_request=False,
                profiler_interval=0.0000001,
                prof_file_name=str(full_path),
            )
        ) as client:
            # request
            request_path = "/test"
            client.get(request_path)

        # Check if the .prof file has been created and has content
        assert full_path.exists()
        assert full_path.read_binary()
