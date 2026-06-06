"""CLI entrypoint."""
from __future__ import annotations

import argparse
import json
import sys

from openswarm_builder.service import BuilderService


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="openswarm-builder", description="OpenSwarm Agent Builder")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("serve", help="Start HTTP API on :8090")
    sub.add_parser("health", help="Health check")

    p_design = sub.add_parser("design", help="Run design loop")
    p_design.add_argument("request", help="Swarm description")

    p_approve = sub.add_parser("approve", help="Approve a spec")
    p_approve.add_argument("spec_id")

    p_build = sub.add_parser("build", help="Materialize approved spec")
    p_build.add_argument("spec_id")
    p_build.add_argument("--start", action="store_true")

    p_list = sub.add_parser("list", help="List swarms")
    p_provision = sub.add_parser("provision-default", help="Provision vendor default swarm")

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "serve":
        from openswarm_builder.adapters.http_server import main as serve_main

        serve_main()
        return

    service = BuilderService()

    if args.command == "health":
        print(json.dumps(service.health(), indent=2))
    elif args.command == "design":
        print(json.dumps(service.design(args.request), indent=2))
    elif args.command == "approve":
        print(json.dumps(service.approve(args.spec_id), indent=2))
    elif args.command == "build":
        print(json.dumps(service.build(args.spec_id, start=args.start), indent=2))
    elif args.command == "list":
        print(json.dumps(service.list_swarms(), indent=2))
    elif args.command == "provision-default":
        print(json.dumps(service.provision_default(), indent=2))


if __name__ == "__main__":
    main()
