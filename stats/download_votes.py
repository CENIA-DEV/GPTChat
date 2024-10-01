import time
from google.cloud.storage import Client, transfer_manager

def download_bucket_with_transfer_manager(
    bucket_name, destination_directory="", workers=8, max_results=1000
):
    """Download all of the blobs in a bucket, concurrently in a process pool.

    The filename of each blob once downloaded is derived from the blob name and
    the `destination_directory `parameter. For complete control of the filename
    of each blob, use transfer_manager.download_many() instead.

    Directories will be created automatically as needed, for instance to
    accommodate blob names that include slashes.
    """
    storage_client = Client()
    bucket = storage_client.bucket(bucket_name)

    blob_names = [
        blob.name
        for blob in bucket.list_blobs(prefix="data_chat", max_results=max_results)
    ]

    transfer_manager.download_many_to_path(
        bucket,
        blob_names,
        destination_directory=destination_directory,
        max_workers=workers,
    )


def main():
    while True:
        time.sleep(300)
        download_bucket_with_transfer_manager(
            bucket_name="gpt-las-chat",
            destination_directory="/home/sebastiandonoso/GPTChat/stats/data",
        )


if __name__ == "__main__":
    main()
