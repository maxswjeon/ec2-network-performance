import csv
import json
import os

field_names = [
    "Instance Type",
    "On-Demand Price",
    "Compute Savings Plan, 1 Year, No Upfront",
    "Compute Savings Plan, 1 Year, Partial Upfront",
    "Compute Savings Plan, 1 Year, All Upfront",
    "Compute Savings Plan, 3 Year, No Upfront",
    "Compute Savings Plan, 3 Year, Partial Upfront",
    "Compute Savings Plan, 3 Year, All Upfront",
    "Instance Savings Plan, 1 Year, No Upfront",
    "Instance Savings Plan, 1 Year, Partial Upfront",
    "Instance Savings Plan, 1 Year, All Upfront",
    "Instance Savings Plan, 3 Year, No Upfront",
    "Instance Savings Plan, 3 Year, Partial Upfront",
    "Instance Savings Plan, 3 Year, All Upfront",
    "Standard Reserved Instance, 1 Year, No Upfront",
    "Standard Reserved Instance, 1 Year, Partial Upfront",
    "Standard Reserved Instance, 1 Year, All Upfront",
    "Standard Reserved Instance, 3 Year, No Upfront",
    "Standard Reserved Instance, 3 Year, Partial Upfront",
    "Standard Reserved Instance, 3 Year, All Upfront",
    "Convertible Reserved Instance, 1 Year, No Upfront",
    "Convertible Reserved Instance, 1 Year, Partial Upfront",
    "Convertible Reserved Instance, 1 Year, All Upfront",
    "Convertible Reserved Instance, 3 Year, No Upfront",
    "Convertible Reserved Instance, 3 Year, Partial Upfront",
    "Convertible Reserved Instance, 3 Year, All Upfront",
    "Baseline Bandwidth (Gbps)",
    "Burst Bandwidth (Gbps)",
    "Network cards",
    "Max. network interfaces",
    "IP addresses per interface",
    "IPv6 Support",
    "ENA Support",
    "EFA Support",
    "ENA Express Support",
]


def merge_data(network_data: dict, pricing_data: dict) -> list[dict]:
    merged_data = []
    for instance_type, specs in network_data.items():
        row = {"Instance Type": instance_type}
        if instance_type not in pricing_data:
            continue
        row.update(pricing_data[instance_type])
        row.update(specs)
        merged_data.append(row)
    return merged_data


def export_data(network_data: dict[str, dict], region: str):
    with open(f"data/pricing/{region}/summary.json", "r", encoding="utf-8") as f:
        pricing_data = json.load(f)

    with open(f"data/pricing/{region}/data.csv", "w", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=field_names)
        writer.writeheader()
        writer.writerows(merge_data(network_data, pricing_data))


if __name__ == "__main__":
    with open("data/network_performance.json", "r", encoding="utf-8") as f:
        network_data = json.load(f)

    for region in os.listdir("data/pricing"):
        if not os.path.isdir(f"data/pricing/{region}"):
            continue
        export_data(network_data, region)
