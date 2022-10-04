from aiogram.types import KeyboardButton, InlineKeyboardButton


class Button:
    def __init__(self, text: str):
        self.text = str(text)

    def inline(self,
               callback_data: str,
               url=None):
        return InlineKeyboardButton(text=self.text,
                                    callback_data=str(callback_data),
                                    url=url)

    def reply(self, request_location=False):
        return KeyboardButton(text=self.text,
                              request_location=request_location)


def get_condition_smile(bool_value):
    return '✅' if bool_value else '☑'


def split_array(arr, n):
    a = []
    for i in range(0, len(arr), n):
        a.append(arr[i:i + n])
    return a


def get_close_button():
    return Button("❌").inline("close")


def get_paging_button(callback, direction="left"):
    return Button('⬅' if direction == "left" else '➡').inline(callback)
