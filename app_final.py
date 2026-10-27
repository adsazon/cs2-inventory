from fastapi import FastAPI, HTTPException, Query, Path, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field, ValidationError
import os, logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("cs2inv")

APP_NAME = os.getenv("APP_NAME", "CS2 Inventory Value")

def _env_float(name: str, default: float, lo: float, hi: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        v = float(raw)
        if not (lo <= v <= hi):
            raise ValueError(f"out of range [{lo}, {hi}]")
        return v
    except Exception as e:
        logger.warning("Invalid %s=%r (%s), using default %s", name, raw, e, default)
        return default

def _env_int(name: str, default: int, lo: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        v = int(raw)
        if v < lo:
            raise ValueError(f"must be >= {lo}")
        return v
    except Exception as e:
        logger.warning("Invalid %s=%r (%s), using default %s", name, raw, e, default)
        return default

DEFAULT_COMMISSION_PCT = _env_float("DEFAULT_COMMISSION_PCT", 15.0, 0.0, 100.0)
MAX_ITEMS = _env_int("MAX_ITEMS", 50, 1)

app = FastAPI(title=APP_NAME)

INVENTORY: dict[str, dict] = {}

ITEM_NAME_PATTERN = r"^[A-Za-z0-9_\-]+$"

class ItemIn(BaseModel):
    price: float = Field(..., gt=0, description="Цена предмета, > 0")
    qty: int = Field(1, ge=1, description="Количество, >= 1")

@app.exception_handler(HTTPException)
async def http_exc_handler(request: Request, exc: HTTPException):
    logger.info("HTTP %s on %s %s: %s",
                exc.status_code, request.method, request.url.path, exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.exception_handler(ValidationError)
async def validation_exc_handler(request: Request, exc: ValidationError):
    logger.warning("Validation error on %s %s: %s",
                   request.method, request.url.path, exc.errors())
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

@app.exception_handler(Exception)
async def unhandled_exc_handler(request: Request, exc: Exception):
    logger.error("Unhandled error on %s %s: %s",
                 request.method, request.url.path, exc, exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

@app.on_event("startup")
def startup():
    logger.info("Service %s started | commission=%.1f%% max_items=%d",
                APP_NAME, DEFAULT_COMMISSION_PCT, MAX_ITEMS)

@app.get("/", include_in_schema=False)
def root():
    return {
        "app": APP_NAME,
        "docs": "/docs",
        "health": "/health",
        "version": "/version",
        "inventory": "/inventory",
    }

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)

@app.get("/health")
def health():
    logger.info("Health check")
    return {"status": "ok"}

@app.get("/version")
def version():
    return {"version": "1.0.0", "app": APP_NAME}

@app.get("/inventory/total")
def inventory_total(
    commission: float | None = Query(None, ge=0, le=100,
                                     description="Комиссия в %, 0–100"),
):
    pct = DEFAULT_COMMISSION_PCT if commission is None else commission
    subtotal = sum(v["price"] * v["qty"] for v in INVENTORY.values())
    total = round(subtotal * (1 + pct / 100), 2)
    logger.info("Total items=%d subtotal=%.2f commission=%.1f%% total=%.2f",
                len(INVENTORY), subtotal, pct, total)
    return {
        "items_count": len(INVENTORY),
        "subtotal": round(subtotal, 2),
        "commission_pct": pct,
        "total": total,
    }

@app.get("/inventory")
def get_inventory():
    logger.info("Get inventory: %d positions", len(INVENTORY))
    return INVENTORY

@app.delete("/inventory/{item_name}")
def delete_item(
    item_name: str = Path(..., min_length=1, max_length=64, pattern=ITEM_NAME_PATTERN),
):
    if item_name not in INVENTORY:
        raise HTTPException(status_code=404, detail="Item not found")
    del INVENTORY[item_name]
    logger.info("Deleted item=%s", item_name)
    return {"deleted": item_name}

@app.post("/inventory/{item_name}", status_code=201)
def add_item(
    item_name: str = Path(..., min_length=1, max_length=64, pattern=ITEM_NAME_PATTERN),
    payload: ItemIn = ...,
):
    if item_name not in INVENTORY and len(INVENTORY) >= MAX_ITEMS:
        raise HTTPException(status_code=400, detail="Inventory limit reached")
    existing = INVENTORY.get(item_name)
    if existing:
        existing["qty"] += payload.qty
        existing["price"] = payload.price
        logger.info("Updated item=%s qty=%d price=%.2f",
                    item_name, existing["qty"], existing["price"])
    else:
        INVENTORY[item_name] = {"price": payload.price, "qty": payload.qty}
        logger.info("Added item=%s qty=%d price=%.2f",
                    item_name, payload.qty, payload.price)
    return {"item": item_name, **INVENTORY[item_name]}