# Copyright The KiCad Developers
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""create_items / update_items decode the items KiCad sends back (issue #147)."""

from typing import Any

import pytest

from kipy.board import Board
from kipy.board_types import Track
from kipy.errors import ApiError
from kipy.proto.common.commands import editor_commands_pb2
from kipy.proto.common.types import DocumentSpecifier, base_types_pb2
from kipy.schematic import Schematic
from kipy.schematic_types import Junction
from kipy.util import pack_any


class _FakeKiCad:
    """Answers each command with the response the test prepared, echoing the request."""

    def __init__(self, failed: bool = False):
        self.failed = failed

    def send(self, command: Any, response_type: type) -> Any:
        response = response_type()
        response.status = base_types_pb2.ItemRequestStatus.IRS_OK
        results = (
            response.created_items
            if isinstance(command, editor_commands_pb2.CreateItems)
            else response.updated_items
        )
        for item in command.items:
            result = results.add()
            if self.failed:
                result.status.code = editor_commands_pb2.ItemStatusCode.ISC_INVALID_TYPE
                result.status.error_message = "rejected"
            else:
                result.status.code = editor_commands_pb2.ItemStatusCode.ISC_OK
                result.item.CopyFrom(item)
        return response


def _editors(kicad: _FakeKiCad) -> list[tuple[Any, Any]]:
    return [
        (Schematic(kicad, DocumentSpecifier()), Junction),  # type: ignore[arg-type]
        (Board(kicad, DocumentSpecifier()), Track),  # type: ignore[arg-type]
    ]


@pytest.mark.parametrize("index", [0, 1])
def test_create_and_update_return_wrapped_items(index: int):
    editor, item_type = _editors(_FakeKiCad())[index]
    item = item_type()

    created = editor.create_items(item)
    updated = editor.update_items(item)

    assert len(created) == 1 and isinstance(created[0], item_type)
    assert len(updated) == 1 and isinstance(updated[0], item_type)
    assert pack_any(created[0].proto) == pack_any(item.proto)


@pytest.mark.parametrize("index", [0, 1])
def test_rejected_item_raises_api_error(index: int):
    editor, item_type = _editors(_FakeKiCad(failed=True))[index]

    with pytest.raises(ApiError, match="rejected"):
        editor.create_items(item_type())
    with pytest.raises(ApiError, match="rejected"):
        editor.update_items(item_type())
