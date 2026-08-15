-- Drops tables if they already exist, so we can re-run this file
DROP TABLE IF EXISTS Users;
DROP TABLE IF EXISTS Properties;
DROP TABLE IF EXISTS Bookings;

-- Users Table
CREATE TABLE Users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    user_type TEXT NOT NULL DEFAULT 'renter' -- 'renter' or 'owner'
);

-- Properties Table
CREATE TABLE Properties (
    property_id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    address TEXT,
    city TEXT NOT NULL,
    price_per_night REAL NOT NULL,
    num_bedrooms INTEGER,
    image_url TEXT, -- NEW COLUMN
    FOREIGN KEY (owner_id) REFERENCES Users (user_id)
);

-- Bookings Table
CREATE TABLE Bookings (
    booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
    renter_id INTEGER NOT NULL,
    property_id INTEGER NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    total_price REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'confirmed', -- 'confirmed', 'cancelled'
    FOREIGN KEY (renter_id) REFERENCES Users (user_id),
    FOREIGN KEY (property_id) REFERENCES Properties (property_id)
);

-- Insert sample data to test with
INSERT INTO Users (username, email, password_hash, user_type) VALUES
('eiden_owner', 'eiden@owner.com', 'scrypt:32768:8:1$4ATQEevNU1enyFSA$93f191e3eedbc2a881008c663e1ac57d3c5705f7d28c0b17358118ec4e879b51d634d18c5a2a91699c853ca749152323a525078d6a510f4b6608ce6672fd7d03', 'owner'),
('test_renter', 'renter@test.com', 'scrypt:32768:8:1$42gIkgOwWyeHx6hR$37bd9d388b4e77ef5a659d1b49a23c314a05af61338df8776655ac98f65df9abdcf9fde65731fd79ddf1a736d1686d1622bc0393d52c451590d764b9cfba7d2d', 'renter');

INSERT INTO Properties (owner_id, title, city, price_per_night, num_bedrooms, image_url) VALUES
(1, 'Cozy Apartment in Munich', 'Munich', 120.50, 1, 'https://images.unsplash.com/photo-1513694203232-719a280e022f?w=400'), 
(1, 'Spacious Loft in Berlin', 'Berlin', 200.00, 3, 'https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=400'),
(1, 'Modern Studio in Hamburg', 'Hamburg', 95.00, 1, 'https://images.unsplash.com/photo-1522771739844-6a9f6d5f14af?w=400'), 
(1, 'Sunny 2-Bedroom in Munich', 'Munich', 180.00, 2, 'https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=400'),
(1, 'Historic Flat in Berlin', 'Berlin', 210.00, 2, 'https://images.unsplash.com/photo-1540518614846-7eded433c457?w=400'),
(1, 'Rooftop Penthouse in Hamburg', 'Hamburg', 350.00, 3, 'https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=400'),
(1, 'Quiet Room near English Garden', 'Munich', 85.00, 1, 'https://images.unsplash.com/photo-1497366811353-6870744d04b2?w=400'), 
(1, 'Artistic Loft in Cologne', 'Cologne', 160.00, 2, 'https://images.unsplash.com/photo-1493809842364-78817add7ffb?w=400');