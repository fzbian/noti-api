
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from clients.whatsapp import check_number_exists


router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])


class ValidateNumberResponse(BaseModel):
    number: str
    exists: bool
    name: str


@router.get("/validate-number", response_model=ValidateNumberResponse)
def validate_number(
    number: str = Query(
        ..., min_length=10, max_length=10, pattern=r"^\d{10}$",
        description="Número celular colombiano de 10 dígitos (sin prefijo)."
    )
):
    formatted = f"+57{number}"
    try:
        data = check_number_exists(formatted)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e)) from e

    if not data:
        return ValidateNumberResponse(number=number, exists=False, name="No disponible")

    exists = bool(data.get("exists"))
    name = data.get("name") or "No disponible"
    return ValidateNumberResponse(number=number, exists=exists, name=name)
