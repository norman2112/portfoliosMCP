"""Module for migrating data from one region to another."""
import json
import os
import sys
import traceback
import uuid
from http import HTTPStatus

import boto3
import sqlalchemy
from sqlalchemy import orm

from okrs_api.api.controller.helpers import extract_hasura_payload
from okrs_api.database import triggers_disabled_session
from okrs_api.data_utils.eradicator import Eradicator
from okrs_api.data_utils.manifests.bucket_utils import ManifestConductor
from okrs_api.data_utils.manifests.manifest_converter import manifest_converter
from okrs_api.data_utils.exporter import OrgExporter
from okrs_api.data_utils.importer import DataImporter


# pylint:disable=unused-argument


def submit_to_batch(params):
    """Submit a job to the job queue."""
    batch_client = boto3.client("batch")
    job_name = f"job_okrs_batch_{str(uuid.uuid4())}"
    job_queue = os.environ.get("JOB_QUEUE", "okrs-batch-job-queue")
    job_defn = os.environ.get("JOB_DEFINITION", "okrs-batch-job-definition")
    print(f"JOBQUEUE {job_queue} | JOB DEFINITION {job_defn}")

    submit_job = batch_client.submit_job(
        jobName=job_name,
        jobQueue=job_queue,
        jobDefinition=job_defn,
        containerOverrides={"command": params},
    )

    job_id = submit_job["jobId"]
    print(f"Submitted {job_id}")
    return dict(job_id=job_id, message="Job submitted")


async def export_from_json_input(app, input_json):
    """
    Given a JSON string input, adapt manifest and generate output file.

    A valid payload string looks like this (without new line):
    {"manifest_filename": "10146315773-10126896852-manifest.csv",
    "product_type": "leankit",
    "tenant_id_str": "LEANKIT~d09-10146315773"}
    """

    db = None
    try:
        payload = json.loads(input_json)
        db_settings = app["settings"].database
        # Configure the database engine and session.
        db_settings_dict = db_settings.engine.dict()
        db_url = db_settings_dict.pop("name_or_url")
        db = sqlalchemy.create_engine(db_url, **db_settings_dict)
        db_session_obj = orm.scoped_session(orm.sessionmaker(bind=db))
        with db_session_obj() as db_session:
            try:
                return await adapt_product_manifest_with_payload(db_session, payload)
            except BaseException as export_error:
                print("Export failed: " + str(export_error), file=sys.stderr)
                print(traceback.format_exc())
    except BaseException as ex:
        print(traceback.format_exc())
        print("Aborting due to configuration error " + str(ex), file=sys.stderr)
        return
    finally:
        if db:
            db.dispose()
        print("--------")


async def import_from_json_input(app, input_json):
    """
    Given a JSON string input, adapt manifest and generate output file.

    A valid payload string looks like this (without new line):
    {"product_type": "leankit",
    "original_tenant_id_str": "LEANKIT~d09-10146315773",
    "new_tenant_id_str": "LEANKIT~i01-10146315883"}
    """

    db = None
    try:
        payload = json.loads(input_json)
        db_settings = app["settings"].database
        # Configure the database engine and session.
        db_settings_dict = db_settings.engine.dict()
        db_url = db_settings_dict.pop("name_or_url")
        db = sqlalchemy.create_engine(db_url, **db_settings_dict)
        db_session_obj = orm.scoped_session(orm.sessionmaker(bind=db))
        try:
            return await import_adapted_manifest_with_payload(db_session_obj, payload)
        except BaseException as export_error:
            print("Import failed: " + str(export_error), file=sys.stderr)
            print(traceback.format_exc())
    except BaseException as ex:
        print(traceback.format_exc())
        print("Aborting due to configuration error " + str(ex), file=sys.stderr)
        return
    finally:
        if db:
            db.dispose()
        print("--------")


async def delete_from_json_input(app, input_json):
    """
    Given a JSON string input, delete an account.

    A valid payload string looks like this (without new line):
    {"tenant_id_str": "LEANKIT~d09-10146315773"}
    """
    db = None
    try:
        payload = json.loads(input_json)
        db_settings = app["settings"].database
        # Configure the database engine and session.
        db_settings_dict = db_settings.engine.dict()
        db_url = db_settings_dict.pop("name_or_url")
        db = sqlalchemy.create_engine(db_url, **db_settings_dict)
        db_session_obj = orm.scoped_session(orm.sessionmaker(bind=db))
        with db_session_obj() as db_session:
            try:
                return await delete_organization_with_payload(db_session, payload)
            except BaseException as export_error:
                print("Delete failed: " + str(export_error), file=sys.stderr)
                print(traceback.format_exc())
    except BaseException as ex:
        print(traceback.format_exc())
        print("Aborting due to error " + str(ex), file=sys.stderr)
        return
    finally:
        if db:
            db.dispose()
    print("--------")


async def migrate_from_json_input(app, payload):
    """
    Given a JSON string input, import or export account.

    A valid payload string looks like this (without new line):
    {"migration_type": "export" | "import", ...}
    """

    try:
        if "migration_type" in payload:
            if payload["migration_type"] == "export":
                await export_from_json_input(app, json.dumps(payload))
            elif payload["migration_type"] == "import":
                await import_from_json_input(app, json.dumps(payload))
            elif payload["migration_type"] == "delete":
                await delete_from_json_input(app, json.dumps(payload))
    except BaseException as ex:
        print(traceback.format_exc())
        print("Aborting due to configuration error " + str(ex), file=sys.stderr)


async def adapt_product_manifest_with_payload(db_session, payload):
    """
    Convert and export a manifest from a Planview Product.

    When a customer wishes to move to another region, they first must be
    moved/migrated by the Planview app. A manifest file must be generated and
    used by this app in order to create a new, _adapted manifest_.

    The payload is a dict with the following keys:

    :param string manifest_filename: the filename of the incoming manifest
    :param enum product_type: the planview product
    :param string tenant_id_str: the tenant_id_str of the tenant to move

    Reminder: the `tenant_id_str` is in the format of
    `{PRODUCT_TYPE}~{env}-{app-level product id}`
    """
    product_type = payload["product_type"]
    tenant_id_str = payload["tenant_id_str"]
    print("Attempting to download manifest file from S3")
    conductor = ManifestConductor(product_type, tenant_id_str)
    filename = conductor.download_product_manifest(payload["manifest_filename"])
    print("File downloaded, now reading to create ID map")
    with open(filename, "r") as f:
        manifest_ids = manifest_converter(f, product_type)
    print("ID map created, invoking Org exporter")
    org_exporter = OrgExporter(
        db_session=db_session,
        tenant_id_str=tenant_id_str,
        manifest_ids=manifest_ids,
    )
    adapted_manifest = org_exporter.export()
    db_session.close()
    if "SUMMARY" in adapted_manifest:
        print(json.dumps(adapted_manifest["SUMMARY"]))

    try:
        conductor.upload_adapted_manifest(adapted_manifest)
    except BaseException as e:
        print(e)
    return adapted_manifest


async def adapt_product_manifest(request, body, use_batch=True):
    """
    Convert and export a manifest from a Planview Product.

    When a customer wishes to move to another region, they first must be
    moved/migrated by the Planview app. A manifest file must be generated and
    used by this app in order to create a new, _adapted manifest_.

    The body must contain a JSON 'payload'  with the following keys:

    :param enum request: the request
    :param string body: payload
    :param boolean use_batch: Use the new batch to do migration.

    Reminder: the `tenant_id_str` is in the format of
    `{PRODUCT_TYPE}~{env}-{app-level product id}`
    """
    if not use_batch:
        payload = extract_hasura_payload(body)
        adapted_manifest = await adapt_product_manifest_with_payload(
            request.app["db_session"](), payload
        )
        return adapted_manifest, HTTPStatus.OK

    payload = extract_hasura_payload(body)
    params = [
        "export",
        payload["manifest_filename"],
        payload["product_type"],
        payload["tenant_id_str"],
    ]

    return submit_to_batch(params), HTTPStatus.OK


async def import_adapted_manifest_with_payload(session, payload):
    """
    Import the adapted manifest for a Planview Product.

    The adapted manifest is a JSON file that has been adapted from a
    Planview product manifest and re-tooled to allow direct import into
    the database that this api call is run on.

    The body must contain a JSON 'payload'  with the following keys:

    :param object session: the DB session
    :param dict payload: the payload
    """
    # Find the existing DB engine from the current session.
    engine = session.bind.engine

    # Make a new db connection and new session.
    # Set the db connection to ignore triggers.
    with triggers_disabled_session(engine) as db_session:
        product_type = payload["product_type"]
        original_tenant_id_str = payload["original_tenant_id_str"]
        new_tenant_id_str = payload["new_tenant_id_str"]
        new_tenant_group_id_str = payload.get("new_tenant_group_id_str", None)
        # Download the adapted manifest. If this errors out, we don't
        # make any changes.
        print("Attempting to download manifest file from S3")
        conductor = ManifestConductor(product_type, original_tenant_id_str)
        local_filename = conductor.download_adapted_manifest()
        print("Downloaded manifest file, proceeding to import")
        # Delete any previous records with the new_tenant_id_str
        print("Delete existing tenant")
        Eradicator.delete_tenant(db_session, new_tenant_id_str)
        print("Delete done")

        # Open the locally-saved adapted manifest and import
        with open(local_filename, "r") as f:
            print("Starting to import")
            importer = DataImporter(
                db_session=db_session,
                adapted_manifest_file=f,
                new_tenant_id_str=new_tenant_id_str,
                new_tenant_group_id_str=new_tenant_group_id_str,
            )
            import_log = importer.apply_adapted_manifest()
            print("Import completed")

            results = dict(export_summary=importer.export_summary)
            if "SUMMARY" in import_log:
                results["import_summary"] = import_log["SUMMARY"]

            print(json.dumps(results))


async def import_adapted_manifest(request, body, use_batch=True):
    """
    Import the adapted manifest for a Planview Product.

    The adapted manifest is a JSON file that has been adapted from a
    Planview product manifest and re-tooled to allow direct import into
    the database that this api call is run on.

    The body must contain a JSON 'payload'  with the following keys:

    :param enum product_type: the planview product
    :param string original_tenant_id_str: the original tenant_id_str of the tenant
    :param string new_tenant_id_str: the new tenant_id_str of the tenant
    """

    if not use_batch:
        # Find the existing DB engine from the current session.
        engine = request.app["db_session"].bind.engine

        # Make a new db connection and new session.
        # Set the db connection to ignore triggers.
        with triggers_disabled_session(engine) as db_session:
            payload = extract_hasura_payload(body)
            product_type = payload["product_type"]
            original_tenant_id_str = payload["original_tenant_id_str"]
            new_tenant_id_str = payload["new_tenant_id_str"]
            new_tenant_group_id_str = payload.get("new_tenant_group_id_str", None)
            # Download the adapted manifest. If this errors out, we don't
            # make any changes.
            print("Attempting to download manifest file from S3")
            conductor = ManifestConductor(product_type, original_tenant_id_str)
            local_filename = conductor.download_adapted_manifest()
            print("Downloaded manifest file, proceeding to import")
            # Delete any previous records with the new_tenant_id_str
            print("Delete existing tenant")
            Eradicator.delete_tenant(db_session, new_tenant_id_str)
            print("Delete done")

            # Open the locally-saved adapted manifest and import
            with open(local_filename, "r") as f:
                print("Starting to import")
                importer = DataImporter(
                    db_session=db_session,
                    adapted_manifest_file=f,
                    new_tenant_id_str=new_tenant_id_str,
                    new_tenant_group_id_str=new_tenant_group_id_str,
                )
                import_log = importer.apply_adapted_manifest()
                print("Import completed")

        return import_log, HTTPStatus.OK

    payload = extract_hasura_payload(body)
    params = [
        "import",
        payload["product_type"],
        payload["original_tenant_id_str"],
        payload["new_tenant_id_str"],
    ]

    return submit_to_batch(params), HTTPStatus.OK


async def delete_organization_with_payload(db_session, payload):
    """
    Delete an organization, permanently.

    This looks for a `tenant_id_str` in the payload and deletes all records
    for that organization. This would be used to delete an organization once it
    has been successfully moved to the destination environment/region.
    """
    tenant_id_str = payload["tenant_id_str"]
    Eradicator.delete_tenant(db_session, tenant_id_str)


async def delete_organization(request, body, use_batch=True):
    """
    Delete an organization, permanently.

    This looks for a `tenant_id_str` in the payload and deletes all records
    for that organization. This would be used to delete an organization once it
    has been successfully moved to the destination environment/region.
    """
    if not use_batch:
        payload = extract_hasura_payload(body)
        tenant_id_str = payload["tenant_id_str"]
        with request.app["db_session"]() as db_session:
            # Delete any records with the tenant_id_str provided
            Eradicator.delete_tenant(db_session, tenant_id_str)

        return None, HTTPStatus.OK

    payload = extract_hasura_payload(body)
    params = ["delete", payload["tenant_id_str"]]

    return submit_to_batch(params), HTTPStatus.OK
