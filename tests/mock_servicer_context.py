"""Mock implementation of grpc.ServicerContext for testing purposes."""

from __future__ import annotations

from typing import Any, Callable, Dict, Tuple

import grpc


class MockServicerContext(grpc.ServicerContext):
    def __init__(self):
        self._code = None
        self._details = None

    def cancel(self) -> bool:
        return True

    def is_cancelled(self) -> bool:
        return False

    def set_code(self, code: grpc.StatusCode):
        self._code = code

    def set_details(self, details: str):
        self._details = details

    def abort(self, code: grpc.StatusCode, details: str):
        self.set_code(code)
        self.set_details(details)
        raise grpc.RpcError(details)

    def abort_with_status(self, status: grpc.Status):
        self.set_code(status.code)
        self.set_details(status.details)
        raise grpc.RpcError(status.details)

    def is_active(self):
        return True

    def time_remaining(self):
        return 1000

    def add_callback(self, callback: Callable[[], None]) -> bool:
        return True

    def invocation_metadata(self):
        return ()

    def peer(self):
        return "peer"

    def send_initial_metadata(self, initial_metadata: Tuple[Tuple[str, Any], ...]) -> None:
        pass

    def set_trailing_metadata(self, trailing_metadata: Tuple[Tuple[str, Any], ...]) -> None:
        pass

    def auth_context(self) -> Dict[str, Any]:
        return {}

    def set_compression(self, compression: Any) -> None:
        pass

    def disable_next_message_compression(self):
        pass

    def initial_metadata(self) -> Tuple[Tuple[str, Any], ...]:
        return ()

    def trailing_metadata(self) -> Tuple[Tuple[str, Any], ...]:
        return ()

    def code(self):
        return self._code

    def details(self):
        return self._details

    def peer_identities(self) -> Tuple[bytes, ...]:
        return ()

    def peer_identity_key(self) -> str:
        return ""
