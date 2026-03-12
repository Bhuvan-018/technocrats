from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class Company:
    name: str
    ticker: str


SECTOR_BANKING = "banking"
SECTOR_ENERGY = "energy"
SECTOR_IT = "it"

SECTOR_COMPANIES: Dict[str, List[Company]] = {
    SECTOR_BANKING: [
        Company("HDFC Bank", "HDFCBANK"),
        Company("ICICI Bank", "ICICIBANK"),
        Company("State Bank of India", "SBIN"),
        Company("Kotak Mahindra Bank", "KOTAKBANK"),
        Company("Axis Bank", "AXISBANK"),
        Company("IndusInd Bank", "INDUSINDBK"),
        Company("Punjab National Bank", "PNB"),
        Company("Bank of Baroda", "BANKBARODA"),
        Company("Bajaj Finance", "BAJFINANCE"),
        Company("Bajaj Finserv", "BAJAJFINSV"),
        Company("LIC India", "LICI"),
        Company("IDFC First Bank", "IDFCFIRSTB"),
    ],
    SECTOR_ENERGY: [
        Company("NTPC", "NTPC"),
        Company("Tata Power", "TATAPOWER"),
        Company("Adani Green Energy", "ADANIGREEN"),
        Company("Adani Energy Solutions", "ADANIENSOL"),
        Company("Power Grid Corporation", "POWERGRID"),
        Company("JSW Energy", "JSWENERGY"),
        Company("NHPC", "NHPC"),
        Company("SJVN", "SJVN"),
        Company("GAIL", "GAIL"),
        Company("Indian Oil Corporation", "IOC"),
        Company("Bharat Petroleum", "BPCL"),
    ],
    SECTOR_IT: [
        Company("Infosys", "INFY"),
        Company("Tata Consultancy Services", "TCS"),
        Company("Wipro", "WIPRO"),
        Company("HCL Technologies", "HCLTECH"),
        Company("Tech Mahindra", "TECHM"),
        Company("LTIMindtree", "LTIM"),
        Company("Coforge", "COFORGE"),
        Company("Persistent Systems", "PERSISTENT"),
        Company("Mphasis", "MPHASIS"),
        Company("Oracle Financial Services", "OFSS"),
        Company("Birlasoft", "BSOFT"),
        Company("Cyient", "CYIENT"),
    ],
}


def get_sector_model_filename(sector_key: str) -> str:
    if sector_key not in SECTOR_COMPANIES:
        raise ValueError(f"Unknown sector key: {sector_key}")
    return f"transformer_{sector_key}_multi.keras"


def find_sector_for_ticker(ticker: str) -> Optional[str]:
    t = ticker.upper().strip()
    for sector_key, companies in SECTOR_COMPANIES.items():
        if any(company.ticker == t for company in companies):
            return sector_key
    return None


def list_sector_company_labels() -> List[str]:
    labels: List[str] = []
    for sector_key, companies in SECTOR_COMPANIES.items():
        for company in companies:
            labels.append(f"{company.name} ({company.ticker}) - Sector {sector_key.upper()}")
    return labels


def find_sector_company_by_label(label: str) -> Optional[Company]:
    for sector_key, companies in SECTOR_COMPANIES.items():
        for company in companies:
            expected = f"{company.name} ({company.ticker}) - Sector {sector_key.upper()}"
            if expected == label:
                return company
    return None
