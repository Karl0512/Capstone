import os
import psycopg2
from dotenv import load_dotenv
import getpass

# load env file
load_dotenv()

def update_env_file(creds, env_path=".env"):
    """Update only DB-related keys in .env without removing other entries."""
    keys_to_update = {
        "DB_HOST": creds["host"],
        "DB_PORT": creds["port"],
        "DB_NAME": creds["database"],
        "DB_USER": creds["user"],
        "DB_PASSWORD": creds["password"],
    }

    # Read existing lines
    existing = {}
    lines = []
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    existing[k] = v

    # Merge updates
    existing.update(keys_to_update)

    # Rebuild lines in original order, add new ones at the end
    written_keys = set()
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if "=" in line:
                    k, _ = line.strip().split("=", 1)
                    if k in existing:
                        lines.append(f"{k}={existing[k]}")
                        written_keys.add(k)
                    else:
                        lines.append(line.strip())
                else:
                    lines.append(line.strip())

    # Append any new keys that weren’t originally in the file
    for k, v in existing.items():
        if k not in written_keys:
            lines.append(f"{k}={v}")

    # Write back
    with open(env_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"💾 Updated {env_path} with new DB settings (kept other values).")


def get_connection():
    # Try env first
    try:
        return psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT"),
        )
    except Exception as e:
        print("❌ Database connection failed:", e)

    # Console fallback
    while True:
        print("\n--- Database Connection Setup ---")
        host = input(f"Host [{os.getenv('DB_HOST', 'localhost')}]: ") or os.getenv("DB_HOST", "localhost")
        port = input(f"Port [{os.getenv('DB_PORT', '5432')}]: ") or os.getenv("DB_PORT", "5432")
        database = input(f"Database [{os.getenv('DB_NAME', 'postgres')}]: ") or os.getenv("DB_NAME", "postgres")
        user = input(f"User [{os.getenv('DB_USER', 'postgres')}]: ") or os.getenv("DB_USER", "postgres")
        password = input("Password: ")  # or use getpass.getpass() for hidden input

        creds = {
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "password": password,
        }

        try:
            conn = psycopg2.connect(**creds)
            print("✅ Database connected manually")
            update_env_file(creds)  # 🔥 save new settings into .env
            load_dotenv(override=True)
            return conn
        except Exception as e2:
            print("❌ Manual connection failed:", e2)
            retry = input("Try again? (y/n): ").strip().lower()
            if retry != "y":
                print("⚠️ User cancelled DB setup.")
                return None
