# ========= Copyright 2023-2024 @ CAMEL-AI.org. All Rights Reserved. =========
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ========= Copyright 2023-2024 @ CAMEL-AI.org. All Rights Reserved. =========

from camel.loaders import UnstructuredIO
from camel.toolkits.base import BaseToolkit
from camel.toolkits.function_tool import FunctionTool
from camel.toolkits import ImageAnalysisToolkit, ExcelToolkit
from camel.utils import retry_on_error
from camel.logger import get_logger
from camel.models import BaseModelBackend
from chunkr_ai import Chunkr
import requests
import mimetypes
import json
from typing import List, Optional, Tuple, Literal
from urllib.parse import urlparse
import os
import subprocess
import xmltodict
import nest_asyncio
import traceback
import asyncio
from crawl4ai import AsyncWebCrawler

nest_asyncio.apply()

logger = get_logger(__name__)


class DocumentProcessingToolkit(BaseToolkit):
    r"""A class representing a toolkit for processing document and return the content of the document.

    This class provides method for processing docx, pdf, pptx, etc. It cannot process excel files.
    """

    def __init__(
        self, cache_dir: Optional[str] = None, model: Optional[BaseModelBackend] = None
    ):
        self.image_tool = ImageAnalysisToolkit(model=model)
        # self.audio_tool = AudioAnalysisToolkit()
        self.excel_tool = ExcelToolkit()

        self.cache_dir = "tmp/"
        if cache_dir:
            self.cache_dir = cache_dir

        self.uio = UnstructuredIO()

    @retry_on_error()
    def extract_document_content(self, document_path: str) -> Tuple[bool, str]:
        r"""Extract the content of a given document (or url) and return the processed text.
        It may filter out some information, resulting in inaccurate content.

        Args:
            document_path (str): The path of the document to be processed, either a local path or a URL. It can process image, audio files, zip files and webpages, etc.

        Returns:
            Tuple[bool, str]: A tuple containing a boolean indicating whether the document was processed successfully, and the content of the document (if success).
        """

        # Reject remote URLs and paths outside the explicitly configured document root.
        from owl.safe_io import require_local_document
        try:
            document_path = str(require_local_document(document_path))
        except (TypeError, ValueError, PermissionError) as exc:
            return False, str(exc)

        if any(document_path.endswith(ext) for ext in [".jpg", ".jpeg", ".png"]):
            res = self.image_tool.ask_question_about_image(
                document_path, "Please make a detailed caption about the image."
            )
            return True, res

        # if any(document_path.endswith(ext) for ext in ['.mp3', '.wav']):
        #     res = self.audio_tool.ask_question_about_audio(document_path, "Please transcribe the audio content to text.")
        #     return True, res

        if any(document_path.endswith(ext) for ext in ["xls", "xlsx"]):
            res = self.excel_tool.extract_excel_content(document_path)
            return True, res

        if any(document_path.endswith(ext) for ext in ["zip"]):
            extracted_files = self._unzip_file(document_path)
            return True, f"The extracted files are: {extracted_files}"

        if any(document_path.endswith(ext) for ext in ["json", "jsonl", "jsonld"]):
            with open(document_path, "r", encoding="utf-8") as f:
                content = json.load(f)
            f.close()
            return True, content

        if any(document_path.endswith(ext) for ext in ["py"]):
            with open(document_path, "r", encoding="utf-8") as f:
                content = f.read()
            f.close()
            return True, content

        if any(document_path.endswith(ext) for ext in ["xml"]):
            data = None
            with open(document_path, "r", encoding="utf-8") as f:
                content = f.read()
            f.close()

            try:
                data = xmltodict.parse(content)
                logger.debug("Extracted XML document")
                return True, data

            except Exception:
                logger.debug("XML extraction failed; returning raw content")
                return True, content

        if self._is_webpage(document_path):
            try:
                extracted_text = self._extract_webpage_content(document_path)
                return True, extracted_text
            except Exception:
                try:
                    elements = self.uio.parse_file_or_url(document_path)
                    if elements is None:
                        logger.error(f"Failed to parse the document: {document_path}.")
                        return False, f"Failed to parse the document: {document_path}."
                    else:
                        # Convert elements list to string
                        elements_str = "\n".join(str(element) for element in elements)
                        return True, elements_str
                except Exception:
                    return False, "Failed to extract content from the webpage."

        else:
            try:
                elements = self.uio.parse_file_or_url(document_path)
                if elements is None:
                    logger.error(f"Failed to parse the document: {document_path}.")
                    return False, f"Failed to parse the document: {document_path}."
                else:
                    # Convert elements list to string
                    elements_str = "\n".join(str(element) for element in elements)
                    return True, elements_str

            except Exception as e:
                logger.error("Document parsing failed: %s", type(e).__name__)
                return False, "Document parsing failed."

    def _is_webpage(self, url: str) -> bool:
        """Remote URL retrieval is disabled for local document processing."""
        return False

    @retry_on_error()
    async def _extract_content_with_chunkr(
        self,
        document_path: str,
        output_format: Literal["json", "markdown"] = "markdown",
    ) -> str:
        chunkr = Chunkr(api_key=os.getenv("CHUNKR_API_KEY"))

        result = await chunkr.upload(document_path)

        # result = chunkr.upload(document_path)

        if result.status == "Failed":
            logger.error(
                f"Error while processing document {document_path}: {result.message} using Chunkr."
            )
            return f"Error while processing document: {result.message}"

        # extract document name
        document_name = os.path.basename(document_path)
        output_file_path: str

        if output_format == "json":
            output_file_path = f"{document_name}.json"
            result.json(output_file_path)

        elif output_format == "markdown":
            output_file_path = f"{document_name}.md"
            result.markdown(output_file_path)

        else:
            return "Invalid output format."

        with open(output_file_path, "r") as f:
            extracted_text = f.read()
        f.close()
        return extracted_text

    @retry_on_error()
    def _extract_webpage_content(self, url: str) -> str:
        raise PermissionError("Remote document retrieval is disabled.")

    def _get_formatted_time(self) -> str:
        import time

        return time.strftime("%m%d%H%M")

    def _unzip_file(self, zip_path: str) -> List[str]:
        from owl.safe_io import extract_zip_safely
        return extract_zip_safely(zip_path, self.cache_dir)

    def get_tools(self) -> List[FunctionTool]:
        r"""Returns a list of FunctionTool objects representing the functions in the toolkit.

        Returns:
            List[FunctionTool]: A list of FunctionTool objects representing the functions in the toolkit.
        """
        return [
            FunctionTool(self.extract_document_content),
        ]  # Added closing triple quotes here
