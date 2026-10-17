"""Company annual reports and regulatory documents endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.api.db import query_all, query_one

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("/{ticker}")
def get_company_documents(ticker: str):
    """Retrieve annual reports, filings, and regulatory document links for a company."""
    company = query_one(
        "SELECT company_id, ticker, company_name FROM companies WHERE UPPER(ticker) = UPPER(?) OR company_id = ?",
        (ticker, ticker),
    )
    if not company:
        raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found.")

    cid = company["company_id"]
    docs = query_all(
        """
        SELECT document_id, document_type, document_url, document_date
        FROM documents
        WHERE company_id = ?
        ORDER BY document_date DESC
        """,
        (cid,),
    )
    return {
        "ticker": company["ticker"],
        "company_name": company["company_name"],
        "total_documents": len(docs),
        "documents": docs,
    }
