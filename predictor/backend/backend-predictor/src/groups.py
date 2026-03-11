from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class Company:
    name: str
    ticker: str


GROUP_A = "groupA"
GROUP_B = "groupB"

GROUP_COMPANIES: Dict[str, List[Company]] = {
    GROUP_A: [
        Company("HDFC Bank", "HDFCBANK"),
        Company("ICICI Bank", "ICICIBANK"),
        Company("State Bank of India", "SBIN"),
        Company("Axis Bank", "AXISBANK"),
        Company("Kotak Mahindra Bank", "KOTAKBANK"),
        Company("Bajaj Finance", "BAJFINANCE"),
        Company("Tata Consultancy Services", "TCS"),
        Company("Infosys", "INFY"),
        Company("Bharti Airtel", "BHARTIARTL"),
        Company("Life Insurance Corporation", "LICI"),
    ],
    GROUP_B: [
        Company("Reliance Industries", "RELIANCE"),
        Company("Larsen & Toubro", "LT"),
        Company("NTPC Limited", "NTPC"),
        Company("Adani Enterprises", "ADANIENT"),
        Company("Adani Green Energy", "ADANIGREEN"),
        Company("Hindustan Unilever", "HINDUNILVR"),
        Company("ITC Limited", "ITC"),
        Company("Maruti Suzuki", "MARUTI"),
        Company("Tata Motors", "TATAMOTORS"),
        Company("Sun Pharmaceutical Industries", "SUNPHARMA"),
    ],
}


def list_company_labels() -> List[str]:
    labels: List[str] = []
    for group_key, companies in GROUP_COMPANIES.items():
        group_label = "A" if group_key == GROUP_A else "B"
        for c in companies:
            labels.append(f"{c.name} ({c.ticker}) - Group {group_label}")
    return labels


def find_company_by_label(label: str) -> Optional[Company]:
    for companies in GROUP_COMPANIES.values():
        for company in companies:
            expected = (
                f"{company.name} ({company.ticker}) - Group "
                f"{'A' if find_group_for_ticker(company.ticker) == GROUP_A else 'B'}"
            )
            if expected == label:
                return company
    return None


def find_group_for_ticker(ticker: str) -> Optional[str]:
    t = ticker.upper().strip()
    for group_key, companies in GROUP_COMPANIES.items():
        if any(company.ticker == t for company in companies):
            return group_key
    return None


def get_group_model_filename(group_key: str) -> str:
    if group_key == GROUP_A:
        return "transformer_groupA_multi.keras"
    if group_key == GROUP_B:
        return "transformer_groupB_multi.keras"
    raise ValueError(f"Unknown group key: {group_key}")
