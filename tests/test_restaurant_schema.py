import pytest
from pydantic import ValidationError

from models.schemas.restaurant import RestaurantCreate, RestaurantPatch


@pytest.mark.parametrize("model", [RestaurantCreate, RestaurantPatch])
def test_restaurant_city_id_must_be_positive(model):
    data = {
        "email": "hello@example.com",
        "phone": "+380441234567",
        "name": "Lviv Bistro",
        "description": "Modern Ukrainian cuisine",
        "opens_at": "09:00:00",
        "closes_at": "22:00:00",
        "address": "1 Rynok Square",
        "city_id": -1,
    }
    if model is RestaurantPatch:
        data = {"city_id": -1}

    with pytest.raises(ValidationError):
        model.model_validate(data)


def test_restaurant_create_accepts_positive_city_id():
    assert RestaurantCreate.model_validate(
        {
            "email": "hello@example.com",
            "phone": "+380441234567",
            "name": "Lviv Bistro",
            "description": "Modern Ukrainian cuisine",
            "opens_at": "09:00:00",
            "closes_at": "22:00:00",
            "address": "1 Rynok Square",
            "city_id": 1,
        }
    )
