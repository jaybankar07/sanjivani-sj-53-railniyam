"""Tests for rail_refund_calculator agent tool adhering to 2015 rule table."""
from app.tools import rail_refund_calculator


def test_calculator_confirmed_above_48h():
    # 3AC flat charge is Rs 180 per passenger
    res = rail_refund_calculator(fare=1500.0, travel_class="3A", status="confirmed", passengers=1, hours_before_departure=50.0)
    assert res["cancellation_charge"] == 180.0
    assert res["refund_amount"] == 1320.0
    assert "Rule 2(i)" in res["rule_applied"]

    # 1A flat charge is Rs 240 per passenger
    res_1a = rail_refund_calculator(fare=3000.0, travel_class="1A", status="confirmed", passengers=2, hours_before_departure=60.0)
    assert res_1a["cancellation_charge"] == 480.0  # 240 * 2
    assert res_1a["refund_amount"] == 2520.0


def test_calculator_confirmed_slabs():
    # 48h to 12h: 25% of fare (or flat min 120 for Sleeper)
    res_25 = rail_refund_calculator(fare=800.0, travel_class="SL", status="confirmed", passengers=1, hours_before_departure=24.0)
    assert res_25["cancellation_charge"] == 200.0  # 25% of 800
    assert res_25["refund_amount"] == 600.0

    # 12h to 4h: 50% of fare
    res_50 = rail_refund_calculator(fare=1000.0, travel_class="3A", status="confirmed", passengers=1, hours_before_departure=6.0)
    assert res_50["cancellation_charge"] == 500.0  # 50% of 1000
    assert res_50["refund_amount"] == 500.0

    # Less than 4 hours: No refund
    res_late = rail_refund_calculator(fare=1200.0, travel_class="3A", status="confirmed", passengers=1, hours_before_departure=2.0)
    assert res_late["cancellation_charge"] == 1200.0
    assert res_late["refund_amount"] == 0.0


def test_calculator_tatkal_and_rac():
    # Confirmed Tatkal has zero refund
    res_tatkal = rail_refund_calculator(fare=1800.0, travel_class="3A", status="tatkal confirmed", passengers=1, hours_before_departure=30.0)
    assert res_tatkal["refund_amount"] == 0.0
    assert res_tatkal["cancellation_charge"] == 1800.0

    # RAC cancelled >0.5h before departure: clerkage Rs 60
    res_rac = rail_refund_calculator(fare=600.0, travel_class="SL", status="RAC", passengers=2, hours_before_departure=4.0)
    assert res_rac["cancellation_charge"] == 120.0  # 60 * 2
    assert res_rac["refund_amount"] == 480.0

