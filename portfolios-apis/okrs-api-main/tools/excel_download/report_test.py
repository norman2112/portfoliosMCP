"""A simple (!) utility to take some data, upload to s3, create a link to it and send email."""

import sys
import uuid
import boto3
from botocore.exceptions import ClientError

BUCKET = "platforma-okrs-development"
DIRECTORY = "okr_reports_test"
TO_EMAIL = "arao@planview.com"
# TO_EMAIL = "sdatta@planview.com"
FROM_EMAIL = "sdatta@planview.com"
EXPIRES_IN_SECONDS = 60 * 5


def generate_data(args):
    """Create a data file with the args to this program."""

    def get_file_name():
        return f"/tmp/test_file_{str(uuid.uuid4())}.txt"

    def upload_file_name(file_name):
        return f"{DIRECTORY}/upload_{str(uuid.uuid4())}.txt"

    def save_to_file(file_name, data):
        with open(file_name, "w") as f:
            f.write(data)

    temp_file_name = get_file_name()
    save_to_file(temp_file_name, "\n".join(args) + "\n")
    upload_file = upload_file_name(temp_file_name)
    return temp_file_name, upload_file


def s3_upload(s3, file_name, upload_file_name):
    """Upload the file to s3."""

    return s3.upload_file(file_name, BUCKET, upload_file_name)


def generate_link(s3, remote_file):
    """Generate a pre-signed URL to the file."""
    method_parameters = {"Bucket": BUCKET, "Key": remote_file}

    try:
        url = s3.generate_presigned_url(
            ClientMethod="get_object",
            Params=method_parameters,
            ExpiresIn=EXPIRES_IN_SECONDS,
        )
        print("Got presigned URL: ", url)
    except ClientError as e:
        print("Couldn't get a presigned URL, error", e["Error"]["Message"])
        raise e
    return url


def send_email(link):
    """Send the email with link to a recipient."""
    client = boto3.client("ses", region_name="us-west-2")
    message = """
    <html>
        <body>
            <h1>You have got a mail</h2>
            <p>File download link <b><a href="{}">HERE</a></b></p>
        </body>
    </html>
    """
    message_text = "Your download link is \r\n" + str(link)
    try:
        response = client.send_email(
            Destination={"ToAddresses": [TO_EMAIL]},
            Message={
                "Body": {
                    "Html": {"Charset": "UTF-8", "Data": message.format(link)},
                    "Text": {"Charset": "UTF-8", "Data": message_text},
                },
                "Subject": {
                    "Charset": "UTF-8",
                    "Data": "Your file is ready to download",
                },
            },
            Source=FROM_EMAIL,
        )
    except ClientError as e:
        print("Error sending email:", e["Error"]["Message"])
    else:
        print("Email sent, ID", response["MessageId"])


if __name__ == "__main__":
    s3_client = boto3.client("s3")
    local_file, remote_file = generate_data(sys.argv)
    print("FILES", local_file, remote_file)
    upload_res = s3_upload(s3_client, local_file, remote_file)
    print("UPLOADED")
    link = generate_link(s3_client, remote_file)
    send_email(link)
