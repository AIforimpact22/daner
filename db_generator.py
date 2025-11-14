import sqlite3

def create_database(db_name="store.db"):
    # Connect to SQLite (this will create the file if it doesn't exist)
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Enable foreign key support
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Drop tables if they exist (optional; remove if you don't want this behavior)
    cursor.execute("DROP TABLE IF EXISTS Sale;")
    cursor.execute("DROP TABLE IF EXISTS Store;")

    # Create the Store table
    cursor.execute("""
        CREATE TABLE Store (
            StockNo TEXT PRIMARY KEY,
            Make TEXT,
            Model TEXT,
            Year INTEGER,
            Trim TEXT,
            BodyStyle TEXT,
            Transmission TEXT,
            Fuel TEXT,
            Engine TEXT,
            Drivetrain TEXT,
            Mileage INTEGER,
            ExteriorColor TEXT,
            InteriorColor TEXT,
            VIN TEXT,
            Price REAL,
            Condition TEXT,
            Features TEXT,
            Location TEXT,
            Photo_URL TEXT
        );
    """)

    # Create the Sale table
    cursor.execute("""
        CREATE TABLE Sale (
            SaleID INTEGER PRIMARY KEY AUTOINCREMENT,
            StockNo TEXT NOT NULL,
            SaleDate TEXT NOT NULL,      -- e.g. '2025-11-14' (ISO format)
            SalePrice REAL NOT NULL,
            BuyerName TEXT,
            Notes TEXT,
            FOREIGN KEY (StockNo) REFERENCES Store(StockNo)
        );
    """)

    # Commit and close
    conn.commit()
    conn.close()
    print(f"Database '{db_name}' created with tables 'Store' and 'Sale'.")

if __name__ == "__main__":
    create_database()
