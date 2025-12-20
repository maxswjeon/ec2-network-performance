import json
import os

from bs4 import BeautifulSoup


def normalize_cell_text(text: str) -> str:
    return text.replace("✓", "").replace("✗", "").strip()


def prepare_instance_type_data(filename: str):
    with open(f"data/instance-types/{filename}.html", "r", encoding="utf-8") as file:
        html_content = file.read()
    soup = BeautifulSoup(html_content, "html.parser")

    network_spec_div = None
    for h2 in soup.find_all("h2"):
        if "Network specifications" == h2.text:
            network_spec_div = h2.find_next_sibling("div", class_="table-container")
            break

    if network_spec_div is None:
        raise ValueError("Network specifications section not found in the HTML.")

    table = network_spec_div.find("table")
    if table is None:
        raise ValueError("No table found in the Network specifications section.")

    data = {}

    table_head_row = table.find("tr")
    if table_head_row is None:
        raise ValueError("Table has no header row.")

    headers = [th.text.strip() for th in table_head_row.find_all("th")]
    for row in table.find_all("tr")[1:]:
        cells = row.find_all("td")
        if len(cells) != len(headers):
            continue
        for cell in cells:
            for sup in cell.find_all("sup"):
                sup.decompose()
        instance_type = cells[0].text.strip()
        data[instance_type] = {
            headers[i]: normalize_cell_text(cells[i].text.strip())
            for i in range(1, len(headers))
        }

    return data


def normalize_network_performance_table(data: dict) -> dict:
    normalized_data = {}
    for instance_type, specs in data.items():
        normalized_specs = {}
        for key, value in specs.items():
            if "Baseline / Burst bandwidth (Gbps)" == key:
                if "Very Low" == value:
                    normalized_specs["Baseline Bandwidth (Gbps)"] = 0.01
                    normalized_specs["Burst Bandwidth (Gbps)"] = 0.01
                    continue

                if "Low" == value:
                    normalized_specs["Baseline Bandwidth (Gbps)"] = 0.05
                    normalized_specs["Burst Bandwidth (Gbps)"] = 0.05
                    continue

                if "Low to Moderate" == value:
                    normalized_specs["Baseline Bandwidth (Gbps)"] = 0.05
                    normalized_specs["Burst Bandwidth (Gbps)"] = 0.3
                    continue

                if "Moderate" == value:
                    normalized_specs["Baseline Bandwidth (Gbps)"] = 0.3
                    normalized_specs["Burst Bandwidth (Gbps)"] = 0.3
                    continue

                if "High" == value:
                    normalized_specs["Baseline Bandwidth (Gbps)"] = 1
                    normalized_specs["Burst Bandwidth (Gbps)"] = 1
                    continue

                if "/" in value:
                    baseline, burst = value.split("/")
                    normalized_specs["Baseline Bandwidth (Gbps)"] = float(
                        baseline.strip()
                    )
                    normalized_specs["Burst Bandwidth (Gbps)"] = float(burst.strip())
                    continue

                if "Gigabit" in value:
                    value = value.replace("Gigabit", "").strip()

                if "x" in value:
                    parts = value.split("x")
                    factor = float(parts[0].strip())
                    base_value = float(parts[1].strip())
                    normalized_specs["Baseline Bandwidth (Gbps)"] = factor * base_value
                    normalized_specs["Burst Bandwidth (Gbps)"] = factor * base_value
                    continue

                normalized_specs["Baseline Bandwidth (Gbps)"] = float(value.strip())
                normalized_specs["Burst Bandwidth (Gbps)"] = float(value.strip())
            if "ENA" == key:
                normalized_specs["ENA Support"] = value == "Yes"
            if "EFA" == key:
                normalized_specs["EFA Support"] = value == "Yes"
            if "ENA Express" == key:
                normalized_specs["ENA Express Support"] = value == "Yes"
            if "Network cards" == key:
                normalized_specs["Network cards"] = int(value)
            if "Max. network interfaces" == key:
                normalized_specs["Max. network interfaces"] = int(value)
            if "IP addresses per interface" == key:
                normalized_specs["IP addresses per interface"] = int(value)
            if "IPv6" == key:
                normalized_specs["IPv6 Support"] = value == "Yes"
        normalized_data[instance_type] = normalized_specs
    return normalized_data


def prepare_pricing_data(
    prefix: str, filename: str, data: dict[str, dict]
) -> dict[str, dict]:
    if not os.path.exists(f"data/pricing/{filename}"):
        print(f"File data/pricing/{filename} does not exist, skipping...")
        return data

    with open(f"data/pricing/{filename}", "r", encoding="utf-8") as file:
        raw_data = json.load(file)
        location = list(raw_data["regions"].keys())[0]
        for pricing_info in raw_data["regions"][location].values():
            if (
                "Operating System" in pricing_info
                and pricing_info["Operating System"] != "Linux"
            ):
                continue
            if "plc:OS" in pricing_info and pricing_info["plc:OS"] != "Linux":
                continue

            instance_type = None
            if "Instance Type" in pricing_info:
                instance_type = pricing_info["Instance Type"]
            if "ec2:InstanceType" in pricing_info:
                instance_type = pricing_info["ec2:InstanceType"]
            if instance_type is None:
                print("Instance Type not found, skipping...")
                continue

            if instance_type not in data:
                data[instance_type] = {}
            data[instance_type].update({prefix: pricing_info["price"]})
    return data


def prepare_region_pricing_data(region: str):
    data: dict[str, dict] = {}
    data = prepare_pricing_data("On-Demand Price", f"{region}/on-demand.json", data)

    term = ["1yr", "3yr"]
    upfront = ["no", "partial", "all"]
    upfront_full = {
        "no": "No Upfront",
        "partial": "Partial Upfront",
        "all": "All Upfront",
    }
    for t in term:
        for u in upfront:
            data = prepare_pricing_data(
                f"Compute Savings Plan, {t.replace('yr', ' Year')}, {upfront_full[u]}",
                f"{region}/compute-savings-plan/{t}-{u}.json",
                data,
            )

    for t in term:
        for u in upfront:
            for file in os.listdir(
                f"data/pricing/{region}/instance-savings-plan/{t}-{u}"
            ):
                if not file.endswith(".json"):
                    continue
                data = prepare_pricing_data(
                    f"Instance Savings Plan, {t.replace('yr', ' Year')}, {upfront_full[u]}",
                    f"{region}/instance-savings-plan/{t}-{u}/{file}",
                    data,
                )

    for t in term:
        for u in upfront:
            data = prepare_pricing_data(
                f"Standard Reserved Instance, {t.replace('yr', ' Year')}, {upfront_full[u]}",
                f"{region}/standard-reserved-instances/{t}-{u}.json",
                data,
            )

    for t in term:
        for u in upfront:
            data = prepare_pricing_data(
                f"Convertible Reserved Instance, {t.replace('yr', ' Year')}, {upfront_full[u]}",
                f"{region}/convertible-reserved-instances/{t}-{u}.json",
                data,
            )

    return data


if __name__ == "__main__":
    data = {}
    data.update(normalize_network_performance_table(prepare_instance_type_data("gp")))
    data.update(normalize_network_performance_table(prepare_instance_type_data("co")))
    data.update(normalize_network_performance_table(prepare_instance_type_data("mo")))
    data.update(normalize_network_performance_table(prepare_instance_type_data("so")))
    data.update(normalize_network_performance_table(prepare_instance_type_data("ac")))
    data.update(normalize_network_performance_table(prepare_instance_type_data("hpc")))
    data.update(normalize_network_performance_table(prepare_instance_type_data("pg")))

    for region in os.listdir("data/pricing"):
        if not os.path.isdir(f"data/pricing/{region}"):
            continue
        pricing_data = prepare_region_pricing_data(region)
        with open(f"data/pricing/{region}/summary.json", "w", encoding="utf-8") as f:
            json.dump(pricing_data, f, indent=4)

    with open("data/network_performance.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
