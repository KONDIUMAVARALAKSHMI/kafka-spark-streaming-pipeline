import os
import urllib.request
import sys
import ssl

# Disable SSL verification to handle certificate errors
ssl._create_default_https_context = ssl._create_unverified_context

def download_file(url, filepath):
    if os.path.exists(filepath):
        print(f"File {filepath} already exists. Skipping download.")
        return

    try:
        print(f"Downloading {url} to {filepath}...")
        def progress(count, block_size, total_size):
            if total_size > 0:
                percent = int(count * block_size * 100 / total_size)
                sys.stdout.write(f"\rDownloading: {percent}%")
            else:
                sys.stdout.write(f"\rDownloading: {count * block_size} bytes")
            sys.stdout.flush()

        urllib.request.urlretrieve(url, filepath, progress)
        print("\nDownload complete!")
    except Exception as e:
        print(f"\nError downloading file: {e}")
        sys.exit(1)

def main():
    # Setup paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    output_dir = os.path.join(project_root, 'spark')
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 1. Download Spark
    spark_url = "https://archive.apache.org/dist/spark/spark-3.3.2/spark-3.3.2-bin-hadoop3.tgz"
    spark_filename = "spark-3.3.2-bin-hadoop3.tgz"
    spark_filepath = os.path.join(output_dir, spark_filename)
    download_file(spark_url, spark_filepath)

    # 2. Download Postgres JDBC Driver
    pg_url = "https://jdbc.postgresql.org/download/postgresql-42.5.1.jar"
    pg_filename = "postgresql-42.5.1.jar"
    pg_filepath = os.path.join(output_dir, pg_filename)
    download_file(pg_url, pg_filepath)

if __name__ == "__main__":
    main()
