import pytest

from models.db.booking import BookingModel
from models.db.city import CityModel
from models.db.restaurant import RestaurantModel
from models.db.table import TableModel
from models.db.user import UserModel


@pytest.mark.parametrize(
    "model, expected_columns",
    [
        (CityModel, ("name", "country_code", "id")),
        (RestaurantModel, ("name", "id")),
        (UserModel, ("last_name", "first_name", "id")),
        (TableModel, ("number", "id")),
        (BookingModel, ("booking_date", "start_time", "id")),
    ],
)
def test_order_by_returns_model_default_ordering(model, expected_columns):
    ordering = model.order_by()

    assert tuple(expression.element.name for expression in ordering) == expected_columns
    assert all(expression.modifier.__name__ == "asc_op" for expression in ordering)
