import pytest

from models.orm.booking import BookingModel
from models.orm.city import CityModel
from models.orm.restaurant import RestaurantModel
from models.orm.table import TableModel
from models.orm.user import UserModel


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
