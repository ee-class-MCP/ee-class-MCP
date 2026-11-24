"""HTML parser for NCU ee-class course materials and downloadable attachments.

Maintained by the MCP team.
TODO(mcp-team): Verify CSS selectors against anonymized real ee-class HTML fixtures.
"""

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from eeclass_mcp.models.material import Attachment, MaterialItem


def parse_materials(html: str, base_url: str = "") -> list[MaterialItem]:
    """Parse course materials and attachments from ee-class HTML."""
    soup = BeautifulSoup(html, "lxml")
    materials: list[MaterialItem] = []

    for item in soup.select(".material-item[data-material-id]"):
        material_id = str(item.get("data-material-id", "")).strip()
        title_el = item.select_one(".material-title")
        if not material_id or title_el is None:
            continue

        category_el = item.select_one(".material-category")
        date_el = item.select_one(".material-date")
        href = title_el.get("href")
        full_url = (
            urljoin(base_url, str(href)) if href and base_url else (str(href) if href else None)
        )

        attachments: list[Attachment] = []
        for att_el in item.select("a.attachment-link"):
            att_href = att_el.get("href")
            if not att_href:
                continue
            download_url = urljoin(base_url, str(att_href)) if base_url else str(att_href)
            size_attr = att_el.get("data-file-size")
            attachments.append(
                Attachment(
                    id=str(att_el.get("data-attachment-id"))
                    if att_el.get("data-attachment-id")
                    else None,
                    filename=att_el.get_text(strip=True),
                    download_url=download_url,
                    file_size=str(size_attr) if size_attr else None,
                )
            )

        materials.append(
            MaterialItem(
                id=material_id,
                title=title_el.get_text(strip=True),
                category=category_el.get_text(strip=True) if category_el else None,
                published_at=date_el.get_text(strip=True) if date_el else None,
                url=full_url,
                attachments=attachments,
            )
        )

    return materials
