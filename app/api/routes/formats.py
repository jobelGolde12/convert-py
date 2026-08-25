from fastapi import APIRouter

from app.core.conversions_catalog import FORMATS, public_catalog

router = APIRouter()


@router.get("/formats")
def get_formats():
    return {
        "conversions": public_catalog(),
        "formats": [
            {
                "format": f.format,
                "label": f.label,
                "extensions": f.extensions,
                "group": f.group,
            }
            for f in FORMATS
        ],
    }
