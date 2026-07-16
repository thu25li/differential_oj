def normalize_output(text:str):
    if not text:
        return ""
    text=text.replace("\r\n","\n").replace("\r","\n")
    lines=[line.rstrip(" \t") for line in text.split("\n")]
    text="\n".join(lines)
    text=text.rstrip("\n")
    if text:
        text=text+"\n"
    return text
def compare_output(actual:str,expected:str):
    return normalize_output(actual)==normalize_output(expected)