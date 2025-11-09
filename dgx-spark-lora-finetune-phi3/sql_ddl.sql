

CREATE TABLE buyers (
    cid SERIAL PRIMARY KEY,
    FNAME VARCHAR(100) NOT NULL,
    SURNAME VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    TELEPHONE VARCHAR(25),
    modify_date TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE order_header (
    oid SERIAL PRIMARY KEY,
    cid INTEGER NOT NULL,
    oe_number VARCHAR(50) NOT NULL UNIQUE,
    order_entry_date DATE NOT NULL DEFAULT CURRENT_DATE,
    order_status VARCHAR(50) NOT NULL DEFAULT 'pending',
    order_total_amount NUMERIC(12, 2) NOT NULL DEFAULT 0,
    modify_date TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_order_header_customer
        FOREIGN KEY (cid) REFERENCES buyers(cid)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

CREATE TABLE order_detail (
    order_detail_id SERIAL PRIMARY KEY,
    oid INTEGER NOT NULL,
    line_number INTEGER NOT NULL,
    catalog_sku VARCHAR(100) NOT NULL,
    description TEXT,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0),
    line_item_total_amount NUMERIC(12, 2) GENERATED ALWAYS AS (quantity * unit_price) STORED,
    modify_date TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_order_detail_order
        FOREIGN KEY (oid) REFERENCES order_header(oid)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT uq_order_detail_line UNIQUE (oid, line_number)
);

