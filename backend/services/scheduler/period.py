from datetime import date


def derive_period_label(frequency: str, ref_date: date | None = None) -> str:
    d = ref_date or date.today()
    if frequency == "weekly":
        year, week, _ = d.isocalendar()
        return f"{year}-W{week:02d}"
    elif frequency == "monthly":
        return d.strftime("%Y-%m")
    else:
        # daily or on_demand
        return d.strftime("%Y-%m-%d")
