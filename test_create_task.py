#!/usr/bin/env python3
"""Test script to verify SOAP API task creation works correctly.

This script directly tests the SOAP client to create a task,
bypassing the MCP tool layer to isolate any issues.
"""

import asyncio
import logging
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from planview_portfolios_mcp.soap_client import get_soap_client, make_soap_request

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Enable zeep transport logging to see actual XML
logging.getLogger('zeep.transports').setLevel(logging.DEBUG)
logging.getLogger('zeep.wsdl').setLevel(logging.INFO)  # Reduce WSDL noise
logging.getLogger('zeep.xsd').setLevel(logging.INFO)  # Reduce XSD noise

logger = logging.getLogger(__name__)

# Service constants
TASK_SERVICE_NAME = "TaskService"
TASK_SERVICE_PORT = "BasicHttpBinding_ITaskService3"


async def test_create_task():
    """Test creating a task via SOAP API."""
    logger.info("Starting SOAP task creation test...")

    # Use the "Website Redesign" project we've been testing with
    # Structure code 17313 - we'll construct the key URI
    # Format: key://{structure_id}/$Plan/{structure_code}
    # Based on the project creation, this should be key://2/$Plan/17313
    father_key = "key://2/$Plan/17313"
    logger.info(f"Using FatherKey: {father_key}")

    # Create minimal task data matching the SOAP examples
    task_data = {
        "Description": "Test Task from Direct SOAP Call",
        "FatherKey": father_key,
        "Key": f"ekey://2/test-namespace/test-task-{int(time.time())}",
    }

    logger.info(f"Task data: {task_data}")

    try:
        async with get_soap_client() as client:
            logger.info("SOAP client created successfully")

            # Get the service
            try:
                service = client.bind(TASK_SERVICE_NAME, port_name=TASK_SERVICE_PORT)
                logger.info(f"Bound to service: {TASK_SERVICE_NAME} port: {TASK_SERVICE_PORT}")
            except Exception as e:
                logger.warning(f"Binding failed: {e}, trying client.service")
                service = client.service

            # Get the Create operation
            create_op = getattr(service, "Create")
            logger.info(f"Got Create operation: {create_op}")

            # Check operation signature
            if hasattr(create_op, "_signature"):
                logger.info(f"Create operation signature: {create_op._signature}")

            # Inspect the Create operation signature to understand what it expects
            logger.info("Inspecting Create operation...")
            if hasattr(create_op, "_signature"):
                sig = create_op._signature
                logger.info(f"Create signature: {sig}")
                if hasattr(sig, "parameters"):
                    for param_name, param_type in sig.parameters.items():
                        logger.info(f"  Parameter: {param_name} -> {param_type}")
            
            # Get the ArrayOfTaskDto2 type to see if we need to use it
            try:
                array_type = client.get_type(
                    "{http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/TaskDto2/2012/08}ArrayOfTaskDto2"
                )
                logger.info(f"ArrayOfTaskDto2 type: {array_type}")
                logger.info(f"ArrayOfTaskDto2 signature: {array_type.signature() if hasattr(array_type, 'signature') else 'N/A'}")
            except Exception as e:
                logger.warning(f"Could not get ArrayOfTaskDto2: {e}")

            # Try to get TaskDto2 type factory
            task_dto_factory = None
            try:
                task_dto_factory = client.get_type(
                    "{http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/TaskDto2/2012/08}TaskDto2"
                )
                logger.info(f"Got TaskDto2 factory: {task_dto_factory}")
            except Exception as e:
                logger.warning(f"Could not get TaskDto2 factory: {e}")

            # Sort task data alphabetically (Planview requirement)
            # Only include non-None values to avoid zeep filtering them out
            task_dict = {k: v for k, v in sorted(task_data.items()) if v is not None}
            logger.info(f"Sorted task dict (non-None only): {task_dict}")

            # Get TaskDto2 type from the service's namespace
            logger.info("Getting TaskDto2 type from service...")
            task_dto_type = client.get_type(
                "{http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/TaskDto2/2012/08}TaskDto2"
            )
            logger.info(f"Got TaskDto2 type: {task_dto_type}")
            
            # Try creating TaskDto2 using constructor with kwargs (this is the standard zeep way)
            logger.info("Creating TaskDto2 object using constructor...")
            task_dto_obj = task_dto_type(**task_dict)
            
            logger.info(f"Created TaskDto2: {type(task_dto_obj)}")
            logger.info(f"Description: {getattr(task_dto_obj, 'Description', 'NOT SET')}")
            logger.info(f"FatherKey: {getattr(task_dto_obj, 'FatherKey', 'NOT SET')}")
            logger.info(f"Key: {getattr(task_dto_obj, 'Key', 'NOT SET')}")
            
            # Try using ArrayOfTaskDto2 explicitly
            try:
                array_type = client.get_type(
                    "{http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/TaskDto2/2012/08}ArrayOfTaskDto2"
                )
                logger.info("Creating ArrayOfTaskDto2 with TaskDto2 object...")
                # ArrayOfTaskDto2 should accept a list/sequence of TaskDto2
                dtos_param = array_type([task_dto_obj])
                logger.info(f"Created ArrayOfTaskDto2: {type(dtos_param)}")
            except Exception as e:
                logger.warning(f"ArrayOfTaskDto2 creation failed: {e}, using list instead")
                # Fall back to list
                dtos_param = [task_dto_obj]
            
            logger.info(f"Calling Create with dtos parameter type: {type(dtos_param)}")
            logger.info(f"dtos_param value: {dtos_param}")

            # Try calling with dict first - zeep should auto-convert
            logger.info("Attempting call with dict (zeep auto-conversion)...")
            try:
                # Pass dict directly - zeep should convert based on operation signature
                result_direct = await asyncio.to_thread(create_op, dtos=[task_dict])
                logger.info("✅ Call with dict succeeded!")
                logger.info(f"Result type: {type(result_direct)}")
                
                # Process the OpenSuiteResult using our helper
                from planview_portfolios_mcp.soap_client import _handle_soap_result
                result = _handle_soap_result(result_direct)
                logger.info(f"Processed result: {result}")
            except Exception as e:
                logger.warning(f"Call with dict failed: {e}")
                logger.info("Trying with TaskDto2 object...")
                try:
                    # Try with TaskDto2 object
                    result_direct = await asyncio.to_thread(create_op, dtos=dtos_param)
                    logger.info("✅ Call with TaskDto2 object succeeded!")
                    logger.info(f"Result type: {type(result_direct)}")
                    
                    # Process the OpenSuiteResult using our helper
                    from planview_portfolios_mcp.soap_client import _handle_soap_result
                    result = _handle_soap_result(result_direct)
                    logger.info(f"Processed result: {result}")
                except Exception as e2:
                    logger.warning(f"Call with TaskDto2 object failed: {e2}, trying via make_soap_request...")
                    # Fall back to make_soap_request
                    result = await make_soap_request(
                        client,
                        TASK_SERVICE_NAME,
                        "Create",
                        port_name=TASK_SERVICE_PORT,
                        dtos=dtos_param,
                    )

            logger.info("✅ Task created successfully!")
            logger.info(f"Result: {result}")

            if result.get("data", {}).get("Key"):
                logger.info(f"Created task Key: {result['data']['Key']}")

    except Exception as e:
        logger.error(f"❌ Failed to create task: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(test_create_task())
