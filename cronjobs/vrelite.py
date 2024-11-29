import json
import subprocess
import argparse
from datetime import datetime, timezone, timedelta


def remove_user(bucket, mc_usr, mc_pwd, minio_host):
    # create mc alias
    subprocess.run(['mc', 'alias', 'set', 'myminio', minio_host, mc_usr, mc_pwd])
    # detach policy from user
    subprocess.run(['mc', 'admin', 'policy', 'detach', 'myminio', f'{bucket}-policy', '--user', bucket])
    # remove policy
    subprocess.run(['mc', 'admin', 'policy', 'remove', 'myminio', f'{bucket}-policy'])
    # remove user
    subprocess.run(['mc', 'admin', 'user', 'rm', 'myminio', bucket])


def main(json_file_path, time_difference, mc_usr, mc_pwd, minio_host):
    # Read the JSON file
    with open(json_file_path, 'r') as file:
        data = json.load(file)

    # Get the current time
    current_time = datetime.now(timezone.utc)
    print(current_time)

    # Process each item in the array
    for item in data:
        # Skip if the item is already processed or if it is a small bucket
        if item['type'] == 'small' or item['processed']:
            continue

        # Parse the timestamp
        timestamp = datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00'))
        # Get the bucket name
        bucket = item['bucket']

        time_difference_threshold = timedelta(days=time_difference)

        # Check the time difference
        if current_time - timestamp >= time_difference_threshold:
            remove_user(bucket, mc_usr, mc_pwd, minio_host)
            item['processed'] = True  # Add the processed flag

    # Write the updated data back to the JSON file
    with open(json_file_path, 'w') as file:
        json.dump(data, file, indent=2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process MDDB VRE lite log.')
    parser.add_argument('json_file_path', type=str, help='Path to the log JSON file')
    parser.add_argument('time_difference', type=int, help='Time difference in days')
    parser.add_argument('mc_usr', type=str, help='MinIO Admin User')
    parser.add_argument('mc_pwd', type=str, help='MinIO Admin Password')
    parser.add_argument('minio_host', type=str, help='MinIO Host')
    args = parser.parse_args()

    main(args.json_file_path, args.time_difference, args.mc_usr, args.mc_pwd, args.minio_host)
