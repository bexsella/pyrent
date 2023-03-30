"""
This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or
distribute this software, either in source code form or as a compiled
binary, for any purpose, commercial or non-commercial, and by any
means.

In jurisdictions that recognize copyright laws, the author or authors
of this software dedicate any and all copyright interest in the
software to the public domain. We make this dedication for the benefit
of the public at large and to the detriment of our heirs and
successors. We intend this dedication to be an overt act of
relinquishment in perpetuity of all present and future rights to this
software under copyright law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

For more information, please refer to <http://unlicense.org/>

References: http://bittorrent.org/beps/bep_0003.html\
"""

from enum import Enum

BencodeType = dict[str, int | str | list] | list | int | str

class BencodeState(Enum):
  READ_NEXT = 0
  READ_DICT = 1
  READ_ARRAY = 2
  READ_INT = 3
  READ_STRING = 4
  READ_END = 5

class Bencode:
  def __init__(self):
    self.state: BencodeState = BencodeState.READ_NEXT
    self.previous_states: list[BencodeState] = []
    self.active_list: list[BencodeType] = []
    self.start_pos: int = 0
    self.string_len: int = -1
    self.type_actions: dict[str, callable] = {
      'e': lambda _, __: self._next_state(BencodeState.READ_END),
      'd': lambda _, __: self._next_state(BencodeState.READ_DICT),
      'i': lambda _, __: self._next_state(BencodeState.READ_INT),
      'l': lambda _, __: self._next_state(BencodeState.READ_ARRAY)
    }

  def _pop_state(self):
    self.state = self.previous_states.pop()

  def _next_state(self, next_state: BencodeState):
    # there should not be a change in state if we are in the middle of reading a string.
    if self.state == BencodeState.READ_STRING:
      return

    self.previous_states.append(self.state)
    self.state = next_state

  def _default_type_action(self, ch: str, index: int):
    if ch.isnumeric() and self.state != BencodeState.READ_INT and self.state != BencodeState.READ_STRING:
        self.start_pos = index
        self._next_state(BencodeState.READ_STRING)

  def _next_item(self, input: str, ch: str, index: int):
    action = self.type_actions.get(ch, self._default_type_action)
    action(ch, index)

  def _check_active_state(self, input: str, index: int):
    # if these sections are done, finish them, and add them to the object.
    match self.state:
      case BencodeState.READ_STRING:
        if self.string_len > 0 and index - self.start_pos == self.string_len:
            current_obj = input[self.start_pos:index]
            print(current_obj)
            self._pop_state()

            # ensure to reset string length
            self.string_len = -1 

      case BencodeState.READ_END:
        # this is marked as end, so check what we're ending and process accordingly
        self._pop_state()

        if self.state == BencodeState.READ_INT:
          print(input[self.start_pos:index-1])
          self.string_len = -1

        self._pop_state()

  def decode(self, input: str):
    for index, ch in enumerate(input):
      self._check_active_state(input, index)
      self._next_item(input, ch, index)

      match self.state:
        case BencodeState.READ_INT:
          if self.string_len < 0:
            self.string_len = 1
            self.start_pos = index + 1

        case BencodeState.READ_STRING:
          if ch == ':' and self.string_len < 0:
            print('"' + input[self.start_pos:index] + '"')
            self.string_len = int(input[self.start_pos:index])
            self.start_pos = index + 1
          
def test():
  test = Bencode()
  test.decode("d8:announce35:https://torrent.ubuntu.com/announce13:announce-listll35:https://torrent.ubuntu.com/announceel40:https://ipv6.torrent.ubuntu.com/announceee7:comment29:Ubuntu CD releases.ubuntu.com10:created by13:mktorrent 1.113:creation datei1677175131e4:infod6:lengthi4927586304e4:name32:ubuntu-22.04.2-desktop-amd64.iso12:piece lengthi262144eee")

test()
