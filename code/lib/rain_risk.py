import asyncio

from .conductivity import get_conductivity_response
from .data_retrieval import get_basement_response, get_satelite_img
from .fastning import get_fastning_response
from .hollowings import get_hollowing_response


# Async wrappers
async def get_satelite_img_async(coordinates):
    return get_satelite_img(coordinates)


async def get_basement_response_async(address_id):
    return get_basement_response(address_id)


async def get_fastning_response_async(coordinates, sat_img):
    return get_fastning_response(coordinates, sateliteImage=sat_img)


async def get_hollowing_response_async(coordinates, sat_img):
    return get_hollowing_response(coordinates, sateliteImage=sat_img)


async def get_conductivity_response_async(coordinates):
    return get_conductivity_response(coordinates)


async def get_factors_async(address_id, coordinates):
    sat_image = get_satelite_img_async(coordinates)
    basement = get_basement_response_async(address_id)
    conductivity = get_conductivity_response_async(coordinates)
    sat_image = await sat_image
    fastning = get_fastning_response_async(coordinates, sat_image)
    hollowing = get_hollowing_response_async(coordinates, sat_image)
    return [
        await basement,
        await fastning,
        await hollowing,
        await conductivity,
    ]


def get_rain_risk_response(address_id, coordinates):
    results = asyncio.run(get_factors_async(address_id, coordinates))
    factors = {
        "basement": results[0],
        "fastning": results[1],
        "hollowing": results[2],
        "conductivity": results[3],
    }
    return {"factors": factors, "risk": determine_rain_risk(factors)}


def determine_rain_risk(factors):
    """These rules were determined by the subject experts at Bolius. The
    relationship between the factors is complex and sadly requires a bunch of
    if statements."""
    # Helper functions
    is_low = lambda factor: factors[factor]["risk"] == "low"  # noqa: E731
    is_high = lambda factor: factors[factor]["risk"] == "high"  # noqa: E731

    if is_low("basement") and is_low("hollowing"):
        if not (is_high("conductivity") or is_high("fastning")):
            return "low"
        else:
            return "medium"
    elif is_high("basement") and is_high("hollowing"):
        return "high"
    elif is_high("basement"):
        return "medium"
    elif is_high("hollowing"):
        if is_low("conductivity") and is_low("fastning"):
            return "medium"
        else:
            return "high"
