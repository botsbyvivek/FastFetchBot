import asyncio
import functools
import gc
import os
import uuid

# from xhtml2pdf import pisa
from weasyprint import HTML, CSS
from bs4 import BeautifulSoup
from weasyprint.text.fonts import FontConfiguration

from app.config import DOWNLOAD_DIR
from app.utils.logger import logger

current_directory = os.path.dirname(os.path.abspath(__file__))

PDF_STYLESHEET = os.path.join(current_directory, "pdf_export.css")


class PdfExport:
    def __init__(self, title: str, html_string: str):
        self.title = title
        self.html_string = html_string

    async def export(self) -> str:
        html_string = self.wrap_html_string(self.html_string)
        output_filename = os.path.join(DOWNLOAD_DIR, f"{self.title}-{uuid.uuid4()}.pdf")
        loop = asyncio.get_event_loop()
        css_string = await loop.run_in_executor(None, open, PDF_STYLESHEET, "r")
        css_string = await loop.run_in_executor(None, css_string.read)
        logger.debug(
            f"""
        html_string: {html_string}
        """
        )
        await self.convert_html_to_pdf(
            html_string=html_string,
            css_string=css_string,
            output_filename=output_filename,
        )
        return output_filename
        pass

    @staticmethod
    def wrap_html_string(html_string: str) -> str:
        soup = BeautifulSoup(
            '<html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8">'
            '<meta charset="UTF-8"></head><body></body></html>',
            "html.parser",
        )
        soup.body.append(BeautifulSoup(html_string, "html.parser"))
        for tag in soup.find_all(True):
            if "style" in tag.attrs:
                del tag["style"]
        for style_tag in soup.find_all("style"):
            style_tag.decompose()
        return soup.prettify()

    @staticmethod
    async def convert_html_to_pdf(
        html_string: str, css_string: str, output_filename: str
    ) -> None:
        font_config = FontConfiguration()
        css_item = CSS(string=css_string, font_config=font_config)
        html_item = HTML(string=html_string)
        loop = asyncio.get_event_loop()
        pdf_obj = await loop.run_in_executor(
            None,
            functools.partial(
                html_item.write_pdf, output_filename, stylesheets=[css_item]
            ),
        )
        del font_config
        del css_item
        del html_item
        del pdf_obj
        gc.collect()
