import asyncio
import os
from typing import Literal, Union

import aiofiles
import aiohttp
from tqdm import tqdm

DOWNLOAD_CHUNK_SIZE = 1024

CACHE = {}


async def gather_with_progress(tasks: list, desc: str):
    results = []
    with tqdm(total=len(tasks), desc=desc) as pbar:
        for coro in asyncio.as_completed(tasks):
            try:
                result = await coro
                results.append(result)
            except Exception as e:
                results.append(e)
            pbar.update(1)
    return results


async def download_data(session: aiohttp.ClientSession, url: str, destination: str):
    os.makedirs(os.path.dirname(destination), exist_ok=True)

    async with session.get(url) as response:
        response.raise_for_status()
        async with aiofiles.open(destination, "wb") as out_file:
            async for chunk in response.content.iter_chunked(DOWNLOAD_CHUNK_SIZE):
                if not chunk:
                    continue
                await out_file.write(chunk)


async def get_instance_savings_plan_instance_types(session: aiohttp.ClientSession):
    async with session.get(
        "https://b0.p.awsstatic.com/pricing/2.0/meteredUnitMaps/computesavingsplan/USD/current/instance-savings-plan-ec2/metadata.json"
    ) as response:
        response.raise_for_status()
        instance_types_data = await response.json()

    CACHE["instance_types"] = instance_types_data["valueAttributes"]["InstanceFamily"]

    return instance_types_data["valueAttributes"]["InstanceFamily"]


async def get_locations(session: aiohttp.ClientSession):
    async with session.get(
        "https://b0.p.awsstatic.com/locations/1.0/aws/current/locations.json"
    ) as response:
        response.raise_for_status()
        locations_data = await response.json()

    locations = {}

    for region in locations_data:
        locations[locations_data[region]["code"]] = locations_data[region]["name"]

    CACHE["locations"] = locations

    return locations


async def download_on_demand_data(
    session: aiohttp.ClientSession, region: str, overwrite: bool = False
):
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
):
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
):
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
):
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
):
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


async def main():
    regions = [
        "us-east-1",
        "us-east-2",
        "us-west-1",
        "us-west-2",
        "ca-central-1",
        "ca-west-1",
        "mx-central-1",
        "af-south-1",
        "ap-east-1",
        "ap-east-2",
        "ap-south-1",
        "ap-south-2",
        "ap-southeast-1",
        "ap-southeast-2",
        "ap-southeast-3",
        "ap-southeast-4",
        "ap-southeast-5",
        "ap-southeast-6",
        "ap-southeast-7",
        "ap-northeast-1",
        "ap-northeast-2",
        "ap-northeast-3",
        "eu-central-1",
        "eu-central-2",
        "eu-west-1",
        "eu-west-2",
        "eu-west-3",
        "eu-south-1",
        "eu-north-1",
        "il-central-1",
        "me-central-1",
        "me-south-1",
        "sa-east-1",
    ]
    terms: list[Literal["1 year"] | Literal["3 year"]] = ["1 year", "3 year"]
    payment_options: list[
        Literal["No Upfront"] | Literal["Partial Upfront"] | Literal["All Upfront"]
    ] = ["No Upfront", "Partial Upfront", "All Upfront"]

    async with aiohttp.ClientSession() as session:
        # Pre-fetch locations
        await get_locations(session)

        # Download On-Demand data
        tasks = [
            download_on_demand_data(session=session, region=region)
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
            )
            for region in regions
            for term in terms
            for payment_option in payment_options
        ]
        task_params = [
            (region, term, payment_option)
            for region in regions
            for term in terms
            for payment_option in payment_options
        ]
        results = await gather_with_progress(tasks, desc="Compute Savings Plan")
        for params, result in zip(task_params, results):
            if isinstance(result, Exception):
                region, term, payment_option = params
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
            )
            for region in regions
            for term in terms
            for payment_option in payment_options
        ]
        results = await gather_with_progress(tasks, desc="Standard Reserved Instances")
        for params, result in zip(task_params, results):
            if isinstance(result, Exception):
                region, term, payment_option = params
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
            )
            for region in regions
            for term in terms
            for payment_option in payment_options
        ]
        results = await gather_with_progress(
            tasks, desc="Convertible Reserved Instances"
        )
        for params, result in zip(task_params, results):
            if isinstance(result, Exception):
                region, term, payment_option = params
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
            )
            for region in regions
            for term in terms
            for payment_option in payment_options
            for instance_type in instance_types
        ]
        task_params_instance = [
            (region, term, payment_option, instance_type)
            for region in regions
            for term in terms
            for payment_option in payment_options
            for instance_type in instance_types
        ]
        results = await gather_with_progress(tasks, desc="Instance Savings Plan")
        for params, result in zip(task_params_instance, results):
            if isinstance(result, Exception):
                region, term, payment_option, instance_type = params
                print(
                    f"Failed to download data for region={region} term={term} payment_option={payment_option} instance_type={instance_type}"
                )


if __name__ == "__main__":
    asyncio.run(main())
