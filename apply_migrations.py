import psycopg2
import os

DB_URL = "postgresql://postgres:Arunachotu@1718@aws-0-us-west-1.pooler.supabase.com:5432/postgres"

def run_migrations():
    try:
        # Connect to your postgres DB
        conn = psycopg2.connect(DB_URL)
        conn.autocommit = True
        cur = conn.cursor()

        # Read migration files
        migrations_dir = 'supabase/migrations'
        migration_files = sorted([f for f in os.listdir(migrations_dir) if f.endswith('.sql')])
        
        for file in migration_files:
            file_path = os.path.join(migrations_dir, file)
            print(f"Applying migration: {file}")
            with open(file_path, 'r', encoding='utf-8') as f:
                sql = f.read()
                try:
                    cur.execute(sql)
                    print(f"Successfully applied {file}")
                except Exception as e:
                    print(f"Error applying {file}: {e}")
                    # continue with next since it might already be applied

        cur.close()
        conn.close()
        print("All migrations processed.")

    except Exception as e:
        print(f"Failed to connect or execute migrations: {e}")

if __name__ == "__main__":
    run_migrations()
