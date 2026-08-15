import os
import shutil
import tempfile

# Flask-SQLAlchemy binds its engine when db.init_app(app) runs at import time,
# so DATABASE_URL must be set BEFORE `app` is imported below — changing
# app.config['SQLALCHEMY_DATABASE_URI'] afterwards would silently no-op and
# tests would run against the real dev rental.db.
_TEST_DB_DIR = tempfile.mkdtemp(prefix="rental_test_")
os.environ['DATABASE_URL'] = f"sqlite:///{os.path.join(_TEST_DB_DIR, 'test.db')}"

import pytest
from datetime import date, timedelta

from app import app as flask_app, db, User, Property, Booking
from werkzeug.security import generate_password_hash


@pytest.fixture(scope="module")
def test_client():
    flask_app.config['TESTING'] = True

    with flask_app.app_context():
        db.create_all()

        owner = User(username='owner1', email='owner@test.com',
                     password_hash=generate_password_hash('ownerpass'), user_type='owner')
        renter = User(username='renter1', email='renter@test.com',
                      password_hash=generate_password_hash('renterpass'), user_type='renter')
        db.session.add_all([owner, renter])
        db.session.commit()

        prop = Property(owner_id=owner.user_id, title='Test Place', city='TestCity',
                         price_per_night=100.0, num_bedrooms=2)
        db.session.add(prop)
        db.session.commit()

        yield flask_app.test_client(), owner.user_id, renter.user_id, prop.property_id

        db.session.remove()
        db.drop_all()

    shutil.rmtree(_TEST_DB_DIR, ignore_errors=True)


def login(client, email, password):
    return client.post('/login', data={'email': email, 'password': password}, follow_redirects=True)


def test_owner_only_route_blocks_renter(test_client):
    client, owner_id, renter_id, prop_id = test_client
    with client.session_transaction() as sess:
        sess['user_id'] = renter_id
        sess['user_type'] = 'renter'

    response = client.get('/add_property', follow_redirects=False)
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/')


def test_login_rejects_wrong_password(test_client):
    client, *_ = test_client
    response = login(client, 'owner@test.com', 'wrongpassword')
    assert b'Invalid email or password' in response.data


def test_login_accepts_correct_password(test_client):
    client, *_ = test_client
    login(client, 'owner@test.com', 'ownerpass')
    with client.session_transaction() as sess:
        assert sess['user_type'] == 'owner'


def test_booking_price_calculation(test_client):
    client, owner_id, renter_id, prop_id = test_client
    with client.session_transaction() as sess:
        sess['user_id'] = renter_id
        sess['user_type'] = 'renter'

    start = date.today() + timedelta(days=10)
    end = start + timedelta(days=4)  # 4 nights
    client.post(f'/book/{prop_id}', data={
        'start_date': start.isoformat(), 'end_date': end.isoformat()
    }, follow_redirects=True)

    with flask_app.app_context():
        booking = Booking.query.filter_by(
            renter_id=renter_id, property_id=prop_id, start_date=start.isoformat()
        ).first()
        assert booking is not None
        assert booking.total_price == 4 * 100.0


def test_double_booking_is_rejected(test_client):
    client, owner_id, renter_id, prop_id = test_client
    with client.session_transaction() as sess:
        sess['user_id'] = renter_id
        sess['user_type'] = 'renter'

    start = date.today() + timedelta(days=30)
    end = start + timedelta(days=3)
    client.post(f'/book/{prop_id}', data={
        'start_date': start.isoformat(), 'end_date': end.isoformat()
    }, follow_redirects=True)

    overlap_start = start + timedelta(days=1)
    overlap_end = overlap_start + timedelta(days=3)
    response = client.post(f'/book/{prop_id}', data={
        'start_date': overlap_start.isoformat(), 'end_date': overlap_end.isoformat()
    }, follow_redirects=True)
    assert b'already booked' in response.data

    with flask_app.app_context():
        count = Booking.query.filter_by(
            property_id=prop_id, start_date=overlap_start.isoformat()
        ).count()
        assert count == 0


def test_revenue_aggregation(test_client):
    client, owner_id, renter_id, prop_id = test_client

    with flask_app.app_context():
        before = db.session.query(db.func.sum(Booking.total_price)) \
            .join(Property).filter(Property.owner_id == owner_id).scalar() or 0.0

        new_prop = Property(owner_id=owner_id, title='Revenue Test Place',
                             city='TestCity', price_per_night=50.0, num_bedrooms=1)
        db.session.add(new_prop)
        db.session.commit()

        booking = Booking(renter_id=renter_id, property_id=new_prop.property_id,
                           start_date='2030-01-01', end_date='2030-01-06', total_price=250.0)
        db.session.add(booking)
        db.session.commit()

    with client.session_transaction() as sess:
        sess['user_id'] = owner_id
        sess['user_type'] = 'owner'
        sess['username'] = 'owner1'

    response = client.get('/dashboard')
    assert response.status_code == 200

    expected_total = before + 250.0
    assert f"{expected_total:,.2f}".encode() in response.data
    # Confirms the GROUP BY breakdown rendered a row for the newly booked property
    assert b'Revenue Test Place' in response.data
