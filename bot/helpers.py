import  re

# @_**Александр|8** [писал/а](https://zulip.voblake.shop/#narrow/channel/20-.D0.9A.D0.B8.D0.9A-.D1.81.D0.BE.
# D1.84.D1.82-.28.D1.82.D0.B5.D1.81.D1.82.D0.BE.D0.B2.D1.8B.D0.B9.29/topic/.D0.90.D0.BB.D0.B5.D0.BA.D1.81.
# D0.B0.D0.BD.D0.B4.D1.80_542393918/near/945):
# ````quote
# @_**Александр|8** [писал/а](https://zulip.voblake.shop/#narrow/channel/20-.D0.9A.D0.B8.D0.9A-.D1.81.D0.BE.
# D1.84.D1.82-.28.D1.82.D0.B5.D1.81.D1.82.D0.BE.D0.B2.D1.8B.D0.B9.29/topic/.D0.90.D0.BB.D0.B5.D0.BA.D1.81.
# D0.B0.D0.BD.D0.B4.D1.80_542393918/near/898):
# ```quote
# цитируемое сообщ1
# ```
#
# цитируемое сообщ2
# ````
#
# цитируемое сообщ3
# `````
#
# Новое Сообщение


def clean_quote(text: str) -> str:
    #находим последнее вхождение "```quote"
    text_start = text.rfind("```quote")

    # если нету - текст без циирования
    if text_start == -1:
        return text

    # если нашли - оставляем только хвост от этого места (8 - длина строки  "```quote")
    text_start += 8
    text = text[text_start:]

    # отбрасываем 3 или более симвлов [`]
    matches = re.finditer("[^`\n]{3,}", text)

    if not matches:
        return text

    matches = list(matches)
    res = "\n"

    # кроме последнего вхождения - цитаты
    for m in matches[:-1]:
        res += f">{text[m.start() : m.end()].strip()}\n"

    # последнее вхождение - новое сообщение
    res += f"\n{text[matches[-1].start() : matches[-1].end()].strip()}"

    return res


def is_int_string(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def clean_quote2(text: str) -> str:
    # "грязную" цитату превращяем в "Вы писали: цитата..."
    # quote_search = re.search("```quote\n([\w\W]*)```\n([\w\W]*)", text)
    matches = re.finditer("`{3,}", text)
    if matches:
        matches = list(matches)
        length = len(matches)
        last_quote_start = matches[length - 2].end()
        last_quote_end = matches[length - 1].start()
        last_quote = text[last_quote_start:last_quote_end].strip()

        new_text_start = matches[length - 1].end()
        new_text = text[new_text_start:].strip()
        # quote = quote_search.group(1).strip()
        # additiona_text = quote_search.group(2).strip()
        # return f"Вы писали: {quote}\n\n{additiona_text}"
        print(f"Вы писали: {last_quote}\n\n{new_text}")
        return f"Вы писали: {last_quote}\n\n{new_text}"
    return text

