"""Screener endpoints: preset listing, preset execution, and custom screening."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.screener.engine import load_screener_config, run_preset, screen

router = APIRouter(prefix="/screener", tags=["Screener"])


class ScreenFilter(BaseModel):
    metric: str
    operator: str
    value: float | None = None
    threshold: float | None = None
    apply_exception: bool | None = True

    def to_filter_dict(self) -> dict:
        v = self.value if self.value is not None else self.threshold
        return {
            "metric": self.metric,
            "operator": self.operator,
            "value": v,
            "apply_exception": self.apply_exception,
        }


class CustomScreenRequest(BaseModel):
    filters: list[ScreenFilter]
    debug: bool | None = False


@router.get("/presets")
def list_presets():
    """List all available pre-configured screener strategies."""
    cfg = load_screener_config()
    presets_meta = []
    for name, p_data in cfg.get("presets", {}).items():
        presets_meta.append(
            {
                "name": name,
                "description": p_data.get("description", ""),
                "filters": p_data.get("filters", []),
            }
        )
    return {
        "total_presets": len(presets_meta),
        "presets": presets_meta,
    }


@router.get("/presets/{preset_name}")
def execute_preset(preset_name: str, debug: bool = False):
    """Execute a specific preset screener and return matching companies."""
    try:
        result = run_preset(preset_name=preset_name, debug=debug)
        return result
    except (KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/run")
def run_custom_screener(req: CustomScreenRequest):
    """Run a custom multi-metric screener with given filters."""
    try:
        config = load_screener_config()
        filters_dict = [f.to_filter_dict() for f in req.filters]
        result = screen(filters=filters_dict, config=config, debug=req.debug)
        return result
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
