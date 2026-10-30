create database railway_db;
use railway_db;

create table trains (
    train_id int primary key,
    train_name varchar(50) not null,
    source varchar(50) not null,
    destination varchar(50) not null,
    departure_time time,
    total_seats int check (total_seats > 0),
    available_seats int check (available_seats >= 0),
    fare decimal(10,2) check (fare > 0)
);

create table passengers (
    passenger_id int primary key,
    passenger_name varchar(50) not null,
    age int check (age > 0),
    gender enum('male','female','others'),
    phone varchar(15)
);

create table bookings (
    booking_id int primary key auto_increment,
    passenger_id int,
    train_id int,
    travel_date date,
    seats_booked int check (seats_booked > 0),
    total_fare decimal(10,2),
    status enum('confirmed','cancelled') default 'confirmed',
    foreign key (passenger_id) references passengers(passenger_id),
    foreign key (train_id) references trains(train_id)
);

insert into trains values
(1, 'godavari express', 'hyderabad', 'visakhapatnam', '17:20:00', 120, 118, 650.00),
(2, 'charminar express', 'hyderabad', 'chennai', '18:30:00', 100, 99, 720.00),
(3, 'rajdhani express', 'hyderabad', 'delhi', '06:00:00', 80, 77, 1800.00),
(4, 'shatabdi express', 'hyderabad', 'bengaluru', '06:10:00', 90, 88, 900.00),
(5, 'konark express', 'hyderabad', 'bhubaneswar', '11:00:00', 110, 106, 780.00),
(6, 'telangana express', 'hyderabad', 'delhi', '06:25:00', 100, 100, 1500.00),
(7, 'venkatadri express', 'hyderabad', 'tirupati', '19:15:00', 120, 118, 550.00),
(8, 'falaknuma express', 'hyderabad', 'howrah', '13:30:00', 100, 99, 1200.00);

insert into passengers values
(1, 'bharath', 21, 'male', '9000000001'),
(2, 'soumith', 24, 'male', '9000000002'),
(3, 'harshith', 22, 'male', '9000000003'),
(4, 'priya', 25, 'female', '9000000004'),
(5, 'gayathri', 29, 'female', '9000000005'),
(6, 'rajshekar', 45, 'male', '9000000006'),
(7, 'aishu', 22, 'female', '9000000007'),
(8, 'venky', 35, 'male', '9000000008'),
(9, 'rahul', 27, 'male', '9000000009'),
(10, 'siddu', 31, 'male', '9000000010');

insert into bookings (passenger_id, train_id, travel_date, seats_booked, total_fare, status) values
(1, 1, '2026-11-05', 2, 1300.00, 'confirmed'),
(2, 2, '2026-11-06', 1, 720.00, 'confirmed'),
(3, 3, '2026-11-07', 3, 5400.00, 'confirmed'),
(4, 4, '2026-11-08', 2, 1800.00, 'confirmed'),
(5, 1, '2026-11-09', 1, 650.00, 'cancelled'),
(6, 5, '2026-11-10', 4, 3120.00, 'confirmed'),
(7, 7, '2026-11-11', 2, 1100.00, 'confirmed'),
(8, 8, '2026-11-12', 1, 1200.00, 'confirmed');