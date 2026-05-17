import argparse
import json

from helpers import logger


def post_results(args: argparse.Namespace, passed: bool, messages: list[str]):
    if args.output_format == "json":
        result = {
            "passed": passed,
            "project_id": args.project_id,
            "mr_iid": args.mr_iid,
            "messages": messages
        }
        # Print JSON document cleanly to stdout
        print(json.dumps(result, indent=2))
    else:
        # print text results via logger
        logger.info("")
        logger.info("--- Validation Summary ---")
        for msg in messages:
            if msg.startswith("[PASS]"):
                logger.info(msg)
            elif msg.startswith("[FAIL]"):
                logger.error(msg)
            else:
                logger.info(msg)
        logger.info("--------------------------")

        if passed:
            logger.info("Result: PASS. MR can be merged.")
        else:
            logger.error("Result: FAIL. MR does not meet requirements.")
