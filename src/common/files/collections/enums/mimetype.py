import enum


class Mimetype(enum.StrEnum):
    png = "image/png"
    jpeg = "image/jpeg"
    jpg = "image/jpeg"
    gif = "image/gif"
    bmp = "image/bmp"
    webp = "image/webp"
    svg = "image/svg+xml"
    tiff = "image/tiff"

    mp4 = "video/mp4"
    webm = "video/webm"
    avi = "video/x-msvideo"
    mov = "video/quicktime"
    mpeg = "video/mpeg"
    mkv = "video/x-matroska"

    mp3 = "audio/mpeg"
    wav = "audio/wav"
    ogg = "audio/ogg"
    flac = "audio/flac"
    aac = "audio/aac"

    txt = "text/plain"
    csv = "text/csv"
    html = "text/html"
    css = "text/css"
    js = "application/javascript"
    json = "application/json"
    xml = "application/xml"

    pdf = "application/pdf"
    doc = "application/msword"
    docx = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    xls = "application/vnd.ms-excel"
    xlsx = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ppt = "application/vnd.ms-powerpoint"
    pptx = "application/vnd.openxmlformats-officedocument.presentationml.presentation"

    @property
    def extension(self) -> str:
        mapping: dict[Mimetype, str] = {
            Mimetype.png: ".png",
            Mimetype.jpeg: ".jpeg",
            Mimetype.jpg: ".jpg",
            Mimetype.gif: ".gif",
            Mimetype.bmp: ".bmp",
            Mimetype.webp: ".webp",
            Mimetype.svg: ".svg",
            Mimetype.tiff: ".tiff",
            Mimetype.mp4: ".mp4",
            Mimetype.webm: ".webm",
            Mimetype.avi: ".avi",
            Mimetype.mov: ".mov",
            Mimetype.mpeg: ".mpeg",
            Mimetype.mkv: ".mkv",
            Mimetype.mp3: ".mp3",
            Mimetype.wav: ".wav",
            Mimetype.ogg: ".ogg",
            Mimetype.flac: ".flac",
            Mimetype.aac: ".aac",
            Mimetype.txt: ".txt",
            Mimetype.csv: ".csv",
            Mimetype.html: ".html",
            Mimetype.css: ".css",
            Mimetype.js: ".js",
            Mimetype.json: ".json",
            Mimetype.xml: ".xml",
            Mimetype.pdf: ".pdf",
            Mimetype.doc: ".doc",
            Mimetype.docx: ".docx",
            Mimetype.xls: ".xls",
            Mimetype.xlsx: ".xlsx",
            Mimetype.ppt: ".ppt",
            Mimetype.pptx: ".pptx",
        }
        return mapping[self]

    @classmethod
    def image(cls) -> list["Mimetype"]:
        return [
            cls.png,
            cls.jpeg,
            cls.jpg,
            cls.gif,
            cls.bmp,
            cls.webp,
            cls.svg,
            cls.tiff,
        ]

    @classmethod
    def video(cls) -> list["Mimetype"]:
        return [
            cls.mp4,
            cls.webm,
            cls.avi,
            cls.mov,
            cls.mpeg,
            cls.mkv,
        ]

    @classmethod
    def audio(cls) -> list["Mimetype"]:
        return [
            cls.mp3,
            cls.wav,
            cls.ogg,
            cls.flac,
            cls.aac,
        ]

    @classmethod
    def document(cls) -> list["Mimetype"]:
        return [
            cls.txt,
            cls.csv,
            cls.html,
            cls.css,
            cls.js,
            cls.json,
            cls.xml,
            cls.pdf,
            cls.doc,
            cls.docx,
            cls.xls,
            cls.xlsx,
            cls.ppt,
            cls.pptx,
        ]
