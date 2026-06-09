"""
pdf_generator.py - Convert HTML reports to PDF using WeasyPrint.
Falls back gracefully if WeasyPrint is not installed.
"""

from app.utils.logger import get_logger

logger = get_logger(__name__)


def generate_pdf(html_content: str, output_path: str) -> bool:
    """
    Convert HTML content to PDF.
    
    Uses WeasyPrint if available, otherwise skips PDF generation.
    Returns True if PDF was generated successfully.
    """
    try:
        from weasyprint import HTML

        logger.info(f"Generating PDF: {output_path}")
        HTML(string=html_content).write_pdf(output_path)
        logger.info(f"PDF generated successfully: {output_path}")
        return True

    except ImportError:
        logger.warning(
            "WeasyPrint not installed. PDF generation skipped. "
            "Install with: pip install weasyprint"
        )
        return False

    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        return False
