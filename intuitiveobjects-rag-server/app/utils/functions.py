from app.core.config import settings
import re


def inject_image_markdown(text: str, base_url: str = settings.IMAGE_URL) -> str:
    text_with_images = re.sub(
        # r"- (_page_\d+_[\w\d]+\.jpe?g)",
        r"- (_page_\d+_[\w\d]+\.jpe?g)(?: \(\d+x\d+\))?",
        lambda m: f"- ![Image]({base_url}/{m.group(1)})",
        # convert_links_to_anchors(text)
        text,
    )
    return text_with_images
