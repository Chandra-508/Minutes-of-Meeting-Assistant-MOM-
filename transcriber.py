from faster_whisper import WhisperModel


model = WhisperModel(
    "medium",
    device="cpu",
    compute_type="int8"
)


def transcribe(file_path):

    segments, info = model.transcribe(
        file_path
    )

    text = ""

    for segment in segments:
        text += segment.text + " "

    return text