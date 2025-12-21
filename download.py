import argparse
import asyncio
import fnmatch
import os
import sys
from typing import Any, Coroutine, Literal, Union

import aiofiles
import aiohttp
from tqdm import tqdm

DOWNLOAD_CHUNK_SIZE = 1024

CACHE: dict[str, Any] = {}


async def gather_with_progress(
    tasks: list[Coroutine[Any, Any, Any]], desc: str
) -> list[Any]:
    results: list[Any] = []
    with tqdm(total=len(tasks), desc=desc) as pbar:
        for coro in asyncio.as_completed(tasks):
            try:
                result = await coro
                results.append(result)
            except Exception as e:
                results.append(e)
            pbar.update(1)
    return results


async def download_data(
    session: aiohttp.ClientSession, url: str, destination: str
) -> None:
    os.makedirs(os.path.dirname(destination), exist_ok=True)

    async with session.get(url) as response:
        response.raise_for_status()
        async with aiofiles.open(destination, "wb") as out_file:
            async for chunk in response.content.iter_chunked(DOWNLOAD_CHUNK_SIZE):
                if not chunk:
                    continue
                await out_file.write(chunk)


async def get_instance_savings_plan_instance_types(
    session: aiohttp.ClientSession,
) -> list[str]:
    async with session.get(
        "https://b0.p.awsstatic.com/pricing/2.0/meteredUnitMaps/computesavingsplan/USD/current/instance-savings-plan-ec2/metadata.json"
    ) as response:
        response.raise_for_status()
        instance_types_data = await response.json()

    CACHE["instance_types"] = instance_types_data["valueAttributes"]["InstanceFamily"]

    return instance_types_data["valueAttributes"]["InstanceFamily"]


async def get_locations(session: aiohttp.ClientSession) -> dict[str, str]:
    async with session.get(
        "https://b0.p.awsstatic.com/locations/1.0/aws/current/locations.json"
    ) as response:
        response.raise_for_status()
        locations_data = await response.json()

    locations: dict[str, str] = {}

    for region in locations_data:
        locations[locations_data[region]["code"]] = locations_data[region]["name"]

    CACHE["locations"] = locations

    return locations


async def download_on_demand_data(
    session: aiohttp.ClientSession, region: str, overwrite: bool = False
) -> None:
    if overwrite is False and os.path.exists(f"data/pricing/{region}/on-demand.json"):
        return

    if "locations" not in CACHE:
        await get_locations(session)

    location = CACHE["locations"][region]

    await download_data(
        session,
        f"https://b0.p.awsstatic.com/pricing/2.0/meteredUnitMaps/ec2/USD/current/ec2-ondemand-without-sec-sel/{location}/Linux/index.json",
        f"data/pricing/{region}/on-demand.json",
    )


async def download_compute_savings_plan_data(
    session: aiohttp.ClientSession,
    region: str,
    term: Union[Literal["1 year"], Literal["3 year"]],
    payment_option: Union[
        Literal["No Upfront"], Literal["Partial Upfront"], Literal["All Upfront"]
    ],
    overwrite: bool = False,
) -> None:
    term_short = "1yr" if term == "1 year" else "3yr"
    payment_option_short = payment_option.split(" ")[0].lower()

    if overwrite is False and os.path.exists(
        f"data/pricing/{region}/compute-savings-plan/{term_short}-{payment_option_short}.json"
    ):
        return

    if "locations" not in CACHE:
        await get_locations(session)

    location = CACHE["locations"][region]

    await download_data(
        session,
        f"https://b0.p.awsstatic.com/pricing/2.0/meteredUnitMaps/computesavingsplan/USD/current/compute-savings-plan-ec2/{term}/{payment_option}/{location}/Linux/Shared/index.json",
        f"data/pricing/{region}/compute-savings-plan/{term_short}-{payment_option_short}.json",
    )


async def download_instance_savings_plan_data(
    session: aiohttp.ClientSession,
    region: str,
    term: Union[Literal["1 year"], Literal["3 year"]],
    payment_option: Union[
        Literal["No Upfront"], Literal["Partial Upfront"], Literal["All Upfront"]
    ],
    instance_type: str,
    overwrite: bool = False,
) -> None:
    term_short = "1yr" if term == "1 year" else "3yr"
    payment_option_short = payment_option.split(" ")[0].lower()

    if overwrite is False and os.path.exists(
        f"data/pricing/{region}/instance-savings-plan/{term_short}-{payment_option_short}/{instance_type}.json"
    ):
        return

    if "locations" not in CACHE:
        await get_locations(session)

    location = CACHE["locations"][region]

    await download_data(
        session,
        f"https://b0.p.awsstatic.com/pricing/2.0/meteredUnitMaps/computesavingsplan/USD/current/instance-savings-plan-ec2/{term}/{payment_option}/{instance_type}/{location}/Linux/Shared/index.json",
        f"data/pricing/{region}/instance-savings-plan/{term_short}-{payment_option_short}/{instance_type}.json",
    )


async def download_standard_reserved_instance_data(
    session: aiohttp.ClientSession,
    region: str,
    term: Union[Literal["1 year"], Literal["3 year"]],
    payment_option: Union[
        Literal["No Upfront"], Literal["Partial Upfront"], Literal["All Upfront"]
    ],
    overwrite: bool = False,
) -> None:
    term_short = "1yr" if term == "1 year" else "3yr"
    payment_option_short = payment_option.split(" ")[0].lower()

    if overwrite is False and os.path.exists(
        f"data/pricing/{region}/standard-reserved-instances/{term_short}-{payment_option_short}.json"
    ):
        return

    if "locations" not in CACHE:
        await get_locations(session)

    location = CACHE["locations"][region]

    await download_data(
        session,
        f"https://b0.p.awsstatic.com/pricing/2.0/meteredUnitMaps/ec2/USD/current/ec2-reservedinstance/{term}/{payment_option}/{location}/Linux/Shared/index.json",
        f"data/pricing/{region}/standard-reserved-instances/{term_short}-{payment_option_short}.json",
    )


async def download_convertible_reserved_instance_data(
    session: aiohttp.ClientSession,
    region: str,
    term: Union[Literal["1 year"], Literal["3 year"]],
    payment_option: Union[
        Literal["No Upfront"], Literal["Partial Upfront"], Literal["All Upfront"]
    ],
    overwrite: bool = False,
) -> None:
    term_short = "1yr" if term == "1 year" else "3yr"
    payment_option_short = payment_option.split(" ")[0].lower()

    if overwrite is False and os.path.exists(
        f"data/pricing/{region}/convertible-reserved-instances/{term_short}-{payment_option_short}.json"
    ):
        return

    if "locations" not in CACHE:
        await get_locations(session)

    location = CACHE["locations"][region]

    await download_data(
        session,
        f"https://b0.p.awsstatic.com/pricing/2.0/meteredUnitMaps/ec2/USD/current/ec2-reservedinstance-convertible/{term}/{payment_option}/{location}/Linux/Shared/index.json",
        f"data/pricing/{region}/convertible-reserved-instances/{term_short}-{payment_option_short}.json",
    )


async def main(
    force: bool = False,
    regions: list[str] | None = None,
    regions_all: bool = False,
    regions_exclude: list[str] | None = None,
) -> None:
    terms: list[Literal["1 year"] | Literal["3 year"]] = ["1 year", "3 year"]
    payment_options: list[
        Literal["No Upfront"] | Literal["Partial Upfront"] | Literal["All Upfront"]
    ] = ["No Upfront", "Partial Upfront", "All Upfront"]

    async with aiohttp.ClientSession() as session:
        # Pre-fetch locations
        locations = await get_locations(session)
        available_regions = list(locations.keys())

        # Helper function to match regions with wildcard support
        def match_patterns(region: str, patterns: list[str]) -> bool:
            return any(fnmatch.fnmatch(region, pattern) for pattern in patterns)

        # Determine which regions to download
        if regions:
            # Match regions using wildcards
            target_regions = [
                r for r in available_regions if match_patterns(r, regions)
            ]
            # Warn about patterns that didn't match anything
            for pattern in regions:
                if not any(fnmatch.fnmatch(r, pattern) for r in available_regions):
                    print(f"Warning: Pattern '{pattern}' did not match any regions")
        elif regions_all:
            target_regions = available_regions
        else:
            # Default: download all regions
            target_regions = available_regions

        # Apply exclusions with wildcard support
        if regions_exclude:
            target_regions = [
                r for r in target_regions if not match_patterns(r, regions_exclude)
            ]

        if not target_regions:
            print("No valid regions to download.")
            return

        regions = target_regions
        print(
            f"Downloading data for {len(regions)} regions: {', '.join(sorted(regions))}"
        )

        # Download On-Demand data
        tasks = [
            download_on_demand_data(session=session, region=region, overwrite=force)
            for region in regions
        ]
        results = await gather_with_progress(tasks, desc="On-Demand")
        for region, result in zip(regions, results):
            if isinstance(result, Exception):
                print(f"Failed to download data for on-demand: region={region}")

        # Download Compute Savings Plan data
        tasks = [
            download_compute_savings_plan_data(
                session=session,
                region=region,
                term=term,
                payment_option=payment_option,
                overwrite=force,
            )
            for region in regions
            for term in terms
            for payment_option in payment_options
        ]
        csp_params = [
            (region, term, payment_option)
            for region in regions
            for term in terms
            for payment_option in payment_options
        ]
        results = await gather_with_progress(tasks, desc="Compute Savings Plan")
        for csp_param, result in zip(csp_params, results):
            if isinstance(result, Exception):
                region, term, payment_option = csp_param
                print(
                    f"Failed to download data for compute savings plan: region={region}, term={term}, payment_option={payment_option}"
                )

        # Download Standard Reserved Instances data
        tasks = [
            download_standard_reserved_instance_data(
                session=session,
                region=region,
                term=term,
                payment_option=payment_option,
                overwrite=force,
            )
            for region in regions
            for term in terms
            for payment_option in payment_options
        ]
        sri_params = [
            (region, term, payment_option)
            for region in regions
            for term in terms
            for payment_option in payment_options
        ]
        results = await gather_with_progress(tasks, desc="Standard Reserved Instances")
        for sri_param, result in zip(sri_params, results):
            if isinstance(result, Exception):
                region, term, payment_option = sri_param
                print(
                    f"Failed to download data for standard reserved instances: region={region}, term={term}, payment_option={payment_option}"
                )

        # Download Convertible Reserved Instances data
        tasks = [
            download_convertible_reserved_instance_data(
                session=session,
                region=region,
                term=term,
                payment_option=payment_option,
                overwrite=force,
            )
            for region in regions
            for term in terms
            for payment_option in payment_options
        ]
        cri_params = [
            (region, term, payment_option)
            for region in regions
            for term in terms
            for payment_option in payment_options
        ]
        results = await gather_with_progress(
            tasks, desc="Convertible Reserved Instances"
        )
        for cri_param, result in zip(cri_params, results):
            if isinstance(result, Exception):
                region, term, payment_option = cri_param
                print(
                    f"Failed to download data for convertible reserved instances: region={region}, term={term}, payment_option={payment_option}"
                )

        # Download Instance Savings Plan data
        instance_types = await get_instance_savings_plan_instance_types(session)

        tasks = [
            download_instance_savings_plan_data(
                session=session,
                region=region,
                term=term,
                payment_option=payment_option,
                instance_type=instance_type,
                overwrite=force,
            )
            for region in regions
            for term in terms
            for payment_option in payment_options
            for instance_type in instance_types
        ]
        isp_params = [
            (region, term, payment_option, instance_type)
            for region in regions
            for term in terms
            for payment_option in payment_options
            for instance_type in instance_types
        ]
        results = await gather_with_progress(tasks, desc="Instance Savings Plan")
        for isp_param, result in zip(isp_params, results):
            if isinstance(result, Exception):
                region, term, payment_option, instance_type = isp_param
                print(
                    f"Failed to download data for region={region} term={term} payment_option={payment_option} instance_type={instance_type}"
                )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download EC2 pricing data")
    parser.add_argument(
        "-f", "--force", action="store_true", help="Force redownload of existing files"
    )
    parser.add_argument(
        "--regions",
        type=str,
        help="Comma-separated list of regions to download. Supports wildcards (e.g., us-*,eu-west-*)",
    )
    parser.add_argument(
        "--regions-all",
        action="store_true",
        help="Download data for all available regions",
    )
    parser.add_argument(
        "--regions-exclude",
        type=str,
        help="Comma-separated list of regions to exclude. Supports wildcards (e.g., us-gov-*). Requires --regions or --regions-all",
    )
    args = parser.parse_args()

    # Validate --regions-exclude requires --regions or --regions-all
    if args.regions_exclude and not args.regions and not args.regions_all:
        parser.error("--regions-exclude requires --regions or --regions-all")
        sys.exit(1)

    # Parse comma-separated regions
    regions = [r.strip() for r in args.regions.split(",")] if args.regions else None
    regions_exclude = (
        [r.strip() for r in args.regions_exclude.split(",")]
        if args.regions_exclude
        else None
    )

    asyncio.run(
        main(
            force=args.force,
            regions=regions,
            regions_all=args.regions_all,
            regions_exclude=regions_exclude,
        )
    )
